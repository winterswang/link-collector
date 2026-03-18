"""
Link-Collector V2.0 - 核心服务

提供开放的 API 接口，供外部项目调用
"""

import os
import re
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

from .models import (
    ArticleMeta, ArticleContent, Source, SourceType,
    Classification, Category, SubCategory,
    ImportanceInfo, Importance,
    Timestamps, Relations,
    create_article
)
from .classifier import Classifier
from .indexer import IndexManager


class CollectorService:
    """
    Link-Collector 核心服务
    
    提供内容采集、分类、存储的统一接口
    """
    
    def __init__(self, 
                 data_dir: str = None,
                 api_key: str = None):
        """
        初始化服务
        
        Args:
            data_dir: 数据存储目录，默认为 link-collector/data
            api_key: 百炼 API Key
        """
        # 数据目录
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data"
        
        self.inbox_dir = self.data_dir / "inbox"
        self.library_dir = self.data_dir / "library"
        self.index_dir = self.data_dir / "index"
        
        # 创建目录
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # API Key
        self.api_key = api_key or os.environ.get('BAILIAN_API_KEY', '')
        
        # 组件
        self.classifier = Classifier(self.api_key)
        self.indexer = IndexManager(self.index_dir)
        
        # OpenAI client
        self.client = None
        if self.api_key and OpenAI:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
    
    # ============ 核心 API ============
    
    def process_url(self, url: str, options: dict = None) -> dict:
        """
        处理链接
        
        Args:
            url: 链接地址
            options: 选项
                - category: 指定分类
                - tags: 预设标签
                - importance: 预设重要性
                - save_to: 额外保存路径
                - raw_copy: 是否保留原始文件副本
        
        Returns:
            {"success": True, "id": "...", "paths": {...}, "metadata": {...}}
        """
        options = options or {}
        
        try:
            # 1. 爬取内容
            content_data = self._fetch_url(url)
            
            if not content_data:
                return {"success": False, "error": "无法获取内容"}
            
            # 2. 分类
            classification = self._classify_content(
                content_data.get("title", ""),
                content_data.get("content", ""),
                url,
                options
            )
            
            # 3. 评估重要性
            importance = self._evaluate_importance(
                content_data.get("title", ""),
                content_data.get("content", ""),
                classification
            )
            
            # 4. 生成元数据
            article_id = str(uuid.uuid4())
            today = datetime.now().strftime("%Y-%m-%d")
            
            meta = ArticleMeta(
                id=article_id,
                title=content_data.get("title", "无标题"),
                source=Source(
                    type=SourceType.WEB,
                    url=url,
                    platform=self._detect_platform(url),
                    author=content_data.get("author")
                ),
                classification=classification,
                importance=importance,
                content=ArticleContent(
                    summary=content_data.get("summary"),
                    key_points=content_data.get("key_points", []),
                    word_count=len(content_data.get("content", "")),
                    raw_content=content_data.get("content")
                ),
                timestamps=Timestamps(
                    created=datetime.now(),
                    published=content_data.get("publish_time")
                )
            )
            
            # 5. 存储
            paths = self._save_article(meta, options)
            
            # 6. 更新索引
            self.indexer.add_article(meta.to_dict(), paths.get("primary", ""))
            
            return {
                "success": True,
                "id": article_id,
                "paths": paths,
                "metadata": meta.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_file(self, file_path: str, options: dict = None) -> dict:
        """
        处理本地文件
        
        Args:
            file_path: 文件路径
            options: 选项（同 process_url）
        
        Returns:
            处理结果
        """
        options = options or {}
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"success": False, "error": "文件不存在"}
        
        try:
            # 1. 提取内容
            content_data = self._extract_file_content(file_path)
            
            # 2. 分类
            classification = self._classify_content(
                content_data.get("title", file_path.stem),
                content_data.get("content", ""),
                str(file_path),
                options
            )
            
            # 3. 评估重要性
            importance = self._evaluate_importance(
                content_data.get("title", file_path.stem),
                content_data.get("content", ""),
                classification
            )
            
            # 4. 生成元数据
            article_id = str(uuid.uuid4())
            
            # 确定文件类型
            suffix = file_path.suffix.lower()
            source_type = {
                '.pdf': SourceType.PDF,
                '.xlsx': SourceType.EXCEL,
                '.xls': SourceType.EXCEL,
                '.md': SourceType.MARKDOWN,
                '.txt': SourceType.MARKDOWN,
                '.png': SourceType.IMAGE,
                '.jpg': SourceType.IMAGE,
                '.jpeg': SourceType.IMAGE,
            }.get(suffix, SourceType.WEB)
            
            meta = ArticleMeta(
                id=article_id,
                title=content_data.get("title", file_path.stem),
                source=Source(
                    type=source_type,
                    url=str(file_path),
                    platform="local",
                    author=options.get("author"),  # 支持预设作者
                ),
                classification=classification,
                importance=importance,
                content=ArticleContent(
                    summary=content_data.get("summary"),
                    key_points=content_data.get("key_points", []),
                    word_count=len(content_data.get("content", "")),
                    raw_content=content_data.get("content")
                ),
                timestamps=Timestamps(created=datetime.now())
            )
            
            # 5. 存储
            paths = self._save_article(meta, options)
            
            # 6. 更新索引
            self.indexer.add_article(meta.to_dict(), paths.get("primary", ""))
            
            return {
                "success": True,
                "id": article_id,
                "paths": paths,
                "metadata": meta.to_dict()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_batch(self, urls: List[str], options: dict = None) -> List[dict]:
        """
        批量处理
        
        Args:
            urls: URL 列表
            options: 选项
        
        Returns:
            处理结果列表
        """
        results = []
        for url in urls:
            result = self.process_url(url, options)
            results.append(result)
        return results
    
    def fetch_only(self, url: str) -> dict:
        """
        仅爬取内容，不存储
        
        Args:
            url: 链接地址
        
        Returns:
            {"title": "...", "content": "...", "metadata": {...}}
        """
        return self._fetch_url(url)
    
    def classify_only(self, title: str, content: str, url: str = None) -> dict:
        """
        仅分类，不存储
        
        Args:
            title: 标题
            content: 内容
            url: 来源链接
        
        Returns:
            {"category": "...", "sub_category": "...", "tags": [...], "importance": "..."}
        """
        classification = self.classifier.classify(title, content, url)
        importance = self.classifier.calculate_importance(title, content, classification)
        
        return {
            "category": classification.category.value,
            "sub_category": classification.sub_category.value if classification.sub_category else None,
            "tags": classification.tags,
            "related_stocks": classification.related_stocks,
            "importance": importance.level.value,
            "score": importance.score
        }
    
    # ============ 内部方法 ============
    
    def _fetch_url(self, url: str) -> Optional[dict]:
        """爬取网页内容"""
        
        # 特殊处理雪球
        if "xueqiu.com" in url:
            return self._fetch_xueqiu(url)
        
        # 通用爬取
        return self._fetch_generic(url)
    
    def _fetch_xueqiu(self, url: str) -> Optional[dict]:
        """爬取雪球文章"""
        
        if not sync_playwright:
            return self._fetch_with_llm(url)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(url, timeout=30000)
                page.wait_for_load_state('networkidle')
                
                # 提取标题
                title = page.title()
                if '雪球' in title:
                    title = title.split('雪球')[0].strip().rstrip('-').strip()
                
                # 提取作者
                author = ""
                author_elem = page.query_selector('.article__bd__from a, .user-name')
                if author_elem:
                    author = author_elem.inner_text().strip()
                
                # 提取内容
                content = ""
                content_elem = page.query_selector('.article__bd__detail, article')
                if content_elem:
                    content = content_elem.inner_text().strip()
                
                browser.close()
                
                return {
                    "title": title,
                    "content": content,
                    "author": author,
                    "url": url
                }
                
        except Exception as e:
            print(f"Playwright 爬取失败: {e}")
            return self._fetch_with_llm(url)
    
    def _fetch_generic(self, url: str) -> Optional[dict]:
        """通用网页爬取"""
        
        if sync_playwright:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state('networkidle')
                    
                    title = page.title()
                    content = page.content()
                    
                    browser.close()
                    
                    return {
                        "title": title,
                        "content": content[:10000],  # 限制长度
                        "url": url
                    }
            except Exception as e:
                print(f"爬取失败: {e}")
        
        return self._fetch_with_llm(url)
    
    def _fetch_with_llm(self, url: str) -> Optional[dict]:
        """使用 LLM 联网获取内容"""
        
        if not self.client:
            return None
        
        try:
            completion = self.client.chat.completions.create(
                model="glm-5",
                messages=[{
                    "role": "user", 
                    "content": f"请访问以下链接，提取文章的标题和正文内容：\n\n{url}"
                }],
            )
            
            response = completion.choices[0].message.content
            
            return {
                "title": url.split("/")[-1],
                "content": response,
                "url": url
            }
            
        except Exception as e:
            print(f"LLM 获取失败: {e}")
            return None
    
    def _extract_file_content(self, file_path: Path) -> dict:
        """提取文件内容"""
        
        suffix = file_path.suffix.lower()
        content = ""
        
        if suffix == '.pdf':
            content = self._extract_pdf(file_path)
        elif suffix in ['.xlsx', '.xls']:
            content = self._extract_excel(file_path)
        elif suffix in ['.md', '.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = f"[{suffix} 文件，内容待提取]"
        
        return {
            "title": file_path.stem,
            "content": content
        }
    
    def _extract_pdf(self, file_path: Path) -> str:
        """提取 PDF 内容"""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages[:10]:  # 最多 10 页
                    text += page.extract_text() or ""
                return text[:10000]
        except ImportError:
            return "[PDF 内容：请安装 pdfplumber]"
    
    def _extract_excel(self, file_path: Path) -> str:
        """提取 Excel 内容"""
        try:
            import pandas as pd
            xlsx = pd.ExcelFile(file_path)
            text = f"工作表: {', '.join(xlsx.sheet_names)}\n\n"
            for sheet in xlsx.sheet_names[:3]:  # 最多 3 个工作表
                df = pd.read_excel(xlsx, sheet_name=sheet)
                text += f"### {sheet}\n{df.head(20).to_string()}\n\n"
            return text[:10000]
        except ImportError:
            return "[Excel 内容：请安装 pandas]"
    
    def _classify_content(self, title: str, content: str, url: str, options: dict) -> Classification:
        """分类内容"""
        
        # 如果用户指定了分类，使用用户的
        if options.get("category"):
            return Classification(
                category=Category(options["category"]),
                sub_category=SubCategory(options["sub_category"]) if options.get("sub_category") else None,
                tags=options.get("tags", []),
                related_stocks=options.get("related_stocks", [])
            )
        
        # 智能分类
        classification = self.classifier.classify(title, content, url)
        
        # 合并用户预设的标签
        if options.get("tags"):
            for tag in options["tags"]:
                if tag not in classification.tags:
                    classification.tags.append(tag)
        
        if options.get("related_stocks"):
            for stock in options["related_stocks"]:
                if stock not in classification.related_stocks:
                    classification.related_stocks.append(stock)
        
        return classification
    
    def _evaluate_importance(self, title: str, content: str, classification: Classification) -> ImportanceInfo:
        """评估重要性"""
        
        importance_info = self.classifier.calculate_importance(title, content, classification)
        
        return importance_info
    
    def _detect_platform(self, url: str) -> str:
        """检测平台"""
        if "xueqiu.com" in url:
            return "xueqiu"
        elif "feishu.cn" in url:
            return "feishu"
        elif "mp.weixin.qq.com" in url:
            return "wechat"
        elif "github.com" in url:
            return "github"
        else:
            return "web"
    
    def _save_article(self, meta: ArticleMeta, options: dict) -> dict:
        """保存文章"""
        
        paths = {}
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 保存到 inbox（主存储）
        inbox_dir = self.inbox_dir / today
        inbox_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件名
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', meta.title)[:50]
        filename = f"{datetime.now().strftime('%H%M%S')}_{safe_title}.md"
        
        inbox_path = inbox_dir / filename
        self._write_article_file(inbox_path, meta)
        paths["primary"] = str(inbox_path)
        
        # 2. 保存元数据 JSON
        meta_path = inbox_dir / f"{meta.id}.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            f.write(meta.to_json())
        paths["meta"] = str(meta_path)
        
        # 3. 创建 library 符号链接（按分类）
        if not options.get("no_library"):
            cat = meta.classification.category.value
            sub_cat = meta.classification.sub_category.value if meta.classification.sub_category else "_others"
            
            library_cat_dir = self.library_dir / cat / sub_cat
            library_cat_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果有股票，创建股票目录
            if meta.classification.related_stocks:
                for stock in meta.classification.related_stocks:
                    stock_dir = library_cat_dir / stock
                    stock_dir.mkdir(parents=True, exist_ok=True)
                    # 创建符号链接
                    link_path = stock_dir / filename
                    try:
                        link_path.symlink_to(inbox_path)
                    except Exception:
                        pass
            
            paths["library"] = str(library_cat_dir)
        
        # 4. 保存到指定目录（副本）
        save_to = options.get("save_to")
        if save_to:
            save_dir = Path(save_to)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            copy_path = save_dir / filename
            self._write_article_file(copy_path, meta)
            paths["copy"] = str(copy_path)
        
        return paths
    
    def _write_article_file(self, path: Path, meta: ArticleMeta):
        """写入文章文件"""
        
        lines = [
            f"# {meta.title}",
            "",
            "## 元数据",
            "",
            "| 属性 | 值 |",
            "|------|------|",
            f"| **ID** | {meta.id} |",
            f"| **来源** | {meta.source.url or '本地文件'} |",
            f"| **分类** | {meta.classification.category.value} |",
            f"| **子分类** | {meta.classification.sub_category.value if meta.classification.sub_category else '-'} |",
            f"| **重要性** | {meta.importance.level.value} ({meta.importance.score}分) |",
            f"| **标签** | {', '.join(meta.classification.tags) or '-'} |",
            f"| **相关股票** | {', '.join(meta.classification.related_stocks) or '-'} |",
            f"| **采集时间** | {meta.timestamps.created.strftime('%Y-%m-%d %H:%M')} |",
            "",
            "## 摘要",
            "",
            meta.content.summary or "（无摘要）",
            "",
            "## 要点",
            ""
        ]
        
        for point in meta.content.key_points:
            lines.append(f"- {point}")
        
        if meta.content.raw_content:
            lines.extend([
                "",
                "## 内容预览",
                "",
                meta.content.raw_content[:2000] + ("..." if len(meta.content.raw_content) > 2000 else "")
            ])
        
        lines.extend([
            "",
            "---",
            f"*由 link-collector V2.0 自动采集*"
        ])
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))