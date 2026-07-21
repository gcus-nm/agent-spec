# 共通エージェント指示

- 指示リポジトリ: `<AGENT_SPEC_REPOSITORY_PATH>`
- タスク開始時に次を読んでください。
  1. `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/principles.md`
  2. `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/task-lifecycle.md`
  3. 作業対象プロジェクトのルートから現在地までにある `AGENTS.md`
  4. タスクに該当する `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/` の文書
- `agent-spec`自体を更新するときは、編集前に
  `<AGENT_SPEC_REPOSITORY_PATH>/docs/MAINTENANCE.md` も読んでください。
- Skillは`<AGENT_SPEC_REPOSITORY_PATH>/docs/SKILL_MANAGEMENT.md`に従って別途導入し、
  このrepo参照だけで自動導入されたと判断しないでください。
- 明示された上位指示を最優先し、同階層では対象へ近い具体的な指示を優先してください。
- 参照先を読めない場合は、欠落したファイルと影響を報告してください。
