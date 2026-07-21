# GitHub Copilot

- リポジトリ共通: `.github/copilot-instructions.md`
- パス固有: `.github/instructions/<name>.instructions.md`
- エージェント指示: `AGENTS.md`
- 製品面やIDEにより対応形式が異なるため、対応表を確認します。

このリポジトリの汎用文書はそのまま保持し、Copilotで必ず適用したい短い規則だけを
`.github/copilot-instructions.md` へ置くか、対応する環境では `AGENTS.md` を入口にします。

公式:

- [Adding repository custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
- [Custom instruction support](https://docs.github.com/en/copilot/reference/custom-instructions-support)
