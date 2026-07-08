# 安装到 OpenCode / Claude Code

本仓库是一个 AI Agent Skill，可直接安装到 OpenCode 或 Claude Code 的技能目录中。

## 目录结构

克隆仓库后，你会看到：

```text
knowledge-source-scoring/
├── SKILL.md                          # 主指令文件
├── references/                       # 评分策略与来源清单
│   ├── knowledge_source_policy.yaml
│   ├── source_priority_registry.yaml
│   ├── source_scorecard_template.md
│   └── knowledge_source_workflow.md
└── scripts/
    └── download_source.py            # 独立下载与评分脚本
```

## 安装到 OpenCode

1. 克隆仓库：

   ```bash
   git clone https://github.com/aaa949714447-cmyk/knowledge-source-scoring.git
   cd knowledge-source-scoring
   ```

2. 复制到 OpenCode 技能目录（默认路径）：

   ```bash
   mkdir -p ~/.config/opencode/skills/knowledge-source-scoring
   cp SKILL.md ~/.config/opencode/skills/knowledge-source-scoring/
   cp -r references ~/.config/opencode/skills/knowledge-source-scoring/
   cp -r scripts ~/.config/opencode/skills/knowledge-source-scoring/
   ```

3. 重启 OpenCode，Skill 即可生效。

## 安装到 Claude Code

Claude Code 的 Skill 目录通常是 `~/.claude/skills/`：

```bash
mkdir -p ~/.claude/skills/knowledge-source-scoring
cp SKILL.md ~/.claude/skills/knowledge-source-scoring/
cp -r references ~/.claude/skills/knowledge-source-scoring/
cp -r scripts ~/.claude/skills/knowledge-source-scoring/
```

## 验证安装

在 OpenCode 或 Claude Code 中输入：

```text
我想研究"提示词工程中的链式思考"，请帮我找靠谱来源并整理成 Obsidian 笔记。
```

如果助手开始搜索、评分、展示候选来源并要求你确认大纲，说明安装成功。

## 独立使用脚本

不想安装 Skill，也可以单独运行评分脚本：

```bash
python3 scripts/download_source.py \
  --url "https://www.promptingguide.ai/zh/techniques/consistency" \
  --out ~/uumit-local-knowledge-base \
  --query "自我一致性提示技术是什么"
```

详见 README 中的"快速开始"。
