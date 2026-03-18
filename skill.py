#!/usr/bin/env python3
"""
Link-Collector Skill - 知识库检索工具

用法:
    python skill.py search {关键词}
    python skill.py stock {股票代码}
    python skill.py author {作者}
    python skill.py tag {标签}
    python skill.py type {类型}
    python skill.py stats
    python skill.py aggregate {维度}
"""

import sys
import re
import json
from pathlib import Path

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent))

from link_collector import Library


def parse_args(text: str) -> dict:
    """
    解析用户输入
    
    Args:
        text: 用户输入文本
    
    Returns:
        {
            "action": "search/stock/author/tag/stats/aggregate",
            "query": "...",
            "filters": {...}
        }
    """
    text = text.strip()
    
    # 解析筛选条件
    filters = {}
    
    # --from 日期
    from_match = re.search(r'--from\s+(\d{4}-\d{2}-\d{2})', text)
    if from_match:
        filters['date_from'] = from_match.group(1)
        text = text.replace(from_match.group(0), '').strip()
    
    # --to 日期
    to_match = re.search(r'--to\s+(\d{4}-\d{2}-\d{2})', text)
    if to_match:
        filters['date_to'] = to_match.group(1)
        text = text.replace(to_match.group(0), '').strip()
    
    # --必读
    if '--必读' in text or '必读' in text:
        filters['importance'] = 'must_read'
        text = re.sub(r'--?必读', '', text).strip()
    
    # --值得关注
    if '--值得关注' in text or '值得关注' in text:
        filters['importance'] = 'worth_reading'
        text = re.sub(r'--?值得关注', '', text).strip()
    
    return {
        "text": text,
        "filters": filters
    }


def load_article_summary(lib: Library, article: dict) -> str:
    """
    加载文章摘要
    
    Args:
        lib: Library 实例
        article: 文章索引条目
    
    Returns:
        摘要文本
    """
    import json
    
    path = article.get('path', '')
    article_id = article.get('id', '')
    
    if not path and not article_id:
        return ''
    
    # 方法1: 从 JSON 文件加载
    inbox_dir = lib.inbox_dir
    
    for date_dir in inbox_dir.iterdir():
        if not date_dir.is_dir():
            continue
        
        # 通过 ID 查找
        if article_id:
            json_file = date_dir / f"{article_id}.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    content = data.get("content", {})
                    summary = content.get("summary", "")
                    key_points = content.get("key_points", [])
                    raw_content = content.get("raw_content", "")
                    
                    result = []
                    
                    # 如果有摘要
                    if summary:
                        result.append(f"📝 **摘要**: {summary[:150]}{'...' if len(summary) > 150 else ''}")
                    
                    # 如果有要点
                    if key_points:
                        result.append("💡 **要点**:")
                        for pt in key_points[:3]:
                            result.append(f"  - {pt[:80]}{'...' if len(pt) > 80 else ''}")
                    
                    # 如果有原始内容，提取前200字
                    if raw_content and not summary:
                        preview = raw_content[:200].replace('\n', ' ').strip()
                        result.append(f"📄 **内容预览**: {preview}...")
                    
                    if result:
                        return '\n'.join(result)
                        
                except Exception as e:
                    pass
    
    # 方法2: 从 MD 文件提取预览
    if path:
        try:
            md_path = Path(path)
            if md_path.exists():
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取内容预览部分
                preview_match = re.search(r'## 内容预览\s*\n(.*?)(?:\n---|\Z)', content, re.DOTALL)
                if preview_match:
                    preview = preview_match.group(1).strip()
                    # 清理换行和多余空格
                    preview = re.sub(r'\s+', ' ', preview)[:200]
                    if preview and not preview.startswith('*由 link-collector'):
                        return f"📄 **内容预览**: {preview}..."
                
        except Exception:
            pass
    
    return ''


