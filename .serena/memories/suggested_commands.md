# Suggested Commands

- 更新前確認: `git status --short --branch`、`git remote -v`。
- リモート比較が必要で権限がある場合: `git fetch`。未コミット変更へ無断のpull/rebase/resetを行わない。
- 全変更確認: `git status --short --untracked-files=all`。
- 追跡済み差分の空白確認: `git diff --check`。未追跡Markdownは別途全ファイルを走査。
- ファイル探索: `Get-ChildItem -Recurse -File`。`rg`が利用可能なら `rg --files` を優先。
- プレースホルダー確認: `Select-String -Path README.md,ROOT_AGENTS_TEMPLATE.md,templates\\*.md -Pattern '<[^>]+>'`。
- Serena参照確認: `serena memories check`。CLIがなければSerena MCPの一覧と `mem:` 参照を照合。
- 個人用ルート配置: `ROOT_AGENTS_TEMPLATE.md`、汎用配置: `templates/ROOT_AGENTS_GENERIC.md` をコピーし、リポジトリパスを置換。
- 他環境への更新依頼: `templates/UPDATE_REQUEST.md` を具体化し、`docs/MAINTENANCE.md` を必須参照にする。
- Skill検証: リポジトリルートで `python scripts/validate_skills.py`。
- repo全体検証: リポジトリルートで `python scripts/validate_repository.py`。
- セットアップ検証: `python skills/verify-agent-spec-setup/scripts/verify_setup.py --repo <repo> --root-agents <AGENTS.md> --installed-skills-dir <skills-dir>`。
- Skill作成依頼: `templates/SKILL_REQUEST.md` で起動例、入出力、リソース、導入範囲を具体化する。
