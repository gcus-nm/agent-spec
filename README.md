# agent-spec

AIコーディングエージェント向けの指示とSkillを、汎用ルール・個人設定・ユースケース・
再利用可能なワークフロー・ベンダー別導入形式に分けて管理するリポジトリです。

## ディレクトリ

```text
AGENTS.md                         このリポジトリ自身の短いルーター
instructions/core/               全環境で再利用できる原則と設計規約
instructions/use-cases/          実装、調査、レビューなど作業別の手順
profiles/personal/               個人向け指示の既定プロファイル
adapters/                        Codex、Copilot、Gemini CLI向け導入差分
templates/                       環境ルート・プロジェクト・タスク用ひな形
skills/                          複数環境で再利用するSkillの正本
scripts/                         Skillなどの機械的な検証
docs/                            設計、公式資料、取り込み元、変更履歴
.serena/memories/                Serena向けの索引と長期メモリ
```

詳細な責務と読込順は `docs/INSTRUCTION_ARCHITECTURE.md` を参照してください。

## 使い方

### 個人設定を含めて使う

1. このリポジトリを各環境から読める場所へクローンします。
2. `ROOT_AGENTS_TEMPLATE.md` をCodexホームなどのルート `AGENTS.md` へコピーします。
3. `<AGENT_SPEC_REPOSITORY_PATH>` をこのリポジトリの絶対パスへ置換します。
4. 新しいセッションで、読込済み指示の要約をエージェントに確認します。

### 汎用ルールだけを使う

`templates/ROOT_AGENTS_GENERIC.md` をコピーし、同様にリポジトリパスを置換します。
個人プロファイルは読み込まれません。

### プロジェクトへ導入する

`templates/PROJECT_AGENTS.md` を対象リポジトリの `AGENTS.md` としてコピーし、実際の
ビルド・テスト・規約・完了条件に置換します。個別作業の依頼には
`templates/TASK_PROMPT.md` を利用できます。

利用環境ごとの自動読込形式は `adapters/README.md` から選んでください。

### Skillを使う・追加する

管理中のSkillは`skills/README.md`から選びます。ユーザー全体で使う場合は
`$HOME/.agents/skills/<skill-name>`、特定repoで使う場合は
`<TARGET_REPOSITORY>/.agents/skills/<skill-name>`へ、Skillディレクトリ単位でコピーまたは
シンボリックリンクします。

Skillの作成・更新・検証・配布ルールは`docs/SKILL_MANAGEMENT.md`が正本です。新しいSkillの
依頼は`templates/SKILL_REQUEST.md`で起動例と入出力を定義し、変更後は
`python scripts/validate_repository.py`を実行します。

- `$maintain-agent-spec`: このrepoの仕様文書・Skill・メモリを更新する
- `$verify-agent-spec-setup`: 新環境のルートAGENTS・Skill導入・実行時検出を確認する

## このリポジトリを更新する

別環境を含め、このリポジトリ自体を変更するときは最初に
`docs/MAINTENANCE.md` を読んでください。更新対象の分類、同期が必要な文書、公式情報の
扱い、Gitの安全確認、検証、引き渡しを定義しています。

更新依頼を他のエージェントへ渡す場合は `templates/UPDATE_REQUEST.md` を利用できます。
対応環境では`$maintain-agent-spec`を使い、分類・同期・検証の手順を実行できます。導入後の
確認には`$verify-agent-spec-setup`を使います。

## 設計方針

- `AGENTS.md` は短く、正確で、常に適用すべき内容に限定します。
- 詳細はユースケース別Markdownへ分け、ルーターから必要なものだけを読みます。
- 反復する実行手順はSkillにし、常時ルールや単なる長文資料と分離します。
- 個人設定とチーム共有ルールを分離します。
- 繰り返し発生した問題だけを永続ルールへ昇格します。
- 機械的に強制できる規則は、文章だけでなくリンター、テスト、型検査、フックでも
  実施します。

根拠となるOpenAI公式資料やAGENTS.mdオープン形式などは
`docs/OFFICIAL_GUIDANCE.md` にまとめています。

正本リポジトリ: `git@github.com:gcus-nm/agent-spec.git`
