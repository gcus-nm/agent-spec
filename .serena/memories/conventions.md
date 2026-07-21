# Conventions

- ルートAGENTSは索引とリポジトリ固有不変条件だけに保つ。
- リポジトリ更新前に `docs/MAINTENANCE.md` を読み、分類・同期・検証・引き渡し規則に従う。
- 全利用者向けは `instructions/core/`、作業別は `instructions/use-cases/`、個人嗜好は `profiles/`、ベンダー差分は `adapters/`。
- 反復可能な実行手順は `skills/<skill-name>/`、Skill横断の運用は `docs/SKILL_MANAGEMENT.md` に置く。
- Skillの`description`へ起動条件を集約し、本文と`references/`へ同じ情報を重複させない。
- Skillが同じコードを実行ごとに生成する場合は`scripts/`へ切り出し、引数・終了コード・テストを安定させる。
- 規則は適用範囲が最も狭い適切な場所に置き、全文重複を避けて正本へ参照する。
- 外部URLは根拠・更新先。作業に必須の要点はローカルにも残す。
- AGENTSを時系列日誌にせず、変更履歴は `docs/CHANGELOG.md`、意思決定は必要に応じADRへ分ける。
- 端末固有の絶対パスを正本へ保存せず、テンプレートはプレースホルダーを使う。
- 本文は日本語。コマンド、ファイル名、製品名、識別子は原表記を維持。
- Serenaメモリは密な箇条書きで安定した非自明な情報だけを記録し、参照はバッククォート内で `mem:` 接頭辞を使う。
