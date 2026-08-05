# agent-spec リポジトリ指示

このリポジトリは、複数のAIコーディングエージェントで再利用する指示、プロファイル、
アダプター、テンプレート、Skillを管理します。

## 不変条件

- ルート `AGENTS.md` は短い索引とリポジトリ固有の不変条件だけに保ちます。
- 全利用者向け原則は `instructions/core/`、特定作業は `instructions/use-cases/`、個人設定は
  `profiles/`、製品差分は `adapters/`、コピー用成果物は `templates/`、反復手順は `skills/`
  へ置きます。
- 同じ規則を複数ファイルへ複製せず、正本への明示的な参照を使います。
- 秘密情報、資格情報、端末固有パス、個別プロジェクトの長大な履歴を保存しません。
- 作業履歴の正本は `docs/CHANGELOG.md` です。AGENTS.mdへ時系列ログを追記しません。

## 条件付きで読む

- このリポジトリを更新する: `docs/MAINTENANCE.md`
- `AGENTS.md`や指示文書を設計・編集する: `instructions/core/instruction-authoring.md`
- Skillを追加・変更・導入する: `docs/SKILL_MANAGEMENT.md` と対象の `SKILL.md`
- 外部仕様を根拠に変更する: `docs/OFFICIAL_GUIDANCE.md`
- 大規模、曖昧、高リスク、横断的な変更や複雑な診断: `instructions/core/task-lifecycle.md`
- 上記に直接一致しない特殊作業: `instructions/use-cases/README.md`

タスクに関係しないプロファイル、ユースケース、詳細原則を読まないでください。

## 完了条件

- Markdownリンクと参照パス、責務の境界、意図しない差分を確認します。
- Skill変更時は `python scripts/validate_skills.py` を実行します。
- `git diff --check` と `python scripts/validate_repository.py` を実行します。
- 変更内容、参照したMCP・公式資料、検証結果を日本語で報告します。
