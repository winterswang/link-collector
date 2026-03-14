---
name: link-collector
description: 链接内容记录与分类工具。支持网页、PDF、Excel文件的自动提取、智能分类和归档。
version: 1.2.0
author: winterswang
config:
  data_dir: ./data
  inbox_dir: ./data/inbox
  archive_dir: ./data/archive
triggers:
  - pattern: "记录链接 {url}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {url}"
  - pattern: "收藏 {url}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {url}"
  - pattern: "保存链接 {url}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {url}"
  - pattern: "记录文件 {path}"
    command: "python3 /root/.openclaw/workspace/link-collector/collector.py {path}"
---

# 链接内容记录与分类工具 V1.2

自动提取网页、PDF、Excel内容，智能分类并归档。

## 🆕 V1.2 更新

| 功能 | 说明 |
|------|------|
| **配置文件** | 支持 config.yaml 配置 |
| **数据本地化** | 数据存储在项目 data/ 目录 |
| **路径可配置** | inbox/archive 路径可自定义 |

## 项目结构

```
link-collector/
├── collector.py           # 主程序
├── SKILL.md               # Skill 定义
├── config.yaml            # 配置文件
├── data/                  # 数据目录
│   ├── inbox/             # 收件箱
│   │   └── 2026-03-15/    # 按日期组织
│   ├── archive/           # 归档
│   └── exports/           # 导出
├── cookies/               # 登录凭证
└── logs/                  # 日志
```

## 数据存储

| 类型 | 位置 | 说明 |
|------|------|------|
| **原始数据** | `data/inbox/{日期}/*_raw.md` | 未经处理的原始提取内容 |
| **加工数据** | `data/inbox/{日期}/{标题}.md` | LLM 处理后的结构化内容 |

## 支持格式

| 类型 | 图标 | 格式 | 提取方式 |
|------|------|------|----------|
| **网页** | 🌐 | URL | Playwright + 百炼联网 |
| **PDF** | 📄 | .pdf | pdfplumber / PyPDF2 |
| **Excel** | 📊 | .xlsx, .xls | pandas / openpyxl |
| **文本** | 📝 | .md, .txt | 直接读取 |

## 使用方式

### 网页链接

```
记录链接 https://example.com/article
收藏 https://xueqiu.com/xxx
保存链接 https://...
```

### 本地文件

```
记录文件 ~/Downloads/report.pdf
收藏 ./data.xlsx
保存链接 /path/to/file.md
```

## 输出示例

### 网页

```markdown
# 文章标题

## 元数据

| 属性 | 值 |
|------|------|
| **来源** | 🌐 [URL](URL) |
| **类型** | WEB |
| **分类** | investment |
| **重要性** | 值得关注 |
| **标签** | 美股, AI投资 |
| **采集时间** | 2026-03-11 23:20 |

## 摘要
一句话摘要...

## 要点
- 要点1
- 要点2
- 要点3

## 内容预览
...

---
*由 link-collector V1.1 自动采集*
```

### PDF

```markdown
# Report Title

## 元数据

| 属性 | 值 |
|------|------|
| **来源** | 📄 [file:///path/to/report.pdf](file:///path/to/report.pdf) |
| **类型** | PDF |
| **分类** | reading |
| **重要性** | 必读 |
| **标签** | 报告, 分析 |
| **采集时间** | 2026-03-11 23:20 |

## 摘要
PDF内容摘要...

## 要点
- 要点1
- 要点2

## 内容预览
--- 第1页 ---
PDF文本内容...

---
*由 link-collector V1.1 自动采集*
```

### Excel

```markdown
# Sales Data

## 元数据

| 属性 | 值 |
|------|------|
| **来源** | 📊 [file:///path/to/data.xlsx](file:///path/to/data.xlsx) |
| **类型** | EXCEL |
| **分类** | tools |
| **重要性** | 值得关注 |
| **标签** | 数据, 表格 |
| **采集时间** | 2026-03-11 23:20 |

## 摘要
Excel数据摘要...

## 要点
- 工作表数: 3
- 行数: 1000
- 列名: 日期, 销售额, 利润

## 内容预览
## 文件: data.xlsx
## 工作表: Sheet1, Sheet2, Sheet3

### 工作表: Sheet1
行数: 1000, 列数: 10
列名: 日期, 销售额, 利润, ...

数据预览:
| 日期 | 销售额 | 利润 |
|------|--------|------|
| 2026-01-01 | 10000 | 2000 |
...

---
*由 link-collector V1.1 自动采集*
```

## 技术栈

| 组件 | 技术 |
|------|------|
| LLM | 百炼 GLM-5（联网搜索 + 智能分析） |
| 网页爬取 | Playwright |
| PDF提取 | pdfplumber / PyPDF2 |
| Excel提取 | pandas / openpyxl |
| 存储 | Markdown |
| 超时 | 5 分钟 |

## 分类体系

| 分类 | 说明 |
|------|------|
| **tech** | 技术相关（编程、架构、工具） |
| **investment** | 投资理财（股票、基金、经济） |
| **life** | 生活日常（健康、旅行、美食） |
| **reading** | 阅读笔记（书籍、文章、思考） |
| **tools** | 工具资源（软件、服务、资源） |

## 依赖安装

```bash
# PDF 支持
pip install pdfplumber PyPDF2

# Excel 支持
pip install pandas openpyxl

# 网页爬取
pip install playwright
playwright install chromium
```

## GitHub

https://github.com/winterswang/link-collector

---
*版本: V1.1.0 | 更新: 2026-03-11*