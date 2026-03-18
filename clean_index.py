#!/usr/bin/env python3
"""
Link-Collector 索引清理脚本

清理重复文章，重建索引
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加包路径
sys.path.insert(0, str(Path(__file__).parent))

from link_collector import Library


def clean_duplicates():
    """清理重复文章"""
    lib = Library()
    
    print("🔍 分析索引...\n")
    
    # 收集所有文章
    all_articles = {}  # id -> article
    
    # 从股票索引收集
    for stock, data in lib.indexer._by_stock.items():
        for article in data.get('articles', []):
            aid = article.get('id')
            if aid and aid not in all_articles:
                all_articles[aid] = article
    
    # 从作者索引收集
    for author, data in lib.indexer._by_author.items():
        for article in data.get('articles', []):
            aid = article.get('id')
            if aid and aid not in all_articles:
                all_articles[aid] = article
    
    print(f"发现唯一文章: {len(all_articles)} 篇\n")
    
    # 按标题+来源去重
    seen = {}  # (title, source) -> id
    duplicates = []
    
    for aid, article in all_articles.items():
        title = article.get('title', '')
        source = article.get('source', '')
        key = (title, source)
        
        if key in seen:
            duplicates.append((aid, title[:50]))
        else:
            seen[key] = aid
    
    print(f"发现重复文章: {len(duplicates)} 篇\n")
    
    if duplicates:
        print("重复文章列表:")
        for aid, title in duplicates[:10]:
            print(f"  - {title}... (ID: {aid[:8]}...)")
        
        if len(duplicates) > 10:
            print(f"  ... 还有 {len(duplicates) - 10} 篇")
    
    return len(all_articles), len(duplicates)


def rebuild_index():
    """重建索引"""
    print("\n🔨 重建索引...\n")
    
    lib = Library()
    
    # 清空现有索引
    lib.indexer._by_stock = {}
    lib.indexer._by_author = {}
    lib.indexer._by_tag = {}
    lib.indexer._by_source = {}
    
    # 遍历所有 JSON 文件
    inbox_dir = lib.inbox_dir
    
    seen = set()  # (title, source) 用于去重
    added = 0
    skipped = 0
    
    for date_dir in inbox_dir.iterdir():
        if not date_dir.is_dir():
            continue
        
        for json_file in date_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                title = data.get('title', '')
                source_data = data.get('source', {})
                author = source_data.get('author', '') or source_data.get('publisher', '')
                
                # 去重检查
                key = (title, author)
                if key in seen:
                    skipped += 1
                    continue
                
                seen.add(key)
                
                # 构建文章元数据
                source_data = data.get('source', {})
                
                # 如果没有作者，尝试从文件名或 URL 提取
                author = source_data.get('author') or source_data.get('publisher')
                if not author:
                    # 从 URL 或文件名提取公司名称
                    url = source_data.get('url', '')
                    if 'Tencent' in url or 'Tencent' in title:
                        author = 'Tencent Holdings Limited'
                    elif 'downloads/' in url:
                        # 从 downloads/Company/Type/ 提取公司名
                        import re
                        match = re.search(r'downloads/([^/]+)/', url)
                        if match:
                            author = match.group(1)
                
                if author and not source_data.get('author'):
                    source_data['author'] = author
                
                article_meta = {
                    'id': data.get('id'),
                    'title': title,
                    'source': source_data,
                    'classification': data.get('classification', {}),
                    'importance': data.get('importance', {}),
                    'content': data.get('content', {}),
                    'timestamps': data.get('timestamps', {}),
                    'relations': data.get('relations', {}),
                    'raw_file': str(json_file).replace('.json', '.md')
                }
                
                # 获取对应的 MD 文件路径
                md_file = json_file.with_suffix('.md')
                article_path = str(md_file) if md_file.exists() else article_meta['raw_file']
                
                # 添加到索引
                lib.indexer.add_article(article_meta, article_path)
                added += 1
                
            except Exception as e:
                print(f"  ⚠️ 处理失败: {json_file.name} - {e}")
    
    # 保存索引
    lib.indexer._save_all()
    
    print(f"✅ 已添加: {added} 篇")
    print(f"⏭️ 已跳过: {skipped} 篇（重复）")
    
    return added, skipped


def main():
    print("=" * 50)
    print("Link-Collector 索引清理工具")
    print("=" * 50)
    print()
    
    # 1. 分析
    unique, duplicates = clean_duplicates()
    
    # 2. 重建
    added, skipped = rebuild_index()
    
    # 3. 统计
    print("\n" + "=" * 50)
    print("📊 清理结果:")
    print(f"  唯一文章: {unique} 篇")
    print(f"  重复文章: {duplicates} 篇")
    print(f"  实际添加: {added} 篇")
    print("=" * 50)


if __name__ == '__main__':
    main()