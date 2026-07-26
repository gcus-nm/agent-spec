# 変更履歴

## 2026-07-27

- 個人プロファイルのGitコミットメッセージを、変更種別を表す英字の`type`と
  日本語の要約を組み合わせた`<type>: <日本語の要約>`形式へ統一しました。
- 常時読むタスクライフサイクルから、実行環境固有の認証・権限・サンドボックス・検出問題を
  対応アダプターへルーティングする導線を追加しました。
- GitHub関連Skillがサンドボックス内の`gh auth status`失敗を停止条件にしていても、
  CodexアダプターのKeychain診断を先に行い、外側で成功したら作業を続けるよう明記しました。
- 必須のアダプター導線がタスクライフサイクルから失われていないことをrepo検証へ追加しました。
- ユースケース別の索引を追加し、依頼種別からコード変更、レビュー、調査の各文書を
  正確なパスで選べるようにしました。
- 製品固有の導入・設定・挙動確認と、指示文書の設計・編集から対応文書への導線を追加しました。
- maintenance Skillへ指示の到達性監査と、欠落時にvalidatorが失敗することの確認を追加しました。
- ルートテンプレート、セットアップ検証、repo検証で必須ルーティングを保護しました。

## 2026-07-26

- macOSのCodexサンドボックスでKeychain保存されたGitHub CLI認証が無効に見える場合に、
  認証切れと即断せず、秘密値を表示しない読み取り専用チェックで切り分ける手順を
  Codexアダプターへ追加しました。

## 2026-07-25

- 個人プロファイルへ、明示指定がない新規WebサービスをDockerコンテナとして作成・検証する
  既定方針を追加しました。

## 2026-07-21

- 現在の個人向け指示を初期版として取り込みました。
- Serenaメモリと環境ルート向けテンプレートを追加しました。
- ルートAGENTS.mdを短いルーターへ変更しました。
- 汎用コア、ユースケース別手順、個人プロファイル、汎用テンプレートを分離しました。
- OpenAI Codex、AGENTS.mdオープン形式、GitHub Copilot、Gemini CLIの公式資料を整理しました。
- 他環境から安全に更新するための保守ルールと更新依頼テンプレートを追加しました。
- 端末のユーザー名に依存していたプロファイル名を `profiles/personal/` へ変更しました。
- Skillの正本、作成・導入・同期・配布ルール、作成依頼テンプレートを追加しました。
- このリポジトリを保守する`maintain-agent-spec` Skillを追加しました。
- Skill構造と`agents/openai.yaml`を検証する`python scripts/validate_skills.py`を追加しました。
- OpenAIのBuild skills、OpenAI Skills、Agent Skills specification、Plugin配布方針を
  公式資料一覧へ追加しました。
- `maintain-agent-spec`を仕様文書更新専用として明確化し、定型repo検証を
  `scripts/validate_repository.py`へ切り出しました。
- 新環境のルートAGENTS、必須文書、導入済みSkill、実行時検出を診断する
  `verify-agent-spec-setup` Skillと読み取り専用スクリプトを追加しました。
- Skillが反復して生成するコードを`scripts/`へ昇格する基準を追加しました。
- ルートAGENTSによるrepo参照だけではSkillが自動導入されないことを明記し、全管理Skillを
  dry-run付きでコピーまたはシンボリックリンクする`scripts/install_skills.py`を追加しました。
- macOS・Linuxの`python3`利用、Skill導入後の再起動・再検証、実在しないAGENTSパスの
  自己申告を読込成功とみなさない検証ルールを追加しました。
- 新環境でルートAGENTS生成、repoパス置換、Skill導入、セットアップ検証をまとめて行う
  dry-run付きの`scripts/setup_environment.py`を追加しました。
- 既存ルートAGENTSは自動上書きせず、互換性がない場合に手動統合を案内するようにしました。
