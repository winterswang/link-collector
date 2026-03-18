"""
Link-Collector V2.0 - 索引管理器

负责维护多维度索引：按股票、按作者、按标签等
"""

import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
import uuid


@dataclass
class IndexEntry:
    """索引条目"""
    id: str
    title: str
    date: str
    source: str  # 作者或机构
    importance: str
    score: int
    path: str
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "source": self.source,
            "importance": self.importance,
            "score": self.score,
            "path": self.path
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "IndexEntry":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            date=data.get("date", ""),
            source=data.get("source", ""),
            importance=data.get("importance", "reference"),
            score=data.get("score", 0),
            path=data.get("path", "")
        )


class IndexManager:
    """索引管理器"""
    
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 索引文件路径
        self.by_stock_file = self.index_dir / "by_stock.json"
        self.by_author_file = self.index_dir / "by_author.json"
        self.by_tag_file = self.index_dir / "by_tag.json"
        self.by_source_file = self.index_dir / "by_source.json"
        
        # 内存索引
        self._by_stock: Dict[str, Dict] = {}
        self._by_author: Dict[str, Dict] = {}
        self._by_tag: Dict[str, Dict] = {}
        self._by_source: Dict[str, Dict] = {}
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 加载索引
        self._load_indexes()
    
    def _load_indexes(self):
        """加载所有索引"""
        self._by_stock = self._load_index(self.by_stock_file)
        self._by_author = self._load_index(self.by_author_file)
        self._by_tag = self._load_index(self.by_tag_file)
        self._by_source = self._load_index(self.by_source_file)
    
    def _load_index(self, file_path: Path) -> dict:
        """加载单个索引文件"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载索引失败 {file_path}: {e}")
        return {}
    
    def _save_index(self, file_path: Path, data: dict):
        """保存索引文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_article(self, article_meta: dict, article_path: str):
        """
        添加文章到索引
        
        Args:
            article_meta: 文章元数据
            article_path: 文章存储路径
        """
        with self._lock:
            entry = IndexEntry(
                id=article_meta.get("id", str(uuid.uuid4())),
                title=article_meta.get("title", ""),
                date=article_meta.get("timestamps", {}).get("created", "")[:10],
                source=article_meta.get("source", {}).get("author", "") or 
                       article_meta.get("source", {}).get("publisher", ""),
                importance=article_meta.get("importance", {}).get("level", "reference"),
                score=article_meta.get("importance", {}).get("score", 0),
                path=article_path
            )
            
            classification = article_meta.get("classification", {})
            
            # 按股票索引
            for stock in classification.get("related_stocks", []):
                if stock not in self._by_stock:
                    self._by_stock[stock] = {"count": 0, "articles": [], "last_updated": ""}
                
                self._by_stock[stock]["articles"].append(entry.to_dict())
                self._by_stock[stock]["count"] = len(self._by_stock[stock]["articles"])
                self._by_stock[stock]["last_updated"] = datetime.now().isoformat()
            
            # 按作者索引
            author = article_meta.get("source", {}).get("author")
            if author:
                if author not in self._by_author:
                    self._by_author[author] = {"count": 0, "articles": [], "last_updated": ""}
                
                self._by_author[author]["articles"].append(entry.to_dict())
                self._by_author[author]["count"] = len(self._by_author[author]["articles"])
                self._by_author[author]["last_updated"] = datetime.now().isoformat()
            
            # 按标签索引
            for tag in classification.get("tags", []):
                if tag not in self._by_tag:
                    self._by_tag[tag] = {"count": 0, "articles": [], "last_updated": ""}
                
                self._by_tag[tag]["articles"].append(entry.to_dict())
                self._by_tag[tag]["count"] = len(self._by_tag[tag]["articles"])
                self._by_tag[tag]["last_updated"] = datetime.now().isoformat()
            
            # 按来源平台索引
            platform = article_meta.get("source", {}).get("platform")
            if platform:
                if platform not in self._by_source:
                    self._by_source[platform] = {"count": 0, "articles": [], "last_updated": ""}
                
                self._by_source[platform]["articles"].append(entry.to_dict())
                self._by_source[platform]["count"] = len(self._by_source[platform]["articles"])
                self._by_source[platform]["last_updated"] = datetime.now().isoformat()
            
            # 保存索引
            self._save_all()
    
    def _save_all(self):
        """保存所有索引"""
        self._save_index(self.by_stock_file, self._by_stock)
        self._save_index(self.by_author_file, self._by_author)
        self._save_index(self.by_tag_file, self._by_tag)
        self._save_index(self.by_source_file, self._by_source)
    
    # ============ 查询方法 ============
    
    def get_by_stock(self, stock: str) -> List[dict]:
        """获取某股票的所有文章"""
        return self._by_stock.get(stock, {}).get("articles", [])
    
    def get_by_author(self, author: str) -> List[dict]:
        """获取某作者的所有文章"""
        return self._by_author.get(author, {}).get("articles", [])
    
    def get_by_tag(self, tag: str) -> List[dict]:
        """获取某标签的所有文章"""
        return self._by_tag.get(tag, {}).get("articles", [])
    
    def get_by_source(self, source: str) -> List[dict]:
        """获取某来源的所有文章"""
        return self._by_source.get(source, {}).get("articles", [])
    
    def search(self, 
               query: str = None,
               stock: str = None,
               author: str = None,
               tags: List[str] = None,
               importance: str = None,
               date_from: str = None,
               date_to: str = None,
               limit: int = 20) -> List[dict]:
        """
        多条件搜索
        
        Args:
            query: 关键词（匹配标题）
            stock: 股票代码
            author: 作者
            tags: 标签列表
            importance: 重要性
            date_from: 开始日期
            date_to: 结束日期
            limit: 返回数量
        
        Returns:
            文章列表（已去重）
        """
        all_candidates = []  # 收集所有候选文章
        seen_ids = set()
        
        # 收集候选文章
        if stock:
            for entry in self.get_by_stock(stock):
                if entry["id"] not in seen_ids:
                    all_candidates.append(entry)
                    seen_ids.add(entry["id"])
        
        if author:
            for entry in self.get_by_author(author):
                if entry["id"] not in seen_ids:
                    all_candidates.append(entry)
                    seen_ids.add(entry["id"])
        
        if tags:
            for tag in tags:
                for entry in self.get_by_tag(tag):
                    if entry["id"] not in seen_ids:
                        all_candidates.append(entry)
                        seen_ids.add(entry["id"])
        
        # 如果只有关键词查询
        if query and not stock and not author and not tags:
            query_lower = query.lower()
            collected_ids = set()
            
            # 收集所有文章
            for stock_data in self._by_stock.values():
                for entry in stock_data.get("articles", []):
                    if entry["id"] not in collected_ids:
                        all_candidates.append(entry)
                        collected_ids.add(entry["id"])
            
            for author_data in self._by_author.values():
                for entry in author_data.get("articles", []):
                    if entry["id"] not in collected_ids:
                        all_candidates.append(entry)
                        collected_ids.add(entry["id"])
            
            # 过滤：标题包含关键词
            results = [a for a in all_candidates if query_lower in a.get("title", "").lower()]
        else:
            results = all_candidates
        
        # 如果没有任何筛选条件，返回热门文章
        if not results and not stock and not author and not tags and not query:
            # 从所有股票索引中收集
            for stock_data in self._by_stock.values():
                for entry in stock_data.get("articles", []):
                    if entry["id"] not in seen_ids:
                        results.append(entry)
                        seen_ids.add(entry["id"])
        
        # 过滤重要性
        if importance:
            results = [r for r in results if r.get("importance") == importance]
        
        # 过滤日期
        if date_from:
            results = [r for r in results if r.get("date", "") >= date_from]
        if date_to:
            results = [r for r in results if r.get("date", "") <= date_to]
        
        # 按分数排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return results[:limit]
    
    def get_tag_cloud(self, min_count: int = 2, limit: int = 50) -> List[dict]:
        """
        获取标签云
        
        Returns:
            [{"tag": "估值", "count": 15}, ...]
        """
        tags = []
        for tag, data in self._by_tag.items():
            count = data.get("count", 0)
            if count >= min_count:
                tags.append({"tag": tag, "count": count})
        
        tags.sort(key=lambda x: x["count"], reverse=True)
        return tags[:limit]
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_stocks": len(self._by_stock),
            "total_authors": len(self._by_author),
            "total_tags": len(self._by_tag),
            "total_sources": len(self._by_source),
            "total_articles": sum(s.get("count", 0) for s in self._by_stock.values())
        }