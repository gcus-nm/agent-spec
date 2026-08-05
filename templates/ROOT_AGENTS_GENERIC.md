# 共通エージェント指示

- 指示リポジトリ: `<AGENT_SPEC_REPOSITORY_PATH>`
- 作業対象のルートから現在地までにある `AGENTS.md` を適用してください。
- 読取依頼では明示されない限り変更せず、変更依頼では必要最小限を変更して関連する
  非破壊的な検証を行ってください。
- 無関係な既存差分を保持し、破壊的操作、外部への書込、高コスト操作、大幅なスコープ拡張は
  事前に確認してください。
- 完了前に、正確性、スコープ、検証結果、意図しない変更を短く確認してください。

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
- 製品固有の導入、認証、権限、サンドボックス、ツール検出問題:
  `<AGENT_SPEC_REPOSITORY_PATH>/adapters/README.md`
- 上記に直接一致しない特殊作業だけ:
  `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/README.md`
- 明確に一致する反復ワークフロー: 対応する導入済みSkill

タスクに無関係な指示文書を読まないでください。参照先を読めない場合は、欠落したファイルと
影響を報告してください。
