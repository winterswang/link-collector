#!/usr/bin/env python3
"""
Link-Collector V2.0 CLI

命令行工具入口
"""

import argparse
import json
import sys
from pathlib import Path

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from link_collector import CollectorService, Library


def cmd_process(args):
    """处理链接/文件"""
    service = CollectorService()
    
    if args.url:
        result = service.process_url(
            args.url,
            options={
                "category": args.category,
                "sub_category": args.sub_category,
                "tags": args.tags.split(",") if args.tags else None,
                "related_stocks": args.stocks.split(",") if args.stocks else None,
                "importance": args.importance,
                "save_to": args.save_to,
                "no_library": args.no_library
            }
        )
    elif args.file:
        result = service.process_file(
            args.file,
            options={
                "category": args.category,
                "sub_category": args.sub_category,
                "tags": args.tags.split(",") if args.tags else None,
                "related_stocks": args.stocks.split(",") if args.stocks else None,
                "importance": args.importance,
                "save_to": args.save_to,
                "no_library": args.no_library
            }
        )
    else:
        print("请指定 --url 或 --file")
        return 1
    
    if result.get("success"):
        print(f"✅ 处理成功")
        print(f"  ID: {result['id']}")
        print(f"  标题: {result['metadata']['title'][:50]}...")
        print(f"  主存储: {result['paths'].get('primary', '')}")
        if result['paths'].get('copy'):
            print(f"  副本: {result['paths']['copy']}")
        print(f"  分类: {result['metadata']['classification']['category']}", end="")
        if result['metadata']['classification'].get('sub_category'):
            print(f" / {result['metadata']['classification']['sub_category']}")
        else:
            print()
        print(f"  重要性: {result['metadata']['importance']['level']} ({result['metadata']['importance']['score']}分)")
        if result['metadata']['classification'].get('tags'):
            print(f"  标签: {', '.join(result['metadata']['classification']['tags'][:5])}")
        if result['metadata']['classification'].get('related_stocks'):
            print(f"  股票: {', '.join(result['metadata']['classification']['related_stocks'])}")
    else:
        print(f"❌ 处理失败: {result.get('error', '未知错误')}")
        return 1
    
    return 0


def cmd_search(args):
    """搜索文章"""
    lib = Library()
    
    results = lib.search(
        query=args.query,
        stock=args.stock,
        author=args.author,
        publisher=args.publisher,
        tags=args.tags.split(",") if args.tags else None,
        importance=args.importance,
        category=args.category,
        sub_category=args.sub_category,
        date_from=args.from_date,
        date_to=args.to_date,
        limit=args.limit
    )
    
    if not results:
        print("未找到匹配的文章")
        return 0
    
    print(f"找到 {len(results)} 篇文章:\n")
    
    for i, article in enumerate(results, 1):
        title = article.get("title", "无标题")
        source = article.get("source", "")
        date = article.get("date", "")
        importance = article.get("importance", "reference")
        score = article.get("score", 0)
        
        print(f"{i}. {title[:60]}...")
        print(f"   来源: {source}")
        print(f"   日期: {date}")
        print(f"   重要性: {importance} ({score}分)")
        print()
    
    return 0


def cmd_aggregate(args):
    """聚合查询"""
    lib = Library()
    
    by = args.by
    
    if by == "stock":
        stocks = lib.indexer._by_stock
        if not stocks:
            print("暂无股票数据")
            return 0
        
        print(f"📊 按股票聚合 ({len(stocks)} 只股票)\n")
        sorted_stocks = sorted(stocks.items(), key=lambda x: x[1].get('count', 0), reverse=True)
        for stock, data in sorted_stocks[:20]:
            print(f"  {stock}: {data.get('count', 0)} 篇")
    
    elif by == "author":
        authors = lib.indexer._by_author
        if not authors:
            print("暂无作者数据")
            return 0
        
        print(f"📊 按作者聚合 ({len(authors)} 位作者)\n")
        sorted_authors = sorted(authors.items(), key=lambda x: x[1].get('count', 0), reverse=True)
        for author, data in sorted_authors[:20]:
            print(f"  {author}: {data.get('count', 0)} 篇")
    
    elif by == "tag":
        tags = lib.get_tag_cloud(min_count=1, limit=30)
        if not tags:
            print("暂无标签数据")
            return 0
        
        print(f"📊 按标签聚合\n")
        for tag in tags:
            print(f"  {tag['tag']}: {tag['count']} 篇")
    
    elif by == "source":
        sources = lib.indexer._by_source
        if not sources:
            print("暂无来源数据")
            return 0
        
        print(f"📊 按来源聚合 ({len(sources)} 个来源)\n")
        sorted_sources = sorted(sources.items(), key=lambda x: x[1].get('count', 0), reverse=True)
        for source, data in sorted_sources[:20]:
            print(f"  {source}: {data.get('count', 0)} 篇")
    
    else:
        print(f"不支持的聚合类型: {by}")
        print("支持: stock, author, tag, source")
        return 1
    
    return 0