def load_stock_codes(config_path: str = None) -> dict:
    """
    从配置文件加载股票代码映射
    
    Returns:
        {中文名/英文小写: 股票代码}
    """
    if config_path is None:
        config_path = Path(__file__).parent / "data" / "config" / "tag_rules.yaml"
    else:
        config_path = Path(config_path)
    
    stock_codes = {}
    
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            for stock_rule in config.get('stocks', []):
                tag = stock_rule.get('tag', '')
                company = stock_rule.get('company', '')
                pattern = stock_rule.get('pattern', '')
                
                if tag:
                    # 添加股票代码小写
                    stock_codes[tag.lower()] = tag
                    
                    # 添加公司名称
                    if company:
                        stock_codes[company.lower()] = tag
                    
                    # 从 pattern 提取关键词
                    if pattern:
                        # 简单提取中文和英文关键词
                        import re
                        keywords = re.findall(r'[\u4e00-\u9fa5]+|[A-Z]+', pattern)
                        for kw in keywords:
                            if kw and len(kw) > 1:
                                stock_codes[kw.lower()] = tag
        except Exception as e:
            print(f"加载股票配置失败: {e}")
    
    # 硬编码兜底
    fallback = {
        'pdd': 'PDD', '拼多多': 'PDD',
        'aapl': 'AAPL', '苹果': 'AAPL',
        '00700': '00700', '腾讯': '00700', 'tencent': '00700',
        'tcehy': 'TCEHY', '中海油': 'TCEHY',
        'tsla': 'TSLA', '特斯拉': 'TSLA',
        'nvda': 'NVDA', '英伟达': 'NVDA',
        'meta': 'META', 'facebook': 'META',
        'goog': 'GOOG', '谷歌': 'GOOG',
        'amzn': 'AMZN', '亚马逊': 'AMZN',
        'msft': 'MSFT', '微软': 'MSFT',
        'baba': 'BABA', '阿里巴巴': 'BABA', '阿里': 'BABA',
        'jd': 'JD', '京东': 'JD',
    }
    
    for k, v in fallback.items():
        if k not in stock_codes:
            stock_codes[k] = v
    
    return stock_codes


def cmd_search(lib: Library, args: list):
    """搜索文章"""
    if not args:
        print("❌ 请提供搜索关键词")
        return
    
    query = ' '.join(args)
    parsed = parse_args(query)
    
    # 加载股票代码映射
    stock_codes = load_stock_codes()
    
    query_lower = parsed['text'].lower()
    stock = stock_codes.get(query_lower)
    
    # 如果识别为股票代码，搜索股票相关文章
    if stock:
        results = lib.search(stock=stock, **parsed['filters'], limit=10)
        search_type = f"股票 {stock}"
    else:
        # 否则搜索关键词（标题匹配）
        results = lib.search(query=parsed['text'], **parsed['filters'], limit=10)
        search_type = parsed['text']
    
    if not results:
        print(f"❌ 未找到相关文章: {parsed['text']}")
        return
    
    # 统计分类
    by_importance = {'must_read': 0, 'worth_reading': 0, 'reference': 0}
    for article in results:
        imp = article.get('importance', 'reference')
        by_importance[imp] = by_importance.get(imp, 0) + 1
    
    print(f"📚 找到 {len(results)} 篇「{search_type}」相关文章\n")
    print(f"📊 分类统计: 🔴 必读 {by_importance['must_read']} 篇 | 🟡 值得关注 {by_importance['worth_reading']} 篇 | 🔵 参考 {by_importance['reference']} 篇\n")
    print("---\n")
    
    for i, article in enumerate(results, 1):
        title = article.get('title', '无标题')
        source = article.get('source', '未知')
        date = article.get('date', '')
        importance = article.get('importance', 'reference')
        score = article.get('score', 0)
        
        # 重要性标签
        imp_emoji = {'must_read': '🔴', 'worth_reading': '🟡', 'reference': '🔵'}
        imp_text = {'must_read': '必读', 'worth_reading': '值得关注', 'reference': '参考'}
        
        print(f"## {i}. {title[:100]}{'...' if len(title) > 100 else ''}\n")
        print(f"| 属性 | 值 |")
        print(f"|------|------|")
        print(f"| 来源 | {source} |")
        print(f"| 日期 | {date} |")
        print(f"| 重要性 | {imp_emoji.get(importance, '🔵')} {imp_text.get(importance, '参考')} ({score}分) |")
        print()
        
        # 加载摘要
        summary = load_article_summary(lib, article)
        if summary:
            print(summary)
            print()
        
        print("---\n")


