---
name: verify-agent-spec-setup
description: agent-specの導入状態を読み取り専用で診断し、正本repoの必須ファイル、環境ルートAGENTSの参照とプレースホルダー置換、導入済みSkillの同期、Codexでの実行時検出を確認する。新しいPC・コンテナ・クラウド環境へのセットアップ後、ルート指示やSkillが正しく使えるか確認する依頼、または導入不良の切り分けに使用する。agent-spec文書自体の更新にはmaintain-agent-specを使用する。
---

# agent-specセットアップを検証する

## 検証対象を決める

1. agent-specのクローン先を特定する。
2. 対象環境のルート`AGENTS.md`を特定する。指定がなければCodexホームの`AGENTS.md`を
   候補にする。
3. Skillの導入先を特定する。ユーザー共通なら`$HOME/.agents/skills`、repo固有なら
   `<TARGET_REPOSITORY>/.agents/skills`を候補にする。
4. 汎用プロファイルか`personal`プロファイルかを確認する。

## ファイル状態を検証する

Skillディレクトリを基準に`scripts/verify_setup.py`を実行する。スクリプトは読み取り専用で、
repo構造、ルートAGENTS、Skill同期を検査する。

```text
python <THIS_SKILL_DIR>/scripts/verify_setup.py \
  --repo <AGENT_SPEC_REPOSITORY_PATH> \
  --root-agents <ROOT_AGENTS_PATH> \
  --installed-skills-dir <INSTALLED_SKILLS_DIRECTORY> \
  --expect-profile personal \
  --require-skills
```

汎用プロファイルでは`--expect-profile`を省略する。Skill導入を必須にしない環境では
`--require-skills`を省略する。複数の導入先は`--installed-skills-dir`を繰り返す。

結果を次の層に分ける。

- repo整合性: 必須文書、UTF-8、リンク、Skill構造
- ルーター整合性: 未置換プレースホルダー、必須参照、実際のrepoパス
- Skill整合性: 必須Skillの存在、正本との内容差、古いコピー
- 実行時検出: 新しいセッションでのAGENTS読込とSkill一覧

## 実行時検出を確認する

1. 可能なら対象環境で新しいセッションまたは独立エージェントを開始する。
2. 読み込んだAGENTSファイルのパスと、利用可能なSkill名だけを列挙させる。
3. 期待するルートAGENTS、プロジェクトAGENTS、`maintain-agent-spec`、
   `verify-agent-spec-setup`が見えるか照合する。
4. 新しいセッションを使えない場合は、ファイル検証と実行時検出を分け、後者を未確認と
   報告する。継承済みコンテキストだけで自動読込成功と判定しない。

## 報告する

1. PASS、WARN、FAILを層ごとにまとめる。
2. FAILごとに対象パス、期待値、実際値、最小の修正案を示す。
3. 診断依頼だけならファイルを修正しない。修正を依頼された場合は`maintain-agent-spec`または
   対象環境の指示に従って別工程として実施する。
4. 実行したコマンド、未確認の層、VOICEVOX通知結果を報告する。
