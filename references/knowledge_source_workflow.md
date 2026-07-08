# 知识来源评分与本地下载流程

## 目标

把“搜索知识库资料”拆成可复核步骤：搜索、下载、提取证据、评分、交叉验证、入库候选、人工审核。

## 步骤

1. 把主题改写成 1 到 3 个可搜索问题。
2. 优先搜索官方文档、论文、标准、大学课程和知名技术参考。
3. 下载候选来源正文、元数据和图片清单。
4. 按 `knowledge_source_policy.yaml` 打分。
5. 每个知识点至少使用 2 个独立来源交叉验证。
6. A/B 级进入正式候选，C 级进入人工审核，D 级拒绝。
7. 来源冲突时输出冲突说明，不自动入库。

## 图片与多模态

下载网页时应保存图片清单，但不默认识别图片。

只有当图片承载关键知识且文字无法替代时，才允许使用 OCR 或多模态模型。每张图片必须说明：为什么需要识别、识别什么、使用什么模型、置信度是多少。

默认不识别：logo、头像、装饰图、广告图、社交分享图、追踪像素、含隐私或凭证的截图。

## 本地知识库目录建议

```text
~/knowledge-source-scoring-workspace/
├── sources/      # 原始 HTML、文本、图片清单、metadata
├── articles/     # 整理后的 Markdown
├── candidates/   # C 级候选素材
├── rejected/     # D 级或冲突材料
└── reviews/      # 评分表和人工审核记录
```

## 入库元数据

```yaml
title: ""
source_url: ""
source_type: ""
source_score: 0
source_level: "A | B | C | D"
collected_at: "YYYY-MM-DDTHH:MM:SSZ"
review_status: "auto_accepted | needs_review | rejected"
risk_notes: ""
image_inventory: []
multimodal_used: false
```