def cmd_stock(lib: Library, args: list):
    """按股票搜索"""
    if not args:
        # 显示股票列表
        stocks = sorted(lib.indexer._by_stock.items(), 
                       key=lambda x: x[1].get('count', 0), reverse=True)[:15]
        print("📈 热门股票:\n")
        for stock, data in stocks:
            print(f"  {stock}: {data.get('count', 0)} 篇")
        return
    
    stock = args[0].upper()
    parsed = parse_args(' '.join(args[1:]))
    
    results = lib.search(
        stock=stock,
        **parsed['filters'],
        limit=10
    )
    
    if not results:
        print(f"❌ 未找到 {stock} 相关文章")
        return
    
    # 统计分类
    by_importance = {'must_read': 0, 'worth_reading': 0, 'reference': 0}
    for article in results:
        imp = article.get('importance', 'reference')
        by_importance[imp] = by_importance.get(imp, 0) + 1
    
    print(f"📚 {stock} 相关文章 ({len(results)} 篇)\n")
    print(f"📊 分类统计: 🔴 必读 {by_importance['must_read']} 篇 | 🟡 值得关注 {by_importance['worth_reading']} 篇 | 🔵 参考 {by_importance['reference']} 篇\n")
    print("---\n")
    
    for i, article in enumerate(results, 1):
        title = article.get('title', '无标题')
        source = article.get('source', '未知')
        date = article.get('date', '')
        importance = article.get('importance', 'reference')
        score = article.get('score', 0)
        
        imp_emoji = {'must_read': '🔴', 'worth_reading': '🟡', 'reference': '🔵'}
        imp_text = {'must_read': '必读', 'worth_reading': '值得关注', 'reference': '参考'}
        
        print(f"## {i}. {title[:100]}{'...' if len(title) > 100 else ''}\n")
        print(f"| 属性 | 值 |")
        print(f"|------|------|")
        print(f"| 来源 | {source} |")
        print(f"| 日期 | {date} |")
        print(f"| 重要性 | {imp_emoji.get(importance, '🔵')} {imp_text.get(importance, '参考')} ({score}分) |")
        print()
        
        # 加载摘要
        summary = load_article_summary(lib, article)
        if summary:
            print(summary)
            print()
        
        print("---\n")


def cmd_author(lib: Library, args: list):
    """按作者搜索"""
    if not args:
        authors = sorted(lib.indexer._by_author.items(),
                        key=lambda x: x[1].get('count', 0), reverse=True)[:10]
        print("👥 作者列表:\n")
        for author, data in authors:
            print(f"  {author}: {data.get('count', 0)} 篇")
        return
    
    author = ' '.join(args)
    parsed = parse_args('')
    
    results = lib.search(
        author=author,
        **parsed['filters'],
        limit=10
    )
    
    if not results:
        print(f"❌ 未找到作者: {author}")
        return
    
    # 统计分类
    by_importance = {'must_read': 0, 'worth_reading': 0, 'reference': 0}
    for article in results:
        imp = article.get('importance', 'reference')
        by_importance[imp] = by_importance.get(imp, 0) + 1
    
    print(f"📚 {author} 的文章 ({len(results)} 篇)\n")
    print(f"📊 分类统计: 🔴 必读 {by_importance['must_read']} 篇 | 🟡 值得关注 {by_importance['worth_reading']} 篇 | 🔵 参考 {by_importance['reference']} 篇\n")
    print("---\n")
    
    for i, article in enumerate(results, 1):
        title = article.get('title', '无标题')
        date = article.get('date', '')
        importance = article.get('importance', 'reference')
        score = article.get('score', 0)
        
        imp_emoji = {'must_read': '🔴', 'worth_reading': '🟡', 'reference': '🔵'}
        imp_text = {'must_read': '必读', 'worth_reading': '值得关注', 'reference': '参考'}
        
        print(f"## {i}. {title[:100]}{'...' if len(title) > 100 else ''}\n")
        print(f"| 属性 | 值 |")
        print(f"|------|------|")
        print(f"| 日期 | {date} |")
        print(f"| 重要性 | {imp_emoji.get(importance, '🔵')} {imp_text.get(importance, '参考')} ({score}分) |")
        print()
        
        # 加载摘要
        summary = load_article_summary(lib, article)
        if summary:
            print(summary)
            print()
        
        print("---\n")


def cmd_tag(lib: Library, args: list):
    """按标签搜索"""
    if not args:
        tags = lib.get_tag_cloud(min_count=1, limit=20)
        print("🏷️ 热门标签:\n")
        for tag in tags:
            print(f"  {tag['tag']}: {tag['count']} 篇")
        return
    
    tag = ' '.join(args)
    
    results = lib.search(
        tags=[tag],
        limit=10
    )
    
    if not results:
        print(f"❌ 未找到标签: {tag}")
        return
    
    # 统计分类
    by_importance = {'must_read': 0, 'worth_reading': 0, 'reference': 0}
    for article in results:
        imp = article.get('importance', 'reference')
        by_importance[imp] = by_importance.get(imp, 0) + 1
    
    print(f"📚 标签「{tag}」相关文章 ({len(results)} 篇)\n")
    print(f"📊 分类统计: 🔴 必读 {by_importance['must_read']} 篇 | 🟡 值得关注 {by_importance['worth_reading']} 篇 | 🔵 参考 {by_importance['reference']} 篇\n")
    print("---\n")
    
    for i, article in enumerate(results, 1):
        title = article.get('title', '无标题')
        source = article.get('source', '未知')
        date = article.get('date', '')
        importance = article.get('importance', 'reference')
        score = article.get('score', 0)
        
        imp_emoji = {'must_read': '🔴', 'worth_reading': '🟡', 'reference': '🔵'}
        imp_text = {'must_read': '必读', 'worth_reading': '值得关注', 'reference': '参考'}
        
        print(f"## {i}. {title[:100]}{'...' if len(title) > 100 else ''}\n")
        print(f"| 属性 | 值 |")
        print(f"|------|------|")
        print(f"| 来源 | {source} |")
        print(f"| 日期 | {date} |")
        print(f"| 重要性 | {imp_emoji.get(importance, '🔵')} {imp_text.get(importance, '参考')} ({score}分) |")
        print()
        
        # 加载摘要
        summary = load_article_summary(lib, article)
        if summary:
            print(summary)
            print()
        
        print("---\n")


