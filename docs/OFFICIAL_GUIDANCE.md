# 公式・標準資料と採用方針

確認日: 2026-07-21

## OpenAI Codex

- [Codex Best practices](https://learn.chatgpt.com/guides/best-practices)
  - プロンプトにGoal、Context、Constraints、Done whenを含める。
  - AGENTS.mdは短く実用的に保ち、肥大化したら計画、レビュー、アーキテクチャなどを
    タスク別Markdownへ分ける。
  - ビルド、テスト、リント、規約、禁止事項、完了条件を明記する。
- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
  - グローバル、リポジトリ、ネストしたディレクトリの順に指示を階層化する。
  - 対象に近い指示を優先する。
  - Codexの既定では結合されたプロジェクト指示に32KiBの上限があるため、短く保つ。
- [Codex customization](https://learn.chatgpt.com/docs/customization/overview)
  - AGENTSは永続的な挙動、メモリは蓄積文脈、Skillは反復手順、MCPは外部接続に使い分ける。
  - 繰り返す誤りやレビュー指摘を指示へ反映し、自動検査と組み合わせる。
- [Prompting Codex](https://learn.chatgpt.com/docs/prompting)
- [Codex execution plans](https://developers.openai.com/cookbook/articles/codex_exec_plans)

## オープン形式・他エージェント

- [AGENTS.md公式サイト](https://agents.md/)
  - AGENTS.mdをエージェント向けREADMEとして扱うオープン形式。
  - プロジェクト概要、実行、テスト、コード規約、セキュリティ、PR指示が代表的な内容。
  - 大規模リポジトリではサブプロジェクトごとにネストしたAGENTS.mdを置く。
- [agentsmd/agents.md GitHub](https://github.com/agentsmd/agents.md)
- [GitHub Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
  - リポジトリ共通、パス固有、AGENTS.mdを使うエージェント指示を分けられる。
- [GitHub Copilot instruction support](https://docs.github.com/en/copilot/reference/custom-instructions-support)
  - 製品・IDEごとに対応するファイル形式が異なるため、導入先の対応状況を確認する。
- [Gemini CLI GEMINI.md](https://geminicli.com/docs/cli/gemini-md/)
  - グローバル、ワークスペース、必要時の局所コンテキストを階層化できる。
  - `@file.md`による分割読込をサポートするが、これはGemini固有機能なので
    ベンダー非依存のAGENTS.mdでは前提にしない。

## このリポジトリでの採用判断

- OpenAIとAGENTS.mdオープン形式に共通する、短いルート・正確なコマンド・階層化・
  局所化・検証の明記を汎用コアに採用します。
- ベンダー固有のファイル名、import構文、設定キーは汎用コアへ混ぜず、必要に応じて
  `adapters/`へ追加します。
- 外部資料が変わっても作業不能にならないよう、重要な要点はローカル文書にも保持します。
- 例示された規則をそのまま普遍化せず、実際のプロジェクトで反復して必要になったものだけを
  永続指示へ追加します。
