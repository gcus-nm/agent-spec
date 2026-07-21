# 取り込み元一覧

## 個人プロファイルへ取り込んだ情報

- 現在のセッションで提供されたルートAGENTS指示
  - 日本語応答と非公開セルフレビュー
  - プロジェクトAGENTSの参照・記録方針
  - uLoopMCP、Serena、Playwright、Context7、GitHub、File Systemの利用方針
  - VOICEVOXの話者、速度、通知タイミング
  - UnityのnullチェックとC# 10規約
- 保存先: `profiles/personal/`

## 汎用コアへ取り込んだ情報

- OpenAI Codex公式マニュアルのBest practices、AGENTS discovery、Customization
- AGENTS.mdオープン形式の構成・階層化
- GitHub CopilotとGemini CLIのスコープ分離・モジュール化の考え方
- 安全な実装、調査、レビューに共通するタスクライフサイクル

出典URLと採用判断は `docs/OFFICIAL_GUIDANCE.md` に集約しています。

## Serena

- 共有メモリ `memory_maintenance` を `.serena/memories/memory_maintenance.md` に保持します。
- このリポジトリ固有の索引・規約・完了条件は同ディレクトリの各メモリに保持します。

## 意図的に取り込まない情報

- 他プロジェクトの製品仕様、長大な作業履歴、認証・課金・配布ルール
- 一時的な調査結果、端末固有資格情報、秘密値
- 公式資料の長い転載

個別プロジェクトへしか適用できない情報は、そのプロジェクトを正本とします。

## 調査時の制約

- 2026-07-21の初回調査時、このリポジトリには既存コミットがありませんでした。
- VOICEVOXエンジンへ接続できず、通知は試行したものの失敗しました。
