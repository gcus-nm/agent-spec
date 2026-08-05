# 個人用共通エージェント指示

- 指示リポジトリ: `<AGENT_SPEC_REPOSITORY_PATH>`
- 日本語で応答してください。
- ユーザーがコピーして実行するコマンドは、1コマンドにつき1行で提示してください。
- 作業対象のルートから現在地までにある `AGENTS.md` を適用してください。
- 説明、調査、診断、計画、レビューでは、明示されない限りファイルを変更しないでください。
- 実装や修正では必要最小限を変更し、無関係な既存差分を保持して、関連する非破壊的な検証を
  行ってください。
- 破壊的操作、外部への書込、購入、高コスト操作、大幅なスコープ拡張は事前に確認してください。
- 将来も有効なプロジェクト固有の規則・判断や、利用者に影響する変更履歴は、作業内容が新鮮な
  うちに適切な永続記録へ作成・更新してください。
- 完了前に、正確性、スコープ、検証結果、意図しない変更を短く確認してください。
- 最終報告は、結果、主要変更、検証、残課題を簡潔に示してください。

## 条件付きガイド

- 大規模、曖昧、高リスク、横断的な変更、複雑な診断、明示的な計画作成:
  `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/task-lifecycle.md`
- 外部根拠の精査を含む高リスク作業:
  `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/principles.md`
- コードレビュー: `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/code-review.md`
- 複雑な原因調査: `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/research.md`
- 大規模なコード変更: `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/code-change.md`
- `AGENTS.md`や指示設計の編集:
  `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/instruction-authoring.md`
- `agent-spec`の更新: `<AGENT_SPEC_REPOSITORY_PATH>/docs/MAINTENANCE.md`
- Skillの作成、変更、導入: `<AGENT_SPEC_REPOSITORY_PATH>/docs/SKILL_MANAGEMENT.md`
- UnityまたはC#作業: `<AGENT_SPEC_REPOSITORY_PATH>/profiles/personal/unity-csharp.md`
- バックエンドを伴うWebサービスの新規作成:
  `<AGENT_SPEC_REPOSITORY_PATH>/profiles/personal/web-development.md`
- 永続性のある規則・判断・変更履歴が生じる作業:
  `<AGENT_SPEC_REPOSITORY_PATH>/profiles/personal/project-recording.md`
- Unity操作・検証、外部SDK調査、Web UI操作、GitHub上の作業でツール選択が必要な場合、
  または明示的な音声通知:
  `<AGENT_SPEC_REPOSITORY_PATH>/profiles/personal/mcp-and-voicevox.md`
- 製品固有の導入、認証、権限、サンドボックス、ツール検出問題:
  `<AGENT_SPEC_REPOSITORY_PATH>/adapters/README.md`
- 上記に直接一致しない特殊作業だけ:
  `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/README.md`
- 明確に一致する反復ワークフロー: 対応する導入済みSkill

タスクに無関係な指示文書を読まないでください。参照先を読めない場合は、欠落したファイルと
影響を報告してください。`git pull`など外部状態を変更する操作は、権限と作業範囲を確認して
から行ってください。
