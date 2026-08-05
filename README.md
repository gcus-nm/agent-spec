# agent-spec

AIコーディングエージェント向けの指示とSkillを、汎用ルール・個人設定・ユースケース・
再利用可能なワークフロー・ベンダー別導入形式に分けて管理するリポジトリです。

## ディレクトリ

```text
AGENTS.md                         このリポジトリ自身の短いルーター
instructions/core/               全環境で再利用できる原則と設計規約
instructions/use-cases/          作業別手順と、依頼種別から選ぶための索引
profiles/personal/               個人向け指示の既定プロファイル
adapters/                        Codex、Copilot、Gemini CLI向け導入差分
templates/                       環境ルート・プロジェクト・タスク用ひな形
skills/                          複数環境で再利用するSkillの正本
scripts/                         環境セットアップ、Skill導入、機械的な検証
docs/                            設計、公式資料、取り込み元、変更履歴
.serena/memories/                Serena向けの索引と長期メモリ
```

詳細な責務と読込順は `docs/INSTRUCTION_ARCHITECTURE.md` を参照してください。
`instructions/use-cases/README.md` は、環境ルートに直接ルートがない特殊作業用の
フォールバック索引です。

## 使い方

### 個人設定を含めて使う

1. このリポジトリを各環境から読める場所へクローンします。
2. リポジトリルートでセットアップのdry-runを確認します。
3. 同じコマンドへ`--apply`を付け、ルートAGENTS生成、Skill導入、検証を実行します。
4. Codexを再起動し、読込済みAGENTSの実在パスとSkill一覧を確認します。

macOS・Linuxでは次を実行します。

```text
python3 scripts/setup_environment.py --repo "$PWD"
python3 scripts/setup_environment.py --repo "$PWD" --apply
```

Windowsでは`python`で実行します。既存のルートAGENTSが必要な参照を満たさない場合は、
自動上書きせず停止します。テンプレートを既存ファイルへ手動統合して再実行してください。
旧形式の多段ルーターは読取互換として保持し、検証時に最適化テンプレートの手動統合を
案内します。旧形式と判定できたファイルをバックアップして自動移行する場合は、先にdry-runを
確認してから明示オプションを適用します。

```text
python3 scripts/setup_environment.py --repo "$PWD" --migrate-root-agents
python3 scripts/setup_environment.py --repo "$PWD" --migrate-root-agents --apply
```

移行前ファイルは同じディレクトリの `AGENTS.md.pre-token-efficiency.bak` 系の名前へ保存します。
未知形式やシンボリックリンクの既存ファイルは自動移行しません。Windowsでは`python3`を
`python`へ置き換えます。

### 汎用ルールだけを使う

セットアップコマンドへ`--profile generic`を付けます。個人プロファイルは読み込まれません。

### プロジェクトへ導入する

`templates/PROJECT_AGENTS.md` を対象リポジトリの `AGENTS.md` としてコピーし、実際の
ビルド・テスト・規約・完了条件に置換します。個別作業の依頼には
`templates/TASK_PROMPT.md` を利用できます。

利用環境ごとの自動読込形式は `adapters/README.md` から選んでください。

### Skillを使う・追加する

管理中のSkillは`skills/README.md`から選びます。ユーザー全体で使う場合は
`$HOME/.agents/skills/<skill-name>`、特定repoで使う場合は
`<TARGET_REPOSITORY>/.agents/skills/<skill-name>`へ、Skillディレクトリ単位でコピーまたは
シンボリックリンクします。ルート`AGENTS.md`からこのrepoを参照するだけではSkillは
自動導入されません。

全Skillをユーザー共通で使う場合は、dry-runを確認してから導入します。macOS・Linuxでは
`python3`とシンボリックリンク、Windowsでは`python`とコピー方式を既定にします。

通常の初回セットアップでは前述の`scripts/setup_environment.py`を使います。Skillだけを
個別に再同期する場合は次を使います。

```text
python3 scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode symlink
python3 scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode symlink --apply
```

Windowsでは上記の`python3`を`python`、`--mode symlink`を`--mode copy`へ置き換えます。

導入後はCodexを再起動するか新しいセッションを開始し、
`$verify-agent-spec-setup`で再検証します。詳細とコピー方式は`docs/SKILL_MANAGEMENT.md`を
参照してください。

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

- 通常タスクは、短い環境ルート、対象プロジェクトの `AGENTS.md`、条件に一致する追加文書か
  Skillだけを読みます。
- `AGENTS.md` は短く、正確で、常に適用すべき内容と条件付きルートに限定します。
- 詳細は条件付きMarkdownへ分け、頻出タスクは入口から直接、特殊作業だけ索引経由で読みます。
- 反復する実行手順はSkillにし、常時ルールや単なる長文資料と分離します。
- ローカル処理は標準ツールとCLIを基本とし、MCPは固有能力が必要な場合だけ使います。
- 個人設定とチーム共有ルールを分離します。
- 繰り返し発生した問題だけを永続ルールへ昇格します。
- 機械的に強制できる規則は、文章だけでなくリンター、テスト、型検査、フックでも
  実施します。

根拠となるOpenAI公式資料やAGENTS.mdオープン形式などは
`docs/OFFICIAL_GUIDANCE.md` にまとめています。

正本リポジトリ: `git@github.com:gcus-nm/agent-spec.git`
