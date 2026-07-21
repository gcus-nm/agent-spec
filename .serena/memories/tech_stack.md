# Tech Stack

- UTF-8 Markdown中心のドキュメントリポジトリ。
- オープン形式: `AGENTS.md`。汎用正本は `instructions/`。
- Skill形式: `skills/<skill-name>/SKILL.md`。Skill構造は `scripts/validate_skills.py`、repo全体は `scripts/validate_repository.py` で検証。
- 対応アダプター: OpenAI Codex、GitHub Copilot、Gemini CLI。
- 長期メモリ: Serena `.serena/memories/*.md`。Serenaプロジェクト言語は `markdown`。
- 外部一次資料: OpenAI Codex公式マニュアル、OpenAI Skills、Agent Skills specification、agents.md、GitHub Docs、Gemini CLI Docs。
- リモート: `git@github.com:gcus-nm/agent-spec.git`。
