---
name: knowledge-source-scoring
description: Use when researching web knowledge, scoring sources, and writing beginner-friendly single-file Obsidian knowledge notes under AI_Knowledge_Base topic folders.
---

# Knowledge Source Scoring And Beginner Knowledge Notes

Use this skill when the user wants to research a topic, process a URL, score source reliability, and write a beginner-friendly knowledge note into the local Obsidian `AI_Knowledge_Base` vault.

The goal is not to scrape pages or create audit folders. The goal is a small, readable knowledge base:

1. Discover or accept source URLs.
2. Score and filter sources.
3. Show candidate sources, rejected sources, risks, and an outline before writing.
4. After user confirmation, write one deep tutorial-style Markdown note per knowledge point.
5. Put source title, URL, score, level, and trust reason at the bottom of that same note.

When choosing sources, first consult `references/source_priority_registry.yaml`. Prefer official/free knowledge sources before blogs, forums, aggregators, or course sales pages.

## Hard Rules

1. Do not treat model memory as a source.
2. Do not ingest knowledge without URL, title, evidence excerpt, retrieval time, score, and level.
3. Score every source with `references/knowledge_source_policy.yaml`.
4. A/B level sources may be used as primary/supporting evidence.
5. C level sources are examples or leads only. Do not treat C as primary evidence.
6. D level sources are rejected unless the user explicitly asks to mention them.
7. Each durable knowledge point normally needs at least 2 independent sources. A single official source may support a factual product/API note, but mark the note `confidence: medium` or `low` until cross-validated.
8. If sources conflict, do not auto-ingest. Show the conflict and ask for review.
9. Do not write final Obsidian notes before showing candidate sources and a proposed outline, unless the user explicitly says to skip review.
10. Do not create separate Obsidian source notes, review folders, or attachment directories. Source summaries live at the bottom of the knowledge note.

## Beginner Writing Rules

The knowledge base is for beginners. Do not write compressed expert notes.

- Write in Chinese, preserve important English terms in parentheses or inline code.
- Explain the idea first in plain language, then introduce the technical term.
- Use analogies, step-by-step explanations, concrete examples, common mistakes, and small exercises.
- Assume the reader is smart but unfamiliar with the topic.
- Target length for a normal knowledge point: 3000-6000 Chinese characters unless the user asks for a short note.
- Prefer tutorial style over encyclopedia style.
- Add a learning-path section: what to learn before this note, and what to learn next.

## Multimodal And Image Rules

Images are common in downloaded knowledge pages, but do not send every image to a multimodal model by default.

Use this decision order:

1. Prefer page text, captions, alt text, surrounding paragraphs, and linked source files.
2. Use multimodal/OCR only when an image contains essential knowledge unavailable as text.
3. Never OCR decorative images, logos, avatars, banners, ads, social share images, tracking pixels, or unrelated screenshots.
4. Before using a costly or external multimodal model, state which images need analysis and why.
5. If the image may contain private data, credentials, faces, screenshots of internal systems, or user-uploaded content, ask before sending it to any external model.
6. For diagrams, charts, tables, formulas, screenshots of code, and workflow images, extract only evidence relevant to the current knowledge point.
7. Every OCR or image interpretation must keep `image_url`, `image_alt`, `image_context`, `model_used`, `reason_for_multimodal`, and `confidence` in the chat/research record, not as separate Obsidian files.
8. Do not infer facts from ambiguous visual evidence. Mark as `needs_review`.
9. Limit multimodal calls to the smallest useful set. Default maximum: 5 images per source unless the user approves more.

## Helper Script

For a quick source scoring pass, use:

```bash
python3 ~/.config/opencode/skills/knowledge-source-scoring/scripts/download_source.py \
  --url "https://www.promptingguide.ai/zh/techniques/consistency" \
  --out ~/uumit-local-knowledge-base \
  --query "自我一致性提示技术是什么，以及适合解决什么问题"
```

The helper downloads HTML, extracts clean text, lists images, extracts metadata, applies a conservative rule-based score, and prints a JSON result. It does not call any LLM, OCR, or multimodal model. It also does not write source/review artifacts into Obsidian.

Proxy behavior:

- By default, the helper uses `HTTPS_PROXY`, `https_proxy`, `HTTP_PROXY`, or `http_proxy` from the environment.
- `NO_PROXY` / `no_proxy` is respected, so internal hosts can bypass the proxy.
- Use `--proxy "http://172.26.16.1:8902"` to force a proxy for one run.
- Use `--no-proxy` to disable proxy use for one run.
- Proxy use is only for web source downloading. It does not affect model API routing outside this script.

Local staging is only for temporary research evidence:

```text
~/uumit-local-knowledge-base/
└── sources/<slug>/
    ├── raw.html
    ├── metadata.json
    ├── text.txt
    └── images.json
```

## Obsidian Layout

Default vault path:

```text
/mnt/c/Users/luyj/wiki-vault/raw/obsidian
```

Knowledge base root:

