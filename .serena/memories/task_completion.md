# Task Completion

1. `docs/MAINTENANCE.md` の分類、同期、環境非依存性、引き渡し条件を満たす。
2. ルートAGENTS、README、アーキテクチャ、テンプレート、関連プロファイルの参照整合を確認。
3. 個人設定が `instructions/core/` へ混入していないこと、ベンダー固有機能が `adapters/` に分離されていることを確認。
4. 全MarkdownについてUTF-8、末尾空白、競合マーカー、壊れた相対参照を確認。
5. プレースホルダーがテンプレート上の意図した箇所だけに残ることを確認。
6. `mem:` 参照先が一覧に存在することをSerena CLIまたはMCPで確認。
7. Skill変更時は `python scripts/validate_skills.py` と追加したSkill内スクリプトを実行。
8. `python scripts/validate_repository.py` を実行。
9. `git status --short --untracked-files=all` で意図したファイルだけが変更されたことを確認し、commit・push・PRの実施有無を報告。
10. VOICEVOXを `speaker=29`、`speedScale=1.1` で試行し、失敗時はテキストで報告。
