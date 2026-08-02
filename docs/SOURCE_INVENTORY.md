# 取り込み元一覧

## 個人プロファイルへ取り込んだ情報

- 現在のセッションで提供されたルートAGENTS指示
  - 日本語応答と非公開セルフレビュー
  - プロジェクトAGENTSの参照・記録方針
  - uLoopMCP、Serena、Playwright、Context7、GitHub、File Systemの利用方針
  - VOICEVOXの話者、速度、通知タイミング
  - UnityのnullチェックとC# 10規約
  - 新規Webサービスを、明示指定がない限りDockerコンテナとして作成する方針
  - Gitコミットメッセージを`<type>: <日本語の要約>`形式に統一する方針
- 2026-08-03のユーザー依頼とWeb API関連の公式資料
  - バックエンドの主要操作を、Web UIだけでなくAPIを呼び出すCLIからも利用可能にする方針
  - CLIをAIが安全に操作できるよう、機械可読出力、dry-run、冪等性、最小権限、監査記録を
    備える方針
  - Web、CLI、必要に応じたMCPでAPIクライアントまたはApplication Serviceを共有し、
    ブラウザーからCLIを通常の実行経路として呼び出さない設計
- 保存先: `profiles/personal/`

## 汎用コアへ取り込んだ情報

- OpenAI Codex公式マニュアルのBest practices、AGENTS discovery、Customization
- OpenAI Codex公式マニュアルのBuild skills、Skill検出範囲、progressive disclosure、Plugin配布
- OpenAI同梱`skill-creator`の構成、frontmatter、UIメタデータ、検証、forward test方針
- OpenAI Skills repositoryとAgent Skills specificationの形式・実例
- AGENTS.mdオープン形式の構成・階層化
- GitHub CopilotとGemini CLIのスコープ分離・モジュール化の考え方
- 安全な実装、調査、レビューに共通するタスクライフサイクル

出典URLと採用判断は `docs/OFFICIAL_GUIDANCE.md` に集約しています。

## ベンダー別アダプターへ取り込んだ情報

- GitHub CLI公式マニュアルの、システム資格情報ストアへのトークン保存と認証用環境変数の
  優先順位
- CodexサンドボックスからmacOS Keychainへアクセスできない場合に、`gh auth status`の
  失敗を認証切れと即断せず、サンドボックス外の読み取り専用チェックで切り分ける運用
- 保存先: `adapters/codex.md`

## Skillへ取り込んだ情報

- このリポジトリの既存保守手順を`skills/maintain-agent-spec/`へワークフロー化しました。
- ルートAGENTS、repo必須文書、導入済みSkill、実行時検出の確認手順を
  `skills/verify-agent-spec-setup/`へワークフロー化しました。
- セッション内で繰り返していたrepo検証を`scripts/validate_repository.py`へ切り出しました。
- Skill本体へ時系列履歴や導入説明を複製せず、`docs/SKILL_MANAGEMENT.md`と
  `skills/README.md`を横断的な正本にしました。
- 外部Skillを将来取り込む場合は、出典、ライセンス、ローカル変更、更新方法を本書へ
  追記します。

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
