# OpenAI Codex

- 個人の既定値: Codexホーム（通常 `~/.codex`）の `AGENTS.md`
- 一時的なグローバル上書き: `AGENTS.override.md`
- チーム共有: リポジトリルートの `AGENTS.md`
- 局所規則: 対象へ近いディレクトリの `AGENTS.md` または `AGENTS.override.md`
- 読込順: グローバルの後、プロジェクトルートから現在地へ向かって連結され、近い指示が優先
- 既定の結合上限: 32KiB。重要な指示を短く保ち、詳細は明示的に読む別文書へ分割
- repo向けSkill: 対象repoの `.agents/skills/<skill-name>`
- ユーザー向けSkill: `$HOME/.agents/skills/<skill-name>`
- Skillは明示的な`$<skill-name>`または`description`との一致で起動し、同名Skillは統合されない

個人設定付きの入口にはルート `ROOT_AGENTS_TEMPLATE.md`、汎用のみなら
`templates/ROOT_AGENTS_GENERIC.md` を利用します。

導入後は新しいセッションで「現在読み込まれている指示元と優先順を要約して」と依頼し、
想定したファイルが有効か確認します。

このリポジトリで管理するSkillの導入・同期は`docs/SKILL_MANAGEMENT.md`に従います。

公式: [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Skill公式: [Build skills](https://learn.chatgpt.com/docs/build-skills)