def cmd_type(lib: Library, args: list):
    """按类型搜索"""
    type_map = {
        'annual': ('年报', ['年报', 'Annual']),
        'quarterly': ('季报', ['季报', 'Quarterly']),
        'report': ('研报', ['研报', '研究报告']),
    }
    
    if not args:
        print("❌ 请指定类型: annual/quarterly/report")
        return
    
    file_type = args[0].lower()
    if file_type not in type_map:
        print(f"❌ 未知类型: {file_type}")
        print(f"   支持的类型: {', '.join(type_map.keys())}")
        return
    
    type_name, type_tags = type_map[file_type]
    
    results = lib.search(
        tags=type_tags,
        limit=10
    )
    
    if not results:
        print(f"❌ 未找到{type_name}相关文章")
        return
    
    print(f"📚 {type_name} ({len(results)} 篇):\n")
    
    for i, article in enumerate(results, 1):
        title = article.get('title', '无标题')[:60]
        source = article.get('source', '未知')
        score = article.get('score', 0)
        
        print(f"{i}. {title}...")
        print(f"   来源: {source} | {score}分")
        print()


def cmd_stats(lib: Library):
    """显示统计信息"""
    stats = lib.get_stats()
    
    print("📊 Link-Collector 知识库统计\n")
    print(f"  总文章数: {stats.get('total_articles', 0)}")
    print(f"  股票数: {stats.get('total_stocks', 0)}")
    print(f"  作者数: {stats.get('total_authors', 0)}")
    print(f"  标签数: {stats.get('total_tags', 0)}")
    print(f"  来源数: {stats.get('total_sources', 0)}")
    
    # 热门标签
    print("\n🏷️ 热门标签:")
    tags = lib.get_tag_cloud(min_count=2, limit=10)
    for tag in tags:
        print(f"  {tag['tag']}: {tag['count']} 篇")
    
    # 热门股票
    print("\n📈 热门股票:")
    stocks = sorted(lib.indexer._by_stock.items(),
                   key=lambda x: x[1].get('count', 0), reverse=True)[:10]
    for stock, data in stocks:
        print(f"  {stock}: {data.get('count', 0)} 篇")


def cmd_aggregate(lib: Library, args: list):
    """聚合查询"""
    dimension = args[0] if args else 'stock'
    
    if dimension in ['stock', '股票']:
        stocks = sorted(lib.indexer._by_stock.items(),
                       key=lambda x: x[1].get('count', 0), reverse=True)
        print(f"📊 按股票聚合 ({len(stocks)} 只股票)\n")
        for stock, data in stocks[:20]:
            print(f"  {stock}: {data.get('count', 0)} 篇")
    
    elif dimension in ['author', '作者']:
        authors = sorted(lib.indexer._by_author.items(),
                        key=lambda x: x[1].get('count', 0), reverse=True)
        print(f"📊 按作者聚合 ({len(authors)} 位作者)\n")
        for author, data in authors[:20]:
            print(f"  {author}: {data.get('count', 0)} 篇")
    
    elif dimension in ['tag', '标签']:
        tags = lib.get_tag_cloud(min_count=1, limit=30)
        print(f"📊 按标签聚合\n")
        for tag in tags:
            print(f"  {tag['tag']}: {tag['count']} 篇")
    
    else:
        print(f"❌ 未知聚合维度: {dimension}")
        print("   支持的维度: stock/股票, author/作者, tag/标签")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    lib = Library()
    
    if command == 'search':
        cmd_search(lib, args)
    elif command == 'stock':
        cmd_stock(lib, args)
    elif command == 'author':
        cmd_author(lib, args)
    elif command == 'tag':
        cmd_tag(lib, args)
    elif command == 'type':
        cmd_type(lib, args)
    elif command == 'stats':
        cmd_stats(lib)
    elif command == 'aggregate':
        cmd_aggregate(lib, args)
    else:
        print(f"❌ 未知命令: {command}")
        print("   支持的命令: search, stock, author, tag, type, stats, aggregate")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())