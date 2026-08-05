---
name: maintain-agent-spec
description: agent-specリポジトリのAGENTS指示、汎用原則、プロファイル、アダプター、テンプレート、Skill、Serenaメモリなどの仕様文書を分類・更新・検証する。共通指示の追加・改訂・再編成、公式根拠の反映、Skillの作成、保守ルールの更新を依頼されたときに使用する。導入済み環境の診断だけが目的ならverify-agent-spec-setupを使用する。
---

# agent-spec文書を更新する

## 準備する

1. リポジトリルートを特定し、`AGENTS.md`を読む。
2. `instructions/core/instruction-authoring.md`と`docs/MAINTENANCE.md`を読む。
   大規模、曖昧、高リスク、横断的な変更では`instructions/core/task-lifecycle.md`、外部根拠の
   精査を含む高リスク変更では`instructions/core/principles.md`も読む。
3. Skill作業では`docs/SKILL_MANAGEMENT.md`を読む。対象の`SKILL.md`が存在する場合は
   編集前に読み、新規作成では初期化後に読んでから編集を続ける。
4. 編集前にブランチ、作業ツリー、リモート、関連する既存ファイルを確認する。
5. 外部仕様に依存する変更では、`docs/OFFICIAL_GUIDANCE.md`にある公式資料から
   現行の挙動を確認する。
6. 直接ルートがない特殊作業だけ、
   [`instructions/use-cases/README.md`](../../instructions/use-cases/README.md)を
   フォールバック索引として使う。

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

## 指示の導線を保守する

1. 指示の追加、移動、改名、適用条件の変更では、自動または常時読む入口から本文までの
   流入参照を確認する。
2. 条件付き文書が複数ある場合は短い索引を正本とし、依頼条件と正確な文書パスを
   対応させる。「該当文書を読む」だけの案内にしない。
3. 参照先Markdownは自動読込されると仮定せず、入口から索引、索引から詳細文書までを
   1段ずつ明示する。
4. `rg`で詳細文書名の参照元を確認し、到達不能な指示を残さない。
5. ルートテンプレート、導入互換性チェック、セットアップ検証、
   `scripts/validate_repository.py`の必須ルーティングを同期する。

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
2. 必須ルーティングを変更した場合は、参照が欠けた代表例でvalidatorが失敗することも
   確認する。
3. 変更したSkill内にスクリプトがある場合は、正常系と代表的な失敗系を実行する。
4. 最終差分に、到達不能な指示、重複規則、秘密情報、端末固有パス、無関係な変更が
   ないか確認する。
5. commit、push、配布、PR作成は、ユーザーが許可した範囲でだけ行う。
6. 結果、主要ファイル、公式資料、検証、制約、Git操作を報告する。
