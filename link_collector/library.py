"""
Link-Collector V2.0 - 知识库管理

提供检索、聚合等高级功能
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import ArticleMeta
from .indexer import IndexManager


class Library:
    """知识库管理器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化知识库
        
        Args:
            data_dir: 数据目录
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data"
        
        self.inbox_dir = self.data_dir / "inbox"
        self.library_dir = self.data_dir / "library"
        self.index_dir = self.data_dir / "index"
        
        self.indexer = IndexManager(self.index_dir)
    
    # ============ 检索方法 ============
    
    def search(self, 
               query: str = None,
               stock: str = None,
               author: str = None,
               publisher: str = None,
               tags: List[str] = None,
               importance: str = None,
               category: str = None,
               sub_category: str = None,
               date_from: str = None,
               date_to: str = None,
               limit: int = 20) -> List[dict]:
        """
        搜索文章
        
        Args:
            query: 关键词
            stock: 股票代码
            author: 作者
            publisher: 机构/发布者
            tags: 标签列表
            importance: 重要性级别
            category: 主分类
            sub_category: 子分类
            date_from: 开始日期
            date_to: 结束日期
            limit: 返回数量
        
        Returns:
            文章条目列表（dict 格式，包含 id, title, date, source 等）
        """
        # 从索引搜索
        entries = self.indexer.search(
            query=query,
            stock=stock,
            author=author,
            tags=tags,
            importance=importance,
            date_from=date_from,
            date_to=date_to,
            limit=limit * 2  # 多取一些，后面再过滤
        )
        
        # 过滤结果
        results = []
        for entry in entries:
            # 过滤 publisher
            if publisher:
                source = entry.get("source", "")
                if publisher.lower() not in source.lower():
                    continue
            
            # category 和 sub_category 需要从元数据获取
            # 暂时跳过，后续可以优化
            
            results.append(entry)
            if len(results) >= limit:
                break
        
        return results
    
    def search_detailed(self, 
                        query: str = None,
                        stock: str = None,
                        author: str = None,
                        publisher: str = None,
                        tags: List[str] = None,
                        importance: str = None,
                        category: str = None,
                        sub_category: str = None,
                        date_from: str = None,
                        date_to: str = None,
                        limit: int = 20) -> List[ArticleMeta]:
        """
        搜索文章（返回完整 ArticleMeta 对象）
        
        注意：此方法会加载完整元数据，较慢
        """
        entries = self.search(
            query=query, stock=stock, author=author, publisher=publisher,
            tags=tags, importance=importance, category=category, sub_category=sub_category,
            date_from=date_from, date_to=date_to, limit=limit
        )
        
        results = []
        for entry in entries:
            meta = self._load_article_meta(entry.get("path", ""))
            if meta:
                results.append(meta)
        
        return results
    
    def get_by_stock(self, stock: str) -> List[ArticleMeta]:
        """获取某股票的所有文章"""
        entries = self.indexer.get_by_stock(stock)
        return [self._load_article_meta(e["path"]) for e in entries if self._load_article_meta(e["path"])]
    
    def get_by_author(self, author: str) -> List[ArticleMeta]:
        """获取某作者的所有文章"""
        entries = self.indexer.get_by_author(author)
        return [self._load_article_meta(e["path"]) for e in entries if self._load_article_meta(e["path"])]
    
    def get_by_tag(self, tag: str) -> List[ArticleMeta]:
        """获取某标签的所有文章"""
        entries = self.indexer.get_by_tag(tag)
        return [self._load_article_meta(e["path"]) for e in entries if self._load_article_meta(e["path"])]
    
    def get_by_publisher(self, publisher: str) -> List[ArticleMeta]:
        """获取某机构/发布者的所有文章"""
        results = []
        for source, data in self.indexer._by_source.items():
            if publisher.lower() in source.lower():
                for entry in data.get("articles", []):
                    meta = self._load_article_meta(entry.get("path", ""))
                    if meta:
                        results.append(meta)
        return results
    
    def get_tag_cloud(self, min_count: int = 2, limit: int = 50) -> List[dict]:
        """获取标签云"""
        return self.indexer.get_tag_cloud(min_count, limit)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.indexer.get_stats()
    
    def get_related(self, article_id: str, limit: int = 5) -> List[ArticleMeta]:
        """
        获取相关文章
        
        基于标签和股票的相似度推荐
        """
        # TODO: 实现相关文章推荐
        return []
    
    def add(self, file_path: str, metadata: dict = None) -> Optional[ArticleMeta]:
        """
        添加文章到知识库
        
        Args:
            file_path: 文件路径
            metadata: 元数据（可选）
        
        Returns:
            ArticleMeta 或 None
        """
        from .service import CollectorService
        
        service = CollectorService(
            data_dir=str(self.data_dir)
        )
        
        result = service.process_file(
            file_path,
            options=metadata or {}
        )
        
        if result.get("success"):
            return ArticleMeta.from_dict(result["metadata"])
        return None
    
    # ============ 内部方法 ============
    
    def _load_article_meta(self, path: str) -> Optional[ArticleMeta]:
        """加载文章元数据"""
        if not path:
            return None
        
        path = Path(path)
        
        # 索引中的 path 是 .md 文件路径
        # 对应的 JSON 文件在同一目录下，文件名是 {article_id}.json
        
        # 从 inbox 目录加载 json 文件
        inbox_dir = self.inbox_dir
        
        # 扫描所有日期目录
        for date_dir in inbox_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            # 查找对应的 json 文件
            for json_file in date_dir.glob("*.json"):
                try:
                    import json as json_mod
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json_mod.load(f)
                    
                    # 检查 raw_file 是否匹配
                    raw_file = data.get("raw_file", "")
                    if raw_file and Path(raw_file).name == Path(path).name:
                        return ArticleMeta.from_dict(data)
                    
                except Exception:
                    continue
        
        return None