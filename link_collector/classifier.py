"""
Link-Collector V2.0 - 分类器

负责文章的智能分类、标签提取、重要性评估
"""

import os
import re
import json
from typing import Optional, List, Tuple
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .models import (
    Category, SubCategory, Importance,
    Classification, ImportanceInfo
)


# ============ 分类关键词定义 ============

CATEGORY_KEYWORDS = {
    Category.INVESTMENT: {
        "name": "投资理财",
        "keywords": ["股票", "估值", "财报", "投资", "基金", "PE", "PB", "ROE", "ROIC"],
        "sub_categories": {
            SubCategory.COMPANY_RESEARCH: {
                "name": "公司研究",
                "keywords": ["估值", "PE", "PB", "ROE", "财报", "年报", "商业模式", "利润", "现金流"]
            },
            SubCategory.INDUSTRY_ANALYSIS: {
                "name": "行业分析", 
                "keywords": ["行业", "赛道", "竞争", "格局", "市场规模", "产业链", "渗透率"]
            },
            SubCategory.INVESTMENT_PHILOSOPHY: {
                "name": "投资理念",
                "keywords": ["护城河", "安全边际", "价值投资", "巴菲特", "长期主义", "复利"]
            },
            SubCategory.MACRO_ECONOMY: {
                "name": "宏观经济",
                "keywords": ["GDP", "通胀", "利率", "政策", "周期", "央行", "货币"]
            },
            SubCategory.RESEARCH_REPORTS: {
                "name": "机构研报",
                "sources": ["Goldman Sachs", "Morgan Stanley", "高盛", "摩根士丹利", "中金", "中信"]
            }
        }
    },
    Category.TECH: {
        "name": "技术相关",
        "keywords": ["编程", "代码", "架构", "API", "框架", "算法", "AI", "机器学习"],
        "sub_categories": {
            SubCategory.PROGRAMMING: {"name": "编程语言", "keywords": ["Python", "JavaScript", "Go", "Rust"]},
            SubCategory.ARCHITECTURE: {"name": "架构设计", "keywords": ["微服务", "分布式", "架构"]},
            SubCategory.TECH_TOOLS: {"name": "工具使用", "keywords": ["Git", "Docker", "Linux"]},
            SubCategory.AI_ML: {"name": "AI/ML", "keywords": ["AI", "机器学习", "深度学习", "LLM", "GPT"]}
        }
    }
}

# 股票代码正则
STOCK_PATTERNS = [
    (r'拼多多|PDD\b', 'PDD'),
    (r'苹果|AAPL\b', 'AAPL'),
    (r'腾讯|00700\b', '00700'),
    (r'中海油|TCEHY\b', 'TCEHY'),
    (r'特斯拉|TSLA\b', 'TSLA'),
    (r'英伟达|NVDA\b', 'NVDA'),
    (r'META\b|Facebook', 'META'),
    (r'谷歌|GOOG\b|GOOGL\b', 'GOOG'),
    (r'亚马逊|AMZN\b', 'AMZN'),
    (r'微软|MSFT\b', 'MSFT'),
    (r'阿里巴巴|BABA\b', 'BABA'),
    (r'京东|JD\b', 'JD'),
    (r'百度|BIDU\b', 'BIDU'),
    (r'蔚来|NIO\b', 'NIO'),
    (r'小鹏|XPEV\b', 'XPEV'),
    (r'理想|LI\b', 'LI'),
]

# 价值投资关键词（用于评分）
VALUE_INVESTMENT_KEYWORDS = [
    '估值', 'PE', 'PB', 'ROE', 'ROIC', 'DCF', '自由现金流',
    '护城河', '安全边际', '商业模式', '竞争优势', '壁垒',
    '财报', '年报', '季报', '业绩',
    '内在价值', '价值投资',
    '毛利率', '净利率', '利润率', '周转率',
    '管理层', '资本配置', '股东回报'
]


class Classifier:
    """文章分类器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('BAILIAN_API_KEY', '')
        self.client = None
        
        if self.api_key and OpenAI:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
    
    def classify(self, title: str, content: str, url: str = None) -> Classification:
        """
        分类文章
        
        Args:
            title: 标题
            content: 内容
            url: 来源链接
        
        Returns:
            Classification 实例
        """
        # 先尝试 GLM-5 智能分类
        if self.client:
            try:
                return self._classify_with_llm(title, content, url)
            except Exception as e:
                print(f"LLM 分类失败: {e}")
        
        # 降级到规则分类
        return self._classify_with_rules(title, content, url)
    
    def _classify_with_llm(self, title: str, content: str, url: str) -> Classification:
        """使用 LLM 进行智能分类"""
        
        prompt = f"""你是一个内容分类助手。请分析以下内容，进行智能分类。

## 分类标准
- 主分类: investment(投资理财), tech(技术相关), life(生活日常), reading(阅读笔记), tools(工具资源)
- 子分类(investment): company-research(公司研究), industry-analysis(行业分析), investment-philosophy(投资理念), macro-economy(宏观经济), research-reports(机构研报)
- 重要性: must_read(必读), worth_reading(值得关注), reference(参考)

## 内容
标题: {title}
来源: {url or '未知'}
内容摘要: {content[:2000]}

## 输出要求
请以 JSON 格式输出：
{{
    "category": "主分类",
    "sub_category": "子分类（如有）",
    "tags": ["标签1", "标签2"],
    "related_stocks": ["股票代码"],
    "importance": "重要性级别"
}}

