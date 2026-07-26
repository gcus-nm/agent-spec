# 個人用共通エージェント指示

## 共通指示の読込

- 正本: `git@github.com:gcus-nm/agent-spec.git`
- ローカルコピー: `<AGENT_SPEC_REPOSITORY_PATH>`
- タスク開始時に、次の順で必要なファイルを読んでください。
  1. `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/principles.md`
  2. `<AGENT_SPEC_REPOSITORY_PATH>/instructions/core/task-lifecycle.md`
  3. `<AGENT_SPEC_REPOSITORY_PATH>/profiles/personal/AGENTS.md`
  4. 作業対象プロジェクトのルートから現在地までにある `AGENTS.md`
  5. `<AGENT_SPEC_REPOSITORY_PATH>/instructions/use-cases/README.md`で選んだ
     タスク該当文書
- `agent-spec`リポジトリ自体を更新する場合は、編集前に
  `<AGENT_SPEC_REPOSITORY_PATH>/docs/MAINTENANCE.md` も読んでください。

## 優先順位

- システム、開発者、ユーザーの明示指示を最優先します。
- 次に、作業対象へ近いプロジェクト固有の指示を優先します。
- 個人プロファイルは、プロジェクト固有の指示と矛盾しない範囲で適用します。
- 読み込めない参照先がある場合は、欠落したファイルと影響範囲を報告してください。

## 更新

- 共通ルールをこのファイルへ複製せず、`agent-spec`側の正本を更新してください。
- Skillはルート指示とは別に、
  `<AGENT_SPEC_REPOSITORY_PATH>/docs/SKILL_MANAGEMENT.md`に従って導入してください。
  このファイルからrepoを参照するだけで自動導入されたと判断しないでください。
- `git pull`など外部状態を変更する操作は、権限と作業範囲を確認してから行ってください。

<!-- コピー後、<AGENT_SPEC_REPOSITORY_PATH> を実際の絶対パスへ置換してください。 -->
