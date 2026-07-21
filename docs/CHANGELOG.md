# 変更履歴

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
