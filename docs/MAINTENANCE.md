# agent-spec 更新・保守ルール

この文書は、ローカル環境、別PC、クラウドエージェントなど、どの環境から
`agent-spec`を更新する場合にも適用します。

## 1. 更新前の確認

### 指示と構成

編集前に次を読みます。

1. ルート `AGENTS.md`
2. `instructions/core/principles.md`
3. `instructions/core/task-lifecycle.md`
4. `instructions/core/instruction-authoring.md`
5. 本文書
6. Skill変更の場合は `docs/SKILL_MANAGEMENT.md` と対象の `SKILL.md`
7. 更新対象に関連するプロファイル、アダプター、公式資料、Serenaメモリ

### Gitと作業ツリー

- `git status --short --branch` でブランチ、未コミット、未追跡ファイルを確認します。
- `git remote -v` で正本リモートが意図したリポジトリか確認します。
- リモートとの同期確認が必要なら、ネットワーク権限を確認して `git fetch` を行います。
- 未コミット変更がある状態で、無断の `pull`、rebase、reset、checkoutによる上書きを
  行いません。
- 他環境の変更と競合している場合は、双方の意図を確認してから統合します。
- ブランチ作成、commit、push、PR作成は、ユーザーの依頼またはリポジトリ運用ルールに
  含まれる範囲でのみ行います。

## 2. 変更内容を分類する

| 変更内容 | 正本 |
|---|---|
| 全利用者に適用できる原則 | `instructions/core/` |
| 実装、調査、レビューなど特定作業の手順 | `instructions/use-cases/` |
| 個人の言語、通知、ツール、コード嗜好 | `profiles/<name>/` |
| Codex、Copilot、Geminiなど製品固有の差分 | `adapters/` |
| コピーして具体化する雛形 | `templates/` |
| 反復する実行手順、参照資料、任意スクリプト | `skills/<skill-name>/` |
| Skill横断の作成・導入・検証・配布ルール | `docs/SKILL_MANAGEMENT.md` |
| 構成と読込順 | `docs/INSTRUCTION_ARCHITECTURE.md` |
| 外部公式資料と採用判断 | `docs/OFFICIAL_GUIDANCE.md` |
| 取り込み元と除外理由 | `docs/SOURCE_INVENTORY.md` |
| 時系列の変更概要 | `docs/CHANGELOG.md` |
| 安定した非自明な索引・知識 | `.serena/memories/` |

適切な場所がない場合は、既存ファイルへ無理に追加せず、責務が明確なディレクトリまたは
文書を追加します。ルートAGENTS.mdは索引のまま保ちます。

## 3. 追加・更新の基準

- 1回限りの依頼や一時状態を、全環境へ常時適用する規則にしません。
- 同じ誤り、指摘、手順が繰り返され、今後の再発見コストを下げる場合に永続化します。
- `常に`、`必ず`、`禁止`は、適用範囲と例外を確認してから使用します。
- 個人プロファイルの内容を、汎用コアへ自動昇格しません。
- 他プロジェクトのAGENTS.mdを丸ごと複製せず、再利用できる規則だけを抽出します。
- 機械的に検証できる規則は、可能なら文書に加えてテスト、リンター、フック、検証スクリプト
  へ移します。

## 4. 公式情報を更新する

- 製品仕様、対応形式、設定キー、既定値など変わり得る情報は、更新時点の一次資料で確認します。
- OpenAI製品はOpenAI公式文書、他製品は各提供元の公式文書を優先します。
- `docs/OFFICIAL_GUIDANCE.md` の確認日、URL、ローカル要約、採用判断を必要に応じて更新します。
- 公式文書を長く転載せず、運用に必要な要点を言い換えて記録します。
- 情報源同士が食い違う場合は、対象製品、バージョン、確認日、差異を明記します。
- URLへアクセスできない場合は、未確認であることを明記し、記憶だけで最新情報を上書きしません。

## 5. 同期して更新するファイル

変更箇所だけでなく、次の依存先を確認します。

### 汎用コアを変更した場合

