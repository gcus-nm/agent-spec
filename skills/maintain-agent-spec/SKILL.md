---
name: maintain-agent-spec
description: agent-specリポジトリのAGENTS指示、汎用原則、プロファイル、アダプター、テンプレート、Skill、Serenaメモリなどの仕様文書を分類・更新・検証する。共通指示の追加・改訂・再編成、公式根拠の反映、Skillの作成、保守ルールの更新を依頼されたときに使用する。導入済み環境の診断だけが目的ならverify-agent-spec-setupを使用する。
---

# agent-spec文書を更新する

## 準備する

1. リポジトリルートを特定し、`AGENTS.md`を読む。
2. `instructions/core/principles.md`、`instructions/core/task-lifecycle.md`、
   `instructions/core/instruction-authoring.md`、`docs/MAINTENANCE.md`を読む。
3. Skill作業では`docs/SKILL_MANAGEMENT.md`を読む。対象の`SKILL.md`が存在する場合は
   編集前に読み、新規作成では初期化後に読んでから編集を続ける。
4. 編集前にブランチ、作業ツリー、リモート、関連する既存ファイルを確認する。
5. 外部仕様に依存する変更では、`docs/OFFICIAL_GUIDANCE.md`にある公式資料から
   現行の挙動を確認する。

## 変更を分類する

- 全利用者向け原則は`instructions/core/`に置く。
- タスク固有のガイドは`instructions/use-cases/`に置く。
- 個人設定は`profiles/`に置く。
- ベンダー固有の導入差分は`adapters/`に置く。
- コピーして具体化する成果物は`templates/`に置く。
- 再利用する実行ワークフローは`skills/<skill-name>/`に置く。
- 安定したSerena索引は`.serena/memories/`に置く。

各規則の正本を1つに保ち、同じ文章を複製せず正本へリンクする。ルート`AGENTS.md`は
短いルーターのまま保つ。

## Skillを作成・更新する

1. Skillを起動すべき具体的な依頼と、起動すべきでない依頼を定義する。
2. 1つの反復作業へ集中させ、lowercase kebab-caseの短い名前を選ぶ。
3. 利用可能なら`$skill-creator`またはその`init_skill.py`で新規Skillを初期化する。
4. `SKILL.md`を簡潔な命令形で書き、起動条件をfrontmatterの`description`へ集約する。
5. 同じコードを各実行で生成する手順にしない。反復する処理や決定的な処理は
   `scripts/`へ切り出し、引数と終了コードを安定させて実行テストする。
6. 必要なリソースだけを追加する。候補は`scripts/`、`references/`、`assets/`、
   `agents/openai.yaml`とする。
7. 複雑な起動条件や手順は、安全な現実的依頼でforward testする。
8. `skills/README.md`、`docs/CHANGELOG.md`、影響する設計・導入文書を同期する。

## 検証して引き渡す

1. リポジトリルートで`python scripts/validate_repository.py`を実行する。
2. 変更したSkill内にスクリプトがある場合は、正常系と代表的な失敗系を実行する。
3. 最終差分に、重複規則、秘密情報、端末固有パス、無関係な変更がないか確認する。
4. commit、push、配布、PR作成は、ユーザーが許可した範囲でだけ行う。
5. 結果、主要ファイル、公式資料、検証、制約、Git操作を報告する。
