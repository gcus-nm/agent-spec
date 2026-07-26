# ベンダー別アダプター

汎用ルール自体は `instructions/` を正本とし、ここでは各エージェントへ読み込ませる方法だけを
扱います。対応状況は製品更新で変わるため、導入前に各ファイルの公式URLを確認してください。

| 環境 | 標準的な入口 | 詳細 |
|---|---|---|
| OpenAI Codex | `~/.codex/AGENTS.md`、リポジトリの `AGENTS.md` | `codex.md` |
| GitHub Copilot | `.github/copilot-instructions.md`、`AGENTS.md` | `github-copilot.md` |
| Gemini CLI | `GEMINI.md`、または設定した `AGENTS.md` | `gemini-cli.md` |

ベンダー固有ファイルへ汎用ルール全文を複製せず、このリポジトリのローカルコピーを読む
短いルーターを置く方針を推奨します。

CodexをmacOSで使用する場合の、Keychain保存されたGitHub CLI認証の切り分けも
`codex.md`で扱います。
