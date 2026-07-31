# Skillカタログ

このディレクトリは、複数環境で再利用するSkillの正本です。各Skillは
`skills/<skill-name>/SKILL.md`を必須とし、必要な場合だけ`agents/`、`scripts/`、
`references/`、`assets/`を持ちます。

Skillディレクトリ内には、利用時に不要なREADME、変更履歴、導入ガイドを置きません。
横断的な導入・更新・検証手順は [`docs/SKILL_MANAGEMENT.md`](../docs/SKILL_MANAGEMENT.md)
を正本とします。

## 管理中のSkill

| Skill | 用途 | 主な利用範囲 |
|---|---|---|
| [`check-codex-reset-credits`](check-codex-reset-credits/SKILL.md) | Codexの利用可能なリセット権と各有効期限をBashから安全に確認する | macOS・Linux・WSLでのアカウント確認 |
| [`maintain-agent-spec`](maintain-agent-spec/SKILL.md) | 指示の導線を含め、このリポジトリの仕様を分類、更新、検証する | 仕様文書の更新 |
| [`publish-docker-service`](publish-docker-service/SKILL.md) | Docker Compose WebサービスをOCI Relay Control経由で安全に公開・停止する | Windows Docker Desktop上の自己ホストWebサービス |
| [`verify-agent-spec-setup`](verify-agent-spec-setup/SKILL.md) | ルートAGENTS、必須文書、導入済みSkill、実行時検出を診断する | 新環境のセットアップ確認 |

追加時は [`templates/SKILL_REQUEST.md`](../templates/SKILL_REQUEST.md) で利用例と起動境界を
具体化し、`python scripts/validate_repository.py`を実行してください。
