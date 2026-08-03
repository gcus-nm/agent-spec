# ベンダー別アダプター

汎用ルール自体は `instructions/` を正本とし、ここでは各エージェントへの読込方法と、
製品固有の導入・設定・挙動・診断差分を扱います。対応状況は製品更新で変わるため、
参照時に各ファイルの公式URLを確認してください。

| 環境 | 標準的な入口 | 詳細 |
|---|---|---|
| OpenAI Codex | `~/.codex/AGENTS.md`、リポジトリの `AGENTS.md` | [`codex.md`](codex.md) |
| GitHub Copilot | `.github/copilot-instructions.md`、`AGENTS.md` | [`github-copilot.md`](github-copilot.md) |
| Gemini CLI | `GEMINI.md`、または設定した `AGENTS.md` | [`gemini-cli.md`](gemini-cli.md) |

ベンダー固有ファイルへ汎用ルール全文を複製せず、このリポジトリのローカルコピーを読む
短いルーターを置く方針を推奨します。

Codexサンドボックスからシステム資格情報ストアを参照できず、GitHub CLI認証が
無効に見える場合の切り分けも[`codex.md`](codex.md)で扱います。
