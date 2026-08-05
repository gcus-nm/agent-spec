# Core

- ルート `AGENTS.md` はこのリポジトリ自身の短いルーター。全利用者向け原則は `instructions/core/`。
- このリポジトリを更新するときの正本手順は `docs/MAINTENANCE.md`。別環境からの更新も同じ手順を適用。
- 通常タスクは短い環境ルートとプロジェクトAGENTSだけを常時適用し、詳細原則、プロファイル、ユースケース、Skillは明示条件に一致した場合だけ読む。
- 頻出タスクは環境ルートから詳細文書へ直接ルーティングし、`instructions/use-cases/README.md`は直接ルートがない特殊作業のフォールバック索引にする。
- 製品固有の導入・設定・挙動確認と、実行環境固有の認証・権限・サンドボックス・検出問題は、環境ルートから該当`adapters/`文書へ直接ルーティングする。
- Skill横断の作成・導入・検証・配布ルールは `docs/SKILL_MANAGEMENT.md`。管理Skill索引は `skills/README.md`。
- ルートAGENTSによるrepo参照とSkill導入は別工程。Skillは`scripts/install_skills.py`でCodexの探索先へ明示的に同期する。
- 新環境の初回導入は`scripts/setup_environment.py`でルートAGENTS生成、Skill導入、検証を一括実行できる。
- 仕様文書更新は `$maintain-agent-spec`、新環境の導入確認は `$verify-agent-spec-setup`。
- 個人設定の常時最小集合は`ROOT_AGENTS_TEMPLATE.md`へ直接置き、`profiles/personal/AGENTS.md`は旧環境の互換用入口、技術・ツール・通知の詳細は条件付き文書とする。
- 導入と構造は `README.md` と `docs/INSTRUCTION_ARCHITECTURE.md`。
- 公式根拠と確認日は `docs/OFFICIAL_GUIDANCE.md`、取り込み元は `docs/SOURCE_INVENTORY.md`、変更履歴は `docs/CHANGELOG.md`。
- 編集規約は `mem:conventions`、技術構成は `mem:tech_stack`、運用コマンドは `mem:suggested_commands`、完了条件は `mem:task_completion`。
- Serenaメモリの構造・更新基準は `mem:memory_maintenance`。
- 共通規約、個人設定、プロジェクト固有情報を混在させず、秘密情報を保存しない。
