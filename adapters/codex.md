# OpenAI Codex

- 個人の既定値: Codexホーム（通常 `~/.codex`）の `AGENTS.md`
- 一時的なグローバル上書き: `AGENTS.override.md`
- チーム共有: リポジトリルートの `AGENTS.md`
- 局所規則: 対象へ近いディレクトリの `AGENTS.md` または `AGENTS.override.md`
- 読込順: グローバルの後、プロジェクトルートから現在地へ向かって連結され、近い指示が優先
- 既定の結合上限: 32KiB。重要な指示を短く保ち、詳細は明示的に読む別文書へ分割
- repo向けSkill: 対象repoの `.agents/skills/<skill-name>`
- ユーザー向けSkill: `$HOME/.agents/skills/<skill-name>`
- Skillは明示的な`$<skill-name>`または`description`との一致で起動し、同名Skillは統合されない

個人設定付きの入口にはルート `ROOT_AGENTS_TEMPLATE.md`、汎用のみなら
`templates/ROOT_AGENTS_GENERIC.md` を利用します。

導入後は新しいセッションで「現在読み込まれている指示元と優先順を要約して」と依頼し、
想定したファイルが有効か確認します。

このリポジトリの`skills/`やルートAGENTSからの参照だけではSkillは自動導入されません。
Codexが探索する`.agents/skills`への明示的な導入・同期は`docs/SKILL_MANAGEMENT.md`に
従います。新環境では`scripts/setup_environment.py`をdry-run後に適用すると、ルートAGENTS
生成、Skill導入、検証をまとめて実行できます。

## CodexサンドボックスでGitHub CLI認証を診断する

GitHub CLIのトークンをシステム資格情報ストアへ保存している環境では、Codexサンドボックスの
制限されたユーザーコンテキストから資格情報ストアへアクセスできず、`gh auth status`が
保存済みアカウントを無効と報告することがあります。この結果だけで認証切れと断定しません。
macOSのKeychainに加え、Windowsの資格情報ストアを利用するネイティブCodex環境でも
この事象を確認しています。

GitHub関連のSkillやツールが`gh auth status`の失敗を停止条件としていても、結果が
サンドボックス内のものなら、再認証を案内する前に次の切り分けを先に行います。
サンドボックス外で成功した場合は認証済みとして、元のGitHub作業を続けます。

1. `GH_TOKEN`、`GITHUB_TOKEN`などの認証用環境変数が設定されているかを確認します。
   値は表示せず、設定の有無だけを扱います。
2. システム資格情報ストアへの保存を想定している場合は、ユーザー承認を得て、同じ
   読み取り専用の`gh auth status`をサンドボックス外のユーザーコンテキストで再実行します。
3. サンドボックス外で成功した場合は再ログインを求めず、必要な`gh`や`git`コマンドだけを
   個別に承認されたサンドボックス外実行へ切り替えて、元のGitHub作業を続けます。
4. サンドボックス外でも失敗した場合、または利用者がアカウント切替を希望した場合にだけ、
   `gh auth login`による再認証を案内します。

サンドボックス自体へ永続的にログインし直す必要はありません。通常は、資格情報ストアを
参照するコマンドに限定した承認を使います。継続的なヘッドレス実行で承認を避ける必要がある
場合は、必要最小権限かつ短命な`GH_TOKEN`をCodexプロセスの環境へ渡せます。環境変数認証は
保存済み資格情報より優先され、子プロセスからも参照できるため、トークンを出力せず、repoや
平文ファイルへ保存せず、作業後に破棄します。

診断中に`gh auth token`や`printenv GH_TOKEN`などでトークン本体を表示しません。
`gh auth login --insecure-storage`や、資格情報ファイルのworkspaceへの複製も行いません。
この手順はmacOSとWindowsで観測したシステム資格情報ストアの分離を扱うものであり、
すべての`gh auth status`失敗の原因へ一般化しません。

公式: [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Codex公式: [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security.md)、
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox.md)

Skill公式: [Build skills](https://learn.chatgpt.com/docs/build-skills)

GitHub CLI公式: [gh auth login](https://cli.github.com/manual/gh_auth_login)、
[gh help environment](https://cli.github.com/manual/gh_help_environment)
