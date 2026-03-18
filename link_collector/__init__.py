"""
Link-Collector V2.0 - 智能知识管理系统

提供内容采集、分类、存储、检索能力
"""

from .models import ArticleMeta, ArticleContent
from .service import CollectorService
from .library import Library
from .indexer import IndexManager
from .classifier import Classifier

__version__ = "2.0.0"
__all__ = [
    "CollectorService",
    "Library", 
    "ArticleMeta",
    "ArticleContent",
    "IndexManager",
    "Classifier"
]