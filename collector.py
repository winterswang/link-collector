#!/usr/bin/env python3
"""
链接内容记录与分类工具 MVP

功能：
1. 接收用户提交的链接
2. 使用 llms_tools (阿里百炼) 提取网页内容
3. 调用百炼 GLM-5 进行智能分类
4. 生成摘要和标签
5. 归档到 ideas-and-notes/inbox/
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 项目路径
PROJECT_ROOT = Path('/root/.openclaw/workspace/ideas-and-notes')
INBOX_DIR = PROJECT_ROOT / 'inbox'

# 分类标准
CATEGORIES = {
    'tech': '技术相关（编程、架构、工具）',
    'investment': '投资理财（股票、基金、经济）',
    'life': '生活日常（健康、旅行、美食）',
    'reading': '阅读笔记（书籍、文章、思考）',
    'tools': '工具资源（软件、服务、资源）'
}

# 智能分类 Prompt
CLASSIFICATION_PROMPT = """你是一个内容分类助手。请分析以下网页内容，并进行智能分类。

## 分类标准
{categories}

## 网页内容
标题: {title}
来源: {url}
内容摘要: {content}

## 输出要求
请以 JSON 格式输出：
{{
    "category": "分类（从分类标准中选择一个）",
    "importance": "必读/值得关注/参考",
    "tags": ["标签1", "标签2", "标签3"],
    "summary": "一句话摘要（不超过50字）",
    "key_points": ["要点1", "要点2", "要点3"]
}}

只输出 JSON，不要其他内容。"""


class LinkCollector:
    """链接内容收集器"""
    
    def __init__(self):
        # 使用百炼 GLM-5 配置
        self.config = self._load_config()
        self.base_url = self.config.get('baseUrl', 'https://coding.dashscope.aliyuncs.com/v1')
        self.api_key = self.config.get('apiKey', '')
        
    def _load_config(self) -> dict:
        """加载百炼配置"""
        config_path = Path('/root/.openclaw/openclaw.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get('models', {}).get('providers', {}).get('qwencode', {})
        return {}
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        提取网页内容（使用百炼联网搜索）
        
        Args:
            url: 网页链接
            
        Returns:
            包含标题、内容的字典
        """
        try:
            import httpx
            
            # 使用百炼 Chat API 配合 enable_search 抓取网页
            payload = {
                "model": "glm-5",
                "messages": [{
                    "role": "user", 
                    "content": f"请提取并总结这个网页的主要内容，包括标题和正文：{url}"
                }],
                "extra_body": {"enable_search": True}
            }
            
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-5",
                    "messages": [{
                        "role": "user", 
                        "content": f"请提取并总结这个网页的主要内容，包括标题和正文：{url}"
                    }],
                    "max_tokens": 2000
                },
                timeout=300
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # 尝试从内容中提取标题
                lines = content.split('\n')
                title = lines[0] if lines else '未知标题'
                
                return {
                    'title': title.replace('#', '').strip(),
                    'content': content,
                    'url': url
                }
            else:
                return {'error': f'请求失败: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'提取失败: {e}'}
    
    def classify_content(self, title: str, content: str, url: str) -> Dict[str, Any]:
        """
        智能分类内容（使用百炼 GLM-5）
        
        Args:
            title: 标题
            content: 内容
            url: 来源链接
            
        Returns:
            分类结果
        """
        import httpx
        
        categories_text = '\n'.join([f'- {k}: {v}' for k, v in CATEGORIES.items()])
        prompt = CLASSIFICATION_PROMPT.format(
            categories=categories_text,
            title=title,
            url=url,
            content=content[:3000]
        )
        
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-5",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.3
                },
                timeout=300
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data['choices'][0]['message']['content']
                
                # 解析 JSON
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    return json.loads(json_match.group())
            
            return {
                'category': 'reading',
                'importance': '值得关注',
                'tags': [],
                'summary': title,
                'key_points': []
            }
                
        except Exception as e:
            print(f"分类失败: {e}")
            return {
                'category': 'reading',
                'importance': '值得关注',
                'tags': [],
                'summary': title,
                'key_points': []
            }
    
    def save_to_inbox(self, url: str, title: str, content: str, 
                      classification: Dict[str, Any]) -> str:
        """
        保存到收件箱
        
        Returns:
            保存的文件路径
        """
        # 创建日期目录
        today = datetime.now().strftime('%Y-%m-%d')
        inbox_date_dir = INBOX_DIR / today
        inbox_date_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        safe_title = re.sub(r'[^\w\s-]', '', title)[:50]
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{safe_title}.md"
        filepath = inbox_date_dir / filename
        
        # 生成 Markdown 内容
        md_content = f"""# {title}

## 元数据

| 属性 | 值 |
|------|------|
| **来源** | [{url}]({url}) |
| **分类** | {classification.get('category', 'reading')} |
| **重要性** | {classification.get('importance', '值得关注')} |
| **标签** | {', '.join(classification.get('tags', []))} |
| **采集时间** | {datetime.now().strftime('%Y-%m-%d %H:%M')} |

## 摘要

{classification.get('summary', '暂无摘要')}

## 要点

"""
        for point in classification.get('key_points', []):
            md_content += f"- {point}\n"
        
        md_content += f"""
## 原文内容

{content[:3000]}

---
*由 link-collector 自动采集*
"""
        
        # 写入文件
        filepath.write_text(md_content, encoding='utf-8')
        
        return str(filepath)
    
    def process_link(self, url: str) -> Dict[str, Any]:
        """
        处理单个链接
        
        Args:
            url: 网页链接
            
        Returns:
            处理结果
        """
        print(f"正在处理: {url}")
        
        # 1. 提取内容
        extracted = self.extract_content(url)
        if 'error' in extracted:
            return extracted
        
        title = extracted.get('title', '未知标题')
        content = extracted.get('content', '')
        
        print(f"  标题: {title}")
        print(f"  内容长度: {len(content)} 字符")
        
        # 2. 智能分类
        print("  正在分类...")
        classification = self.classify_content(title, content, url)
        
        print(f"  分类: {classification.get('category')}")
        print(f"  重要性: {classification.get('importance')}")
        print(f"  标签: {classification.get('tags')}")
        
        # 3. 保存到收件箱
        filepath = self.save_to_inbox(url, title, content, classification)
        
        print(f"  已保存: {filepath}")
        
        return {
            'success': True,
            'title': title,
            'category': classification.get('category'),
            'importance': classification.get('importance'),
            'tags': classification.get('tags'),
            'summary': classification.get('summary'),
            'filepath': filepath
        }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python collector.py <URL>")
        print("示例: python collector.py https://example.com/article")
        return
    
    url = sys.argv[1]
    
    collector = LinkCollector()
    result = collector.process_link(url)
    
    print("\n" + "="*50)
    print("处理结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()