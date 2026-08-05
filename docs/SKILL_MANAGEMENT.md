# Skill管理ルール

この文書は、再利用可能なSkillをこのリポジトリで作成、導入、更新、検証、配布するための
正本です。

## 1. 適用範囲を選ぶ

| 内容 | 適切な置き場所 |
|---|---|
| 常に適用する短い規約・コマンド | `AGENTS.md`または`instructions/` |
| 決定的なローカル検索、ビルド、テスト、変換 | 標準ツール、CLI、スクリプト |
| 反復するタスクの手順、参照資料、決定的なスクリプト | Skill |
| SkillとMCP、コネクター、フックなどをまとめて配布 | Plugin |
| 外部データや外部操作 | MCPまたはコネクター |

1回限りのプロンプトや、単なる長文資料をSkillへ昇格しません。明確な入力、手順、出力、
再利用場面を持つ作業をSkillにします。

MCPをトークン節約だけを理由に追加しません。ローカルの決定的処理はCLIまたはスクリプト、
反復する判断と手順はSkill、外部データや対話的な外部操作はMCPまたはコネクターを選びます。
同等の情報を返すツールを重複して呼ばず、大きなツールスキーマは必要なタスクだけで有効化
します。

## 2. リポジトリ構成

共有するSkillの正本は`skills/<skill-name>/`です。

```text
skills/
├── README.md                 リポジトリ全体のSkill索引
└── <skill-name>/
    ├── SKILL.md              必須。起動条件と実行手順
    ├── agents/
    │   └── openai.yaml       任意。UI情報、起動方針、ツール依存
    ├── scripts/              任意。反復する決定的処理
    ├── references/           任意。必要時だけ読む詳細資料
    └── assets/               任意。成果物へ使用する素材
```

- Skill名とディレクトリ名は一致させ、64文字未満のlowercase kebab-caseにします。
- `SKILL.md`のYAML frontmatterは`name`と`description`だけにします。
- `description`には機能と起動条件を簡潔に含め、本文へ起動条件を分散させません。
- 本文は命令形で、通常500行未満に保ちます。詳細は1階層の`references/`へ分けます。
- `scripts/`は同じ処理を繰り返す場合や、決定的な再現性が必要な場合だけ追加します。
- Skill内に`README.md`、`CHANGELOG.md`、`INSTALLATION_GUIDE.md`などの運用文書を
  置きません。索引、導入、変更履歴はrepo側文書へ置きます。
- 同じ情報を`SKILL.md`と`references/`へ重複させません。

## 3. 作成・更新手順

1. [`templates/SKILL_REQUEST.md`](../templates/SKILL_REQUEST.md)を使い、起動すべき例、
   起動すべきでない例、入力、出力、制約を具体化します。
2. 既存Skillと名前・責務・起動条件が重複しないか`skills/README.md`で確認します。
3. 新規作成は、利用可能なら`$skill-creator`とその`init_skill.py`を使って
   `skills/<skill-name>/`へ初期化します。
4. 最小の`SKILL.md`から始め、必要なリソースだけを追加します。
5. `agents/openai.yaml`を持つ場合は、表示名、25〜64文字の短い説明、Skill名を含む
   `default_prompt`をSkill本文と同期します。
6. 追加したスクリプトを実行し、正常系と代表的な失敗系を確認します。
7. 複雑なSkillは、正解や診断を渡さない現実的な依頼で独立エージェントによる
   forward testを行います。本番変更や長時間処理を伴う場合は先に承認を得ます。
8. `skills/README.md`と変更履歴を同期します。本書、公式資料、関連メモリは、横断ルール、
   外部根拠、安定した索引が変わる場合だけ更新します。

### スクリプトへ昇格する基準

- Skillが実行のたびに同じ用途のコードを生成するなら、Skillの`scripts/`へファイルとして
  切り出します。repo全体で共有する検証処理はルート`scripts/`へ置きます。
- 数行の一度限りのコマンドは本文に残せますが、分岐、ファイル走査、構造化出力、終了コード、
  外部ツール連携を持つ処理はスクリプト化します。
- スクリプトには端末固有パスや秘密値を埋め込まず、引数または環境から明示的に受け取ります。
- 読み取り専用と変更ありの動作を分離し、変更ありの既定動作を避けます。
- 正常系と代表的な失敗系を実行し、終了コードと出力形式をSkill本文に記載します。
- 複数Skillで同じスクリプト生成が繰り返され、入力・出力・判断が独立したワークフローに
  なった場合だけ、スクリプト化支援自体を別Skillへ昇格します。

## 4. Codexへ導入する

このrepoの`skills/`は管理上の正本であり、別repoから自動探索される場所ではありません。
ルート`AGENTS.md`からこのrepoを参照しても、Skillは自動導入されません。使用先へSkill
ディレクトリ単位でコピーするか、正本へのシンボリックリンクを明示的に作ります。

| 適用範囲 | 導入先 |
|---|---|
| 特定repo全体 | `<TARGET_REPOSITORY>/.agents/skills/<skill-name>` |
| ユーザーの全repo | `$HOME/.agents/skills/<skill-name>` |
| 共有マシン・コンテナ | `/etc/codex/skills/<skill-name>` |

コピーは単純ですが、更新時に再同期が必要です。シンボリックリンクは正本の更新を即時反映
できますが、権限・OS・クローン先パスに依存します。各環境の制約に合わせて選びます。

### 初回セットアップをまとめて実行する

ルートAGENTSの生成、repoパス置換、全Skillの導入、セットアップ検証をまとめる場合は、
まずdry-runを確認してから`--apply`を付けます。

