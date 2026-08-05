# 個人プロファイル

このファイルは、旧ルートから個人プロファイルを直接参照する環境との互換用入口です。
新しい個人用環境ルートは、常時設定を `ROOT_AGENTS_TEMPLATE.md` に直接持つため、通常タスクで
本ファイルを追加読込しません。

- 日本語で応答します。
- ユーザーがコピーして実行するコマンドは、1コマンドにつき1行で提示します。
- 将来も有効なプロジェクト固有の規則・判断や、利用者に影響する変更履歴は、作業中に
  適切な永続記録へ作成・更新します。
- 完了前に、正確性、スコープ、検証結果、意図しない変更を短く確認します。

## 条件付きで読む

- UnityまたはC#作業: [`unity-csharp.md`](unity-csharp.md)
- バックエンドを伴うWebサービスの新規作成: [`web-development.md`](web-development.md)
- Unity操作・検証、外部SDK調査、Web UI操作、GitHub上の作業でツール選択が必要な場合、
  または明示的な音声通知:
  [`mcp-and-voicevox.md`](mcp-and-voicevox.md)
- 永続性のある規則・判断・変更履歴が生じる作業:
  [`project-recording.md`](project-recording.md)

`communication.md`は旧構成との互換用であり、新しい環境ルートでは常時読みません。
