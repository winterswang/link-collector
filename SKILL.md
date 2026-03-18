---
name: link-collector
description: Link-Collector 知识库检索工具 - 搜索本地收藏的文章、研报、IR文件等
version: 2.0.0
author: winterswang
config:
  data_dir: /root/.openclaw/workspace/link-collector/data
triggers:
  # 搜索触发词
  - pattern: "link 搜索"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py search"
  - pattern: "link 检索"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py search"
  - pattern: "link 查找"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py search"
  - pattern: "link 找"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py search"
  
  # 按维度搜索
  - pattern: "link 股票"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py stock"
  - pattern: "link 作者"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py author"
  - pattern: "link 标签"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py tag"
  
  # 按类型搜索
  - pattern: "link 年报"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py type annual"
  - pattern: "link 季报"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py type quarterly"
  - pattern: "link 研报"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py type report"
  - pattern: "link IR文件"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py tag IR文件"
  
  # 统计和聚合
  - pattern: "link 统计"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py stats"
  - pattern: "link 状态"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py stats"
  - pattern: "link 聚合"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py aggregate"
  - pattern: "link 汇总"
    command: "python3 /root/.openclaw/workspace/link-collector/skill.py aggregate"
---

# Link-Collector Skill

知识库检索工具，支持多维度搜索本地收藏的文章、研报、IR文件。

## 使用方式

### 1. 全文搜索

```
link 搜索 {关键词}
link 检索 {关键词}
link 查找 {关键词}
link 找 {关键词}
```

示例：
- "link 搜索 PDD 估值"
- "link 检索 护城河分析"

### 2. 按股票搜索

```
link 股票 {股票代码}
```

示例：
- "link 股票 PDD"
- "link 股票 00700" (腾讯)
- "link 股票 TCEHY" (中海油)

### 3. 按作者搜索

```
link 作者 {作者名}
```

示例：
- "link 作者 czy710"
- "link 作者 林文丰"

### 4. 按标签搜索

```
link 标签 {标签名}
```

示例：
- "link 标签 护城河"
- "link 标签 估值"
- "link 标签 年报"

### 5. 按类型搜索

```
link 年报
link 季报
link 研报
link IR文件
```

### 6. 统计和聚合

```
link 统计        # 显示知识库统计
link 聚合 股票   # 按股票聚合
link 聚合 作者   # 按作者聚合
link 聚合 标签   # 按标签聚合
```

## 筛选条件（可选）

可以在搜索后追加筛选条件：

| 条件 | 示例 |
|------|------|
| `--from 日期` | "link 股票 PDD --from 2026-03-01" |
| `--to 日期` | "link 作者 czy710 --to 2026-03-15" |
| `--必读` | "link 股票 PDD --必读" |
| `--值得关注` | "link 搜索 估值 --值得关注" |

## 返回格式

```
📚 找到 X 篇文章:

1. {标题}
   来源: {作者}
   日期: {日期}
   重要性: {级别} ({分数}分)

2. ...
```

## 数据来源

| 来源 | 说明 |
|------|------|
| xueqiu-crawler | 雪球文章（每日 02:00 同步） |
| ir-crawler | IR 文件（年报、季报等） |
| 手动导入 | 用户通过 link-collector 导入 |

## Python API

```python
from link_collector import Library

lib = Library()

# 搜索
articles = lib.search(query="PDD 估值")
articles = lib.search(stock="PDD")
articles = lib.search(author="czy710")

# 聚合
stocks = lib.indexer._by_stock
tags = lib.get_tag_cloud()
```