```text
python3 scripts/setup_environment.py --repo <AGENT_SPEC_REPOSITORY_PATH>
python3 scripts/setup_environment.py --repo <AGENT_SPEC_REPOSITORY_PATH> --apply
```

Windowsでは`python`で実行します。汎用プロファイルは`--profile generic`を追加します。
Skill配置方式はmacOS・Linuxでシンボリックリンク、Windowsでコピーを自動選択します。
必要なら`--skill-mode symlink`または`--skill-mode copy`で明示します。

スクリプトは既存ルートAGENTSを自動上書きしません。必要な参照と実際のrepoパスを持つ既存
ファイルは保持します。旧形式の多段ルーターも読取互換として保持し、トークン効率化には
新テンプレートの手動統合を案内します。旧形式と判定できた通常ファイルは、
`--migrate-root-agents`を明示すると `AGENTS.md.pre-token-efficiency.bak` 系へバックアップして
最適化版へ移行できます。未知形式とシンボリックリンクは移行しません。互換性がない場合は
FAILとして手動統合を案内します。既定はdry-runで、変更は`--apply`を指定した場合だけ行います。

```text
python3 scripts/setup_environment.py --repo <AGENT_SPEC_REPOSITORY_PATH> --migrate-root-agents
python3 scripts/setup_environment.py --repo <AGENT_SPEC_REPOSITORY_PATH> --migrate-root-agents --apply
```

コピー方式ではrepo更新後に導入済みSkillと正本が異なることがあります。既定動作はFAILで
停止します。差分を確認し、既存コピーをバックアップして正本へ同期する場合だけ、dry-runと
適用の両方へ`--refresh-skills`を明示します。

```text
python scripts/setup_environment.py --repo <AGENT_SPEC_REPOSITORY_PATH> --refresh-skills
python scripts/setup_environment.py --repo <AGENT_SPEC_REPOSITORY_PATH> --refresh-skills --apply
```

更新前コピーはSkill探索先の外にある`<SKILLS_TARGET>.pre-refresh-backups/`へ保存します。
ローカル変更は有効なSkillから外れますがバックアップには残るため、必要な内容はrepo正本へ
整理します。このオプションは通常ディレクトリのコピーだけを対象とし、シンボリックリンク、
同名ファイル、比較不能なコピーは自動変更しません。

### Skillだけを導入・再同期する

全Skillをユーザー共通の導入先へ安全に配置するには、まずdry-runで計画を確認してから
`--apply`を付けます。macOS・LinuxではPython 3を`python3`で起動します。

```text
python3 scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode symlink
python3 scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode symlink --apply
```

Windowsでは、権限設定に左右されにくいコピー方式を既定例にします。

```text
python scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode copy
python scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode copy --apply
```

正本と異なる既存コピーを再同期する場合は、先に差分を確認してから明示的に更新します。

```text
python scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode copy --refresh-existing
python scripts/install_skills.py --repo <AGENT_SPEC_REPOSITORY_PATH> --target "$HOME/.agents/skills" --mode copy --refresh-existing --apply
```

Windowsで開発者モードなどによりリンク作成権限がある場合は`--mode symlink`も選べます。
シンボリックリンクを作れない環境では`--mode copy`を使用します。スクリプトは既存の異なる
コピーやリンクを既定では上書きしません。FAILになった対象は差分とリンク先を確認し、コピー
だけを`--refresh-existing`で再同期するか、手動で整理してから再実行します。

CodexはSkill変更を通常自動検出します。表示されない場合は新しいセッションまたはCodexの
再起動後に、`$<skill-name>`またはSkill一覧で確認します。その後、
`verify-agent-spec-setup`の検証スクリプトを`--require-skills`付きで実行します。同名Skillは
統合されず複数表示され得るため、導入先に古いコピーを残しません。

複数Skillを組織へ配布する場合や、MCP・コネクター・フックとまとめる場合はPlugin化を
別変更として検討します。

## 5. 検証

リポジトリルートで次を実行します。

```text
python scripts/validate_repository.py
```

macOS・Linuxで`python`が存在しない場合は、以降の検証コマンドも`python3`で実行します。

この検証はUTF-8、Markdownリンク、Serena参照、端末固有パス、空白、競合マーカー、
`git diff --check`に加え、`scripts/validate_skills.py`を呼び出します。Skill検証は、Skill名、
必須frontmatter、ディレクトリ名との一致、不要なSkill内文書、
`agents/openai.yaml`の主要UIメタデータを確認します。加えて次を手動または利用可能な
公式validatorで確認します。

`$skill-creator`のソースを利用できる環境では、リポジトリルートから同Skillに同梱された
`scripts/quick_validate.py`へ`skills/<skill-name>`を渡して実行します。validatorの依存関係を
利用できない場合は、repo validatorを代替確認として実行し、公式validator未実施の理由を
報告します。

- `description`が起動すべき例と起動すべきでない例を適切に分離する。
- `SKILL.md`が必要なリソースを直接案内し、深い参照チェーンを作っていない。
- 追加したスクリプトが対象OS・ランタイムで成功する。
- 秘密情報、個人情報、端末固有の絶対パス、無許諾の第三者素材を含まない。
- `git diff --check`とMarkdownリンク検証が成功する。

## 6. 変更と配布

- Skillの振る舞いが変わる変更は`docs/CHANGELOG.md`へ記録します。
- 後方互換性を壊す変更は、起動条件、入力、出力、導入先への影響をPRに明記します。
- repo内の正本、導入先コピー、Plugin版を同時に直接編集しません。repo内の正本を更新して
  から、各配布先を再生成または再同期します。
- 外部Skillを取り込む場合は、出典、ライセンス、変更点、更新方法を
  `docs/SOURCE_INVENTORY.md`へ記録します。