只输出 JSON，不要其他内容。"""

        completion = self.client.chat.completions.create(
            model="glm-5",
            messages=[{"role": "user", "content": prompt}],
        )
        
        response = completion.choices[0].message.content
        
        # 解析 JSON
        result = self._parse_json(response)
        
        return Classification(
            category=Category(result.get("category", "investment")),
            sub_category=SubCategory(result.get("sub_category")) if result.get("sub_category") else None,
            tags=result.get("tags", []),
            related_stocks=result.get("related_stocks", [])
        )
    
    def _classify_with_rules(self, title: str, content: str, url: str) -> Classification:
        """基于规则分类"""
        
        text = title + " " + content
        
        # 1. 确定主分类
        category = self._detect_category(text)
        
        # 2. 确定子分类
        sub_category = self._detect_sub_category(category, text, url)
        
        # 3. 提取标签
        tags = self._extract_tags(text)
        
        # 4. 提取股票
        stocks = self._extract_stocks(text)
        
        return Classification(
            category=category,
            sub_category=sub_category,
            tags=tags,
            related_stocks=stocks
        )
    
    def _detect_category(self, text: str) -> Category:
        """检测主分类"""
        scores = {}
        
        for cat, info in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in info.get("keywords", []) if kw in text)
            scores[cat] = score
        
        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best
        
        return Category.INVESTMENT  # 默认投资类
    
    def _detect_sub_category(self, category: Category, text: str, url: str) -> Optional[SubCategory]:
        """检测子分类"""
        
        if category not in CATEGORY_KEYWORDS:
            return None
        
        cat_info = CATEGORY_KEYWORDS[category]
        sub_cats = cat_info.get("sub_categories", {})
        
        # 检查机构来源
        if category == Category.INVESTMENT:
            reports_info = sub_cats.get(SubCategory.RESEARCH_REPORTS, {})
            sources = reports_info.get("sources", [])
            for source in sources:
                if source in text or (url and source in url):
                    return SubCategory.RESEARCH_REPORTS
        
        # 关键词匹配
        scores = {}
        for sub_cat, info in sub_cats.items():
            score = sum(1 for kw in info.get("keywords", []) if kw in text)
            if score > 0:
                scores[sub_cat] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        tags = []
        
        # 主题关键词
        theme_keywords = [
            "估值", "护城河", "安全边际", "财报", "年报",
            "商业模式", "竞争优势", "市场份额", "增长",
            "AI", "云计算", "电商", "新能源"
        ]
        
        for kw in theme_keywords:
            if kw in text and kw not in tags:
                tags.append(kw)
        
        return tags[:10]  # 最多 10 个
    
    def _extract_stocks(self, text: str) -> List[str]:
        """提取股票代码"""
        stocks = []
        
        for pattern, code in STOCK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if code not in stocks:
                    stocks.append(code)
        
        return stocks
    
    def calculate_importance(self, title: str, content: str, classification: Classification = None) -> ImportanceInfo:
        """
        计算重要性评分（复用 xueqiu-crawler 评分体系）
        
        总分 120 分:
        - 内容深度（30分）
        - 价值投资关键词（25分）
        - 价值投资相关性（20分）
        - 安全边际评估（15分）
        - 主题归类（10分）
        - 核心观点数量（10分）
        - 标题质量（10分）
        """
        scores = {
            "content_depth": 0,
            "keywords": 0,
            "value_alignment": 0,
            "safety_margin": 0,
            "category": 0,
            "core_points": 0,
            "title_quality": 0
        }
        
        # 1. 内容深度（最高 30 分）
        content_len = len(content)
        if content_len > 5000:
            scores["content_depth"] = 30
        elif content_len > 3000:
            scores["content_depth"] = 25
        elif content_len > 1500:
            scores["content_depth"] = 15
        elif content_len > 500:
            scores["content_depth"] = 5
        
        # 2. 价值投资关键词（最高 25 分）
        keyword_hits = sum(1 for kw in VALUE_INVESTMENT_KEYWORDS if kw in title + content)
        scores["keywords"] = min(keyword_hits * 2, 25)
        
        # 3. 分类相关（最高 20 分）
        if classification:
            if classification.category == Category.INVESTMENT:
                scores["category"] = 10
                if classification.sub_category == SubCategory.COMPANY_RESEARCH:
                    scores["category"] += 5
                elif classification.sub_category == SubCategory.RESEARCH_REPORTS:
                    scores["category"] += 5
        
        # 4. 标题质量（最高 10 分）
        title_keywords = ['深度', '分析', '研究', '估值', '财报', '年报', '护城河']
        if any(kw in title for kw in title_keywords):
            scores["title_quality"] = 10
        elif len(title) > 20:
            scores["title_quality"] = 5
        
        # 计算总分
        total = sum(scores.values())
        
        # 确定级别
        if total >= 70:
            level = Importance.MUST_READ
        elif total >= 40:
            level = Importance.WORTH_READING
        else:
            level = Importance.REFERENCE
        
        return ImportanceInfo(
            level=level,
            score=total,
            reason=f"内容{scores['content_depth']}+关键词{scores['keywords']}+归类{scores['category']}+标题{scores['title_quality']}"
        )
    
    def _parse_json(self, text: str) -> dict:
        """解析 JSON"""
        try:
            # 尝试提取 JSON 块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 尝试直接解析
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        return {}