```text
AI_Knowledge_Base/
├── README.md
├── 提示词工程/
│   └── 目录.md
├── 大模型基础/
│   └── 目录.md
├── RAG知识/
│   └── 目录.md
└── Agent知识/
    └── 目录.md
```

Rules:

- One knowledge point = one `.md` file.
- Put each note under the best matching Chinese topic folder.
- Do not create `Inbox`, `Reviewed`, `Sources`, `Candidates`, `Rejected`, or `reviews` inside Obsidian by default.
- Use `README.md` at the root to explain the knowledge-base project, architecture, workflow, and maintenance rules.
- Use each topic folder's `目录.md` as a beginner learning map.

## Research Workflow

1. Convert the user topic into 1-3 search questions.
2. Support two modes: automatic web research by topic, and user-provided URL processing.
3. Check `references/source_priority_registry.yaml` and try priority sources first: official product docs, official research/model pages, papers/preprints, standards/specs, university/open courses, reputable open references, and official project docs.
4. Download or read candidate sources.
5. If an overseas priority source fails with 403, timeout, DNS/TLS error, region restriction, or empty content and the fetch did not use a proxy, stop and ask the user to enable VPN/proxy before falling back. If proxy was used and it still fails, record the source as rejected with the concrete error and continue.
6. Prefer official docs, papers/preprints, standards, university material, and reputable technical references. Use blogs/forums only as supporting examples.
7. Extract claims, evidence excerpts, metadata, image inventory, and source text.
8. Score each source with the policy. The helper can create a first-pass score, but the agent must still review it before treating the source as accepted.
9. Reject D sources and do not use them in synthesis unless explicitly requested.
10. Cross-validate claims across independent A/B sources. Use C sources only as leads or examples.
11. Present the user with candidate sources, rejected sources, risks, and a proposed beginner-friendly outline in chat.
12. Wait for user confirmation before writing the final Obsidian note, unless the user explicitly permits automatic writing.
13. Write the final note into the relevant topic folder and include source summaries at the bottom of the same file.

## Confirmation Output Before Writing

Before writing a final Obsidian note, show:

```yaml
topic: ""
proposed_title: ""
target_folder: "AI_Knowledge_Base/<中文主题文件夹>"
candidate_sources:
  - title: ""
    url: ""
    level: "A | B | C"
    score: 0
    role: "primary | supporting | example_only"
    key_evidence: ""
    trust_reason: ""
rejected_sources:
  - title: ""
    url: ""
    reason: ""
cross_validation:
  matched_claims: []
  conflicts: []
proposed_outline:
  - "这是什么：先用人话解释"
  - "为什么需要它：问题背景"
  - "核心概念：术语拆解"
  - "它怎么工作：一步一步讲"
  - "怎么实际使用：操作方法"
  - "例子：好例子和坏例子"
  - "常见误区：小白容易踩的坑"
  - "学习路线：先学什么，后学什么"
  - "来源：URL、评分、可信理由"
```

## Knowledge Note Template

Use this structure for final notes. Keep it beginner-friendly and tutorial-like.

```markdown
---
title: ""
tags:
  - ai/wiki
  - status/draft
status: draft | reviewed | evergreen
confidence: high | medium | low
updated: YYYY-MM-DD
---

# Title

## 先用一句话说清楚

## 为什么需要这个概念

## 核心概念拆解

Explain key English terms here.

## 它是怎么工作的

Use steps, analogies, and examples.

## 怎么实际使用

## 好例子和坏例子

## 常见误区

## 先学什么，后学什么

Use Obsidian links like [[Chain-of-Thought]] or [[RAG]] when useful.

## 小练习

## 来源

| 来源 | URL | 分数 | 等级 | 为什么可信 / 风险 |
|---|---|---:|---|---|
|  |  |  |  |  |
```

## Topic Folder Defaults

- Prompting, prompts, Chain-of-Thought, Self-Consistency, Structured Output: `提示词工程/`
- LLM basics, Transformer, tokens, context window, attention: `大模型基础/`
- Embedding, vector database, chunking, retrieval, reranking: `RAG知识/`
- Tool use, planning, memory, ReAct, multi-agent: `Agent知识/`

If no folder fits, ask the user whether to create a new Chinese topic folder.

## Output Contract

Always include source data in chat before writing:

```yaml
query: ""
retrieved_at: "YYYY-MM-DD"
sources:
  - source_url: ""
    source_title: ""
    source_type: ""
    source_score: 0
    source_level: "A | B | C | D"
    scoring_breakdown:
      authority: 0
      traceability: 0
      technical_depth: 0
      freshness: 0
      cross_validation: 0
      bias_penalty: 0
    evidence_excerpt: ""
    review_status: "auto_accepted | needs_review | rejected"
    trust_reason: ""
    risk_notes: ""
```

## References

- `references/knowledge_source_policy.yaml`
- `references/source_priority_registry.yaml`
- `references/source_scorecard_template.md`
- `scripts/download_source.py`