def cmd_stats(args):
    """显示统计信息"""
    lib = Library()
    stats = lib.get_stats()
    
    print("📊 Link-Collector 知识库统计\n")
    print(f"  总文章数: {stats.get('total_articles', 0)}")
    print(f"  股票数: {stats.get('total_stocks', 0)}")
    print(f"  作者数: {stats.get('total_authors', 0)}")
    print(f"  标签数: {stats.get('total_tags', 0)}")
    print(f"  来源数: {stats.get('total_sources', 0)}")
    
    # 标签云
    if not args.no_tags:
        print("\n🏷️ 热门标签:")
        tags = lib.get_tag_cloud(min_count=2, limit=10)
        for tag in tags:
            print(f"  {tag['tag']}: {tag['count']} 篇")
    
    # 热门股票
    if not args.no_stocks:
        print("\n📈 热门股票:")
        stocks = sorted(lib.indexer._by_stock.items(), key=lambda x: x[1].get('count', 0), reverse=True)[:10]
        for stock, data in stocks:
            print(f"  {stock}: {data.get('count', 0)} 篇")
    
    return 0


def cmd_classify(args):
    """仅分类（不存储）"""
    service = CollectorService()
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        title = args.title or Path(args.file).stem
    else:
        title = args.title or "未命名"
        content = args.content or ""
    
    result = service.classify_only(title, content)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_fetch(args):
    """仅爬取（不存储）"""
    service = CollectorService()
    
    result = service.fetch_only(args.url)
    
    if result:
        print(f"标题: {result.get('title', '')}")
        print(f"作者: {result.get('author', '未知')}")
        print(f"字数: {len(result.get('content', ''))}")
        
        if args.full:
            print(f"\n完整内容:\n{result.get('content', '')}")
        else:
            print(f"\n内容预览:\n{result.get('content', '')[:500]}...")
    else:
        print("❌ 爬取失败")
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Link-Collector V2.0 - 智能知识管理系统"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # ========== process 命令 ==========
    process_parser = subparsers.add_parser("process", help="处理链接或文件")
    process_parser.add_argument("--url", help="要处理的 URL")
    process_parser.add_argument("--file", "-f", help="要处理的本地文件")
    process_parser.add_argument("--category", "-c", help="指定主分类 (investment/tech/life/reading/tools)")
    process_parser.add_argument("--sub-category", "--sub", help="指定子分类")
    process_parser.add_argument("--tags", "-t", help="预设标签（逗号分隔）")
    process_parser.add_argument("--stocks", "-s", help="关联股票（逗号分隔）")
    process_parser.add_argument("--importance", "-i", help="预设重要性 (must_read/worth_reading/reference)")
    process_parser.add_argument("--save-to", help="额外保存路径")
    process_parser.add_argument("--no-library", action="store_true", help="不写入知识库")
    process_parser.set_defaults(func=cmd_process)
    
    # ========== search 命令 ==========
    search_parser = subparsers.add_parser("search", help="搜索文章")
    search_parser.add_argument("query", nargs="?", help="搜索关键词")
    search_parser.add_argument("--stock", "-s", help="按股票筛选")
    search_parser.add_argument("--author", "-a", help="按作者筛选")
    search_parser.add_argument("--publisher", "-p", help="按机构筛选")
    search_parser.add_argument("--category", "-c", help="按主分类筛选")
    search_parser.add_argument("--sub-category", "--sub", help="按子分类筛选")
    search_parser.add_argument("--tags", "-t", help="按标签筛选（逗号分隔）")
    search_parser.add_argument("--importance", "-i", help="按重要性筛选 (must_read/worth_reading/reference)")
    search_parser.add_argument("--from-date", help="开始日期 (YYYY-MM-DD)")
    search_parser.add_argument("--to-date", help="结束日期 (YYYY-MM-DD)")
    search_parser.add_argument("--limit", "-l", type=int, default=20, help="返回数量")
    search_parser.set_defaults(func=cmd_search)
    
    # ========== aggregate 命令 ==========
    aggregate_parser = subparsers.add_parser("aggregate", help="聚合查询")
    aggregate_parser.add_argument("--by", "-b", required=True, 
                                   choices=["stock", "author", "tag", "source"],
                                   help="聚合维度 (stock/author/tag/source)")
    aggregate_parser.set_defaults(func=cmd_aggregate)
    
    # ========== stats 命令 ==========
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")
    stats_parser.add_argument("--no-tags", action="store_true", help="不显示标签云")
    stats_parser.add_argument("--no-stocks", action="store_true", help="不显示热门股票")
    stats_parser.set_defaults(func=cmd_stats)
    
    # ========== classify 命令 ==========
    classify_parser = subparsers.add_parser("classify", help="仅分类（不存储）")
    classify_parser.add_argument("--title", "-t", help="标题")
    classify_parser.add_argument("--content", help="内容")
    classify_parser.add_argument("--file", "-f", help="从文件读取")
    classify_parser.set_defaults(func=cmd_classify)
    
    # ========== fetch 命令 ==========
    fetch_parser = subparsers.add_parser("fetch", help="仅爬取（不存储）")
    fetch_parser.add_argument("url", help="要爬取的 URL")
    fetch_parser.add_argument("--full", action="store_true", help="显示完整内容")
    fetch_parser.set_defaults(func=cmd_fetch)
    
    args = parser.parse_args()
    
    if args.command:
        return args.func(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())