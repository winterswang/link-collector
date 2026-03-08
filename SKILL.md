---
name: link-collector
description: 链接内容记录与分类工具。当用户提供链接时，自动提取内容、智能分类、生成摘要并归档。
version: 1.0.0
author: winterswang
triggers:
  - pattern: "记录链接 {url}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {url}"
  - pattern: "收藏 {url}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {url}"
  - pattern: "保存链接 {url}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {url}"
---

# 链接内容记录与分类工具

自动提取网页内容，智能分类并归档。

## 功能

| 功能 | 说明 |
|------|------|
| 内容提取 | 百炼 GLM-5 联网搜索 |
| 智能分类 | 5 类：tech/investment/life/reading/tools |
| 标签生成 | 自动提取关键词 |
| 摘要生成 | 一句话总结 |
| 归档存储 | 保存到 ideas-and-notes/inbox/ |

## 使用方式

- `记录链接 https://example.com`
- `收藏 https://xueqiu.com/xxx`
- `保存链接 https://...`

## 输出示例

```markdown
# 文章标题

## 元数据

| 属性 | 值 |
|------|------|
| **来源** | [URL](URL) |
| **分类** | investment |
| **重要性** | 值得关注 |
| **标签** | 美股, AI投资 |
| **采集时间** | 2026-03-08 22:26 |

## 摘要

一句话摘要...

## 要点

- 要点1
- 要点2
- 要点3

## 原文内容

...
```

## 技术栈

- 百炼 GLM-5（联网搜索 + 智能分析）
- Markdown 存储
- 5 分钟超时配置

## GitHub

https://github.com/winterswang/link-collector