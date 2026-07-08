# 示例说明

这个目录展示 `knowledge-source-scoring` 从“网页来源”到“知识笔记”的完整效果。

## 文件说明

| 文件 | 作用 |
|---|---|
| `scorecard-example.json` | `scripts/download_source.py` 对单个网页做首轮下载、提取、评分后的 JSON 输出 |
| `obsidian-note-example.md` | Agent 基于可信来源整理后的 Obsidian Markdown 笔记示例 |

## 怎么理解这些示例

`scorecard-example.json` 是脚本输出，不等于最终知识结论。它负责回答：

- 这个网页标题是什么？
- 来源类型是什么？
- 当前规则给它多少分？
- 它是 A/B/C/D 哪个等级？
- 有哪些风险或需要人工复核的地方？

`obsidian-note-example.md` 是最终笔记效果，展示一篇面向新手的知识点笔记应该包含：

- 一句话解释
- 背景和用途
- 核心术语拆解
- 工作方式
- 好例子和坏例子
- 常见误区
- 学习路线
- 来源表

## 注意

示例中的 `Prompt Engineering Guide` 被评为 C 级，是刻意保留的真实结果：它适合作为线索或辅助例子，但不能单独作为正式知识库主来源。

正式生成笔记前，应该继续补充 A/B 级来源，并对关键结论做交叉验证。
