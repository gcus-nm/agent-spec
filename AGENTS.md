# agent-spec リポジトリ指示

このリポジトリは、複数のAIコーディングエージェントで再利用できる指示、個人プロファイル、
ユースケース別ガイド、導入テンプレートを管理します。

## 作業前に読むファイル

- 常時: `instructions/core/principles.md`
- 変更を伴うタスク: `instructions/core/task-lifecycle.md`
- このリポジトリを更新するタスク: `docs/MAINTENANCE.md`
- 指示ファイルの設計・編集: `instructions/core/instruction-authoring.md`
- Skillの追加・変更・導入: `docs/SKILL_MANAGEMENT.md` と対象の `SKILL.md`
- 個人設定の変更: 対象となる `profiles/<name>/AGENTS.md`
- 外部仕様を根拠にする変更: `docs/OFFICIAL_GUIDANCE.md`

タスクに関係しないプロファイルやユースケース文書は読み込まないでください。

## リポジトリ保守ルール

- ルート `AGENTS.md` は索引と、このリポジトリ固有の不変条件だけに保ちます。
- 全利用者に適用できる規則は `instructions/core/` に置きます。
- 特定の作業だけに適用する手順は `instructions/use-cases/` に置きます。
- 個人の言語、通知、ツール、コーディング嗜好は `profiles/<name>/` に置きます。
- ベンダー固有の自動読込形式は `adapters/`、導入用のコピー元は `templates/` に置きます。
- 再利用する実行手順は `skills/<skill-name>/` に置き、Skill横断の運用は
  `docs/SKILL_MANAGEMENT.md` を正本にします。
- 重要ルールは外部URLだけに依存させず、リポジトリ内へ簡潔に記録します。URLは根拠・
  更新確認先として `docs/OFFICIAL_GUIDANCE.md` にまとめます。
- 同じ規則を複数ファイルへ複製せず、正本への明示的な参照を使います。
- 秘密情報、資格情報、個別プロジェクトの長大な作業履歴を保存しません。
- 更新時の同期対象、検証、Git運用は `docs/MAINTENANCE.md` に従います。

## 完了条件

- Markdownリンクと参照パスが存在することを確認します。
- 個人ルールが汎用コアへ混入していないことを確認します。
- `git diff --check` 相当の末尾空白・競合マーカー確認を行います。
- Serenaメモリを変更した場合は `mem:` 参照の整合性を確認します。
- Skillを変更した場合は `python scripts/validate_skills.py` を実行します。
- 最終的に `python scripts/validate_repository.py` を実行します。
- 変更内容と、参照したMCP・公式資料・検証結果を日本語で報告します。

## 作業記録

作業履歴の正本は `docs/CHANGELOG.md` です。AGENTS.mdへ時系列ログを追記しません。