- ルート `AGENTS.md` のルーティング
- `README.md` と `docs/INSTRUCTION_ARCHITECTURE.md`
- `templates/ROOT_AGENTS_GENERIC.md` と個人用ルートテンプレート
- 関連する `instructions/use-cases/`
- Serenaの `core`、`conventions`、`task_completion`

### 個人プロファイルを変更した場合

- 対象 `profiles/<name>/AGENTS.md` の読込先
- そのプロファイルを使うルートテンプレート
- `docs/SOURCE_INVENTORY.md`
- 汎用コアへ個人固有内容が混入していないこと

### アダプターを変更した場合

- `adapters/README.md` の対応表
- `docs/OFFICIAL_GUIDANCE.md` の公式URLと確認日
- 対応するテンプレートや設定例
- ベンダー固有機能を汎用ルールの前提にしていないこと

### Skillを変更した場合

- `skills/README.md` のカタログ
- `docs/SKILL_MANAGEMENT.md` の構造・導入・検証ルール
- `agents/openai.yaml` と `SKILL.md` の名称・説明・既定プロンプト
- 関連する `README.md`、アダプター、テンプレート、Serenaメモリ
- `python scripts/validate_skills.py` と追加したSkill内スクリプトの実行結果
- 導入先コピーやPluginを直接編集せず、repo内の正本から同期すること

### ファイル移動・改名をした場合

- ルートAGENTS、README、テンプレート、アダプター、文書内の全参照
- Serenaメモリ内の参照
- 各環境へ既にコピーされたルートファイルの移行案内

### すべての意味のある変更

- `docs/CHANGELOG.md` に利用者へ影響する変更を簡潔に追記します。
- `docs/SOURCE_INVENTORY.md` は、出典・分類・除外判断が変わった場合だけ更新します。
- Serenaメモリは、安定した非自明な情報が変わった場合だけ更新します。

## 6. 環境非依存性を守る

- 正本には端末固有の絶対パスを保存せず、テンプレートでは
  `<AGENT_SPEC_REPOSITORY_PATH>` のようなプレースホルダーを使います。
- OS固有コマンドを書く場合は対象OSを明記し、可能なら代替手段も示します。
- `.serena/project.local.yml`、キャッシュ、一時ファイル、認証情報を共有対象にしません。
- 文字コードはUTF-8、Markdownは一般的なCommonMark互換記法を使います。
- 製品固有のimport構文や設定は `adapters/` に閉じ込めます。

## 7. 検証

最低限、次を確認します。

- 変更された全MarkdownがUTF-8で読める。
- 末尾空白、競合マーカー、壊れた相対リンクがない。
- ルートAGENTSは短いルーターのままで、詳細本文が再流入していない。
- 参照されたファイルとディレクトリが存在する。
- テンプレートのプレースホルダーは意図した箇所だけに残っている。
- 個人設定、汎用コア、製品固有設定の境界が保たれている。
- Serenaの全 `mem:` 参照先が存在する。
- Skill変更時は `python scripts/validate_skills.py` が成功する。
- `python scripts/validate_repository.py` が成功する。
- `git status --short --untracked-files=all` で意図したファイルだけが変更されている。
- 追跡済み差分には `git diff --check` を実行する。

外部URLの到達確認ができない環境では、URL検証を未実施として報告します。

## 8. 引き渡し

最終報告には次を含めます。

- 変更した規則と、その適用範囲
- 追加・更新・移動した主要ファイル
- 参照した公式資料と確認日
- 実行した検証と結果、未実施の検証
- 互換性や、他環境のルートファイルで必要になる変更
- commit、push、PRの実施有無

## 完了条件

- 正しい責務のファイルへ変更が配置されている。
- 必要な同期先が更新され、重複する正本がない。
- 個人情報、秘密情報、端末固有情報が混入していない。
- ローカル検証が成功し、実行できなかった確認が明示されている。
- 別環境のエージェントが本文書だけで安全に同じ更新手順を再現できる。
- Skill変更時は、正本、導入範囲、同期方法、起動確認方法が明示されている。
