"""
Link-Collector V2.0 - 数据模型

定义文章元数据、内容等核心数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json
import uuid


class Category(str, Enum):
    """主分类"""
    INVESTMENT = "investment"
    TECH = "tech"
    LIFE = "life"
    READING = "reading"
    TOOLS = "tools"


class SubCategory(str, Enum):
    """子分类"""
    # Investment
    COMPANY_RESEARCH = "company-research"
    INDUSTRY_ANALYSIS = "industry-analysis"
    INVESTMENT_PHILOSOPHY = "investment-philosophy"
    MACRO_ECONOMY = "macro-economy"
    RESEARCH_REPORTS = "research-reports"
    
    # Tech
    PROGRAMMING = "programming"
    ARCHITECTURE = "architecture"
    TECH_TOOLS = "tech-tools"
    AI_ML = "ai-ml"


class Importance(str, Enum):
    """重要性级别"""
    MUST_READ = "must_read"
    WORTH_READING = "worth_reading"
    REFERENCE = "reference"


class SourceType(str, Enum):
    """来源类型"""
    WEB = "web"
    PDF = "pdf"
    EXCEL = "excel"
    MARKDOWN = "markdown"
    IMAGE = "image"


@dataclass
class Source:
    """来源信息"""
    type: SourceType
    url: Optional[str] = None
    platform: Optional[str] = None  # xueqiu, feishu, wechat 等
    author: Optional[str] = None
    author_id: Optional[str] = None
    original_id: Optional[str] = None
    publisher: Optional[str] = None  # 机构名称
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value if self.type else None,
            "url": self.url,
            "platform": self.platform,
            "author": self.author,
            "author_id": self.author_id,
            "original_id": self.original_id,
            "publisher": self.publisher
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        return cls(
            type=SourceType(data.get("type")) if data.get("type") else None,
            url=data.get("url"),
            platform=data.get("platform"),
            author=data.get("author"),
            author_id=data.get("author_id"),
            original_id=data.get("original_id"),
            publisher=data.get("publisher")
        )


@dataclass
class Classification:
    """分类信息"""
    category: Category
    sub_category: Optional[SubCategory] = None
    tags: List[str] = field(default_factory=list)
    related_stocks: List[str] = field(default_factory=list)
    related_companies: List[str] = field(default_factory=list)
    related_industries: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "category": self.category.value if self.category else None,
            "sub_category": self.sub_category.value if self.sub_category else None,
            "tags": self.tags,
            "related_stocks": self.related_stocks,
            "related_companies": self.related_companies,
            "related_industries": self.related_industries
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Classification":
        return cls(
            category=Category(data.get("category")) if data.get("category") else None,
            sub_category=SubCategory(data.get("sub_category")) if data.get("sub_category") else None,
            tags=data.get("tags", []),
            related_stocks=data.get("related_stocks", []),
            related_companies=data.get("related_companies", []),
            related_industries=data.get("related_industries", [])
        )


@dataclass
class ImportanceInfo:
    """重要性信息"""
    level: Importance
    score: int = 0  # 0-120
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "level": self.level.value if self.level else None,
            "score": self.score,
            "reason": self.reason
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImportanceInfo":
        return cls(
            level=Importance(data.get("level")) if data.get("level") else None,
            score=data.get("score", 0),
            reason=data.get("reason")
        )


@dataclass
class ArticleContent:
    """文章内容"""
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    word_count: int = 0
    language: str = "zh-CN"
    raw_content: Optional[str] = None  # 原始内容
    
    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "key_points": self.key_points,
            "word_count": self.word_count,
            "language": self.language
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ArticleContent":
        return cls(
            summary=data.get("summary"),
            key_points=data.get("key_points", []),
            word_count=data.get("word_count", 0),
            language=data.get("language", "zh-CN")
        )


@dataclass
class Timestamps:
    """时间戳"""
    created: datetime
    published: Optional[str] = None  # 原文发布日期
    modified: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "created": self.created.isoformat() if self.created else None,
            "published": self.published,
            "modified": self.modified.isoformat() if self.modified else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Timestamps":
        return cls(
            created=datetime.fromisoformat(data["created"]) if data.get("created") else datetime.now(),
            published=data.get("published"),
            modified=datetime.fromisoformat(data["modified"]) if data.get("modified") else None
        )


@dataclass
class Relations:
    """关联信息"""
    related_articles: List[str] = field(default_factory=list)  # 关联文章ID
    series: Optional[str] = None  # 系列名称
    parent: Optional[str] = None  # 父文章ID
    
    def to_dict(self) -> dict:
        return {
            "related_articles": self.related_articles,
            "series": self.series,
            "parent": self.parent
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Relations":
        return cls(
            related_articles=data.get("related_articles", []),
            series=data.get("series"),
            parent=data.get("parent")
        )


@dataclass
class ArticleMeta:
    """文章元数据（完整 Schema）"""
    id: str
    title: str
    source: Source
    classification: Classification
    importance: ImportanceInfo
    content: ArticleContent
    timestamps: Timestamps
    relations: Relations = field(default_factory=Relations)
    raw_file: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source.to_dict(),
            "classification": self.classification.to_dict(),
            "importance": self.importance.to_dict(),
            "content": self.content.to_dict(),
            "timestamps": self.timestamps.to_dict(),
            "relations": self.relations.to_dict(),
            "raw_file": self.raw_file
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ArticleMeta":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            source=Source.from_dict(data.get("source", {})),
            classification=Classification.from_dict(data.get("classification", {})),
            importance=ImportanceInfo.from_dict(data.get("importance", {})),
            content=ArticleContent.from_dict(data.get("content", {})),
            timestamps=Timestamps.from_dict(data.get("timestamps", {})),
            relations=Relations.from_dict(data.get("relations", {})),
            raw_file=data.get("raw_file")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "ArticleMeta":
        return cls.from_dict(json.loads(json_str))


# ============ 简化构造方法 ============

def create_article(
    title: str,
    url: str = None,
    content: str = None,
    category: str = "investment",
    sub_category: str = None,
    tags: List[str] = None,
    related_stocks: List[str] = None,
    importance_level: str = "worth_reading",
    score: int = 0,
    author: str = None,
    platform: str = None
) -> ArticleMeta:
    """
    简化的文章创建方法
    
    Args:
        title: 标题
        url: 来源链接
        content: 内容
        category: 主分类
        sub_category: 子分类
        tags: 标签列表
        related_stocks: 关联股票
        importance_level: 重要性级别
        score: 评分
        author: 作者
        platform: 平台
    
    Returns:
        ArticleMeta 实例
    """
    return ArticleMeta(
        id=str(uuid.uuid4()),
        title=title,
        source=Source(
            type=SourceType.WEB,
            url=url,
            author=author,
            platform=platform
        ),
        classification=Classification(
            category=Category(category) if category else Category.INVESTMENT,
            sub_category=SubCategory(sub_category) if sub_category else None,
            tags=tags or [],
            related_stocks=related_stocks or []
        ),
        importance=ImportanceInfo(
            level=Importance(importance_level) if importance_level else Importance.WORTH_READING,
            score=score
        ),
        content=ArticleContent(
            raw_content=content,
            word_count=len(content) if content else 0
        ),
        timestamps=Timestamps(created=datetime.now())
    )