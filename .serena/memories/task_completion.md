# Task Completion

1. `docs/MAINTENANCE.md` の分類、同期、環境非依存性、引き渡し条件を満たす。
2. ルートAGENTS、README、アーキテクチャ、テンプレート、関連プロファイルを確認し、
   条件付き指示へ入口または索引から到達できることを確認。
3. 個人設定が `instructions/core/` へ混入していないこと、ベンダー固有機能が `adapters/` に分離されていることを確認。
4. 全MarkdownについてUTF-8、末尾空白、競合マーカー、壊れた相対参照を確認。
5. プレースホルダーがテンプレート上の意図した箇所だけに残ることを確認。
6. `mem:` 参照先が一覧に存在することをSerena CLIまたはMCPで確認。
7. Skill変更時は `python scripts/validate_skills.py` と追加したSkill内スクリプトを実行。
8. Skill導入処理の変更時は`scripts/install_skills.py`のdry-run、適用、再実行、既存差分拒否を一時ディレクトリで確認。
9. 初回セットアップ処理の変更時は`scripts/setup_environment.py`のdry-run、適用、再実行、既存ルートAGENTS保持を一時ディレクトリで確認。
10. `python scripts/validate_repository.py` を実行。
11. `git status --short --untracked-files=all` で意図したファイルだけが変更されたことを確認し、commit・push・PRの実施有無を報告。
12. VOICEVOXは、ユーザー要求、対応Skill、長時間通知設定のいずれかで明示的に有効な場合だけ試行する。
