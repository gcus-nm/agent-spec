# Gemini CLI

- 既定のコンテキストファイルは `GEMINI.md` です。
- グローバル、ワークスペース、必要時の局所ファイルを階層的に読み込みます。
- `settings.json` の `context.fileName` に `AGENTS.md` を設定できます。
- `@file.md`によるimportはGemini固有機能です。

ベンダー間の可搬性を優先する場合は、`context.fileName`で `AGENTS.md` を認識させます。
Geminiだけで詳細文書を自動importしたい場合は、汎用正本を変更せず、薄い `GEMINI.md` 側で
`@` importを構成します。

公式: [Provide context with GEMINI.md files](https://geminicli.com/docs/cli/gemini-md/)
