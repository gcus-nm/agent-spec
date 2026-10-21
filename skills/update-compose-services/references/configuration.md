# 設定とv1の境界

設定はassetsの全キーを必須とする。repoとenv_file、CLIのconfig/plan/stateは利用環境の絶対パス、remote_urlは資格情報を
含まない正確なURL、composeとsource_pathsはrepoルート相対とする。branch/context/project/
remoteは英数字・ピリオド・ハイフン・下線の識別子に限る。環境から暗黙に選ばず明示する。
Dockerの接続先contextは利用者が別途確認し、誤った本番接続を避ける。

- services: 空を拒否するサービスallowlist。既存の全サービスが各1コンテナで稼働していること。
- source_paths: 更新を許すコードファイル/ディレクトリ。各変更の意味をレビューする。
- code_reviewed_no_migrations: DB migration、起動時のデータ変換や不可逆操作がないという
  コードレビューの結果。falseのままでは実行しない。機械的なmigration名検出だけに頼らない。
- rollback_allowed: 計画に含めて事前承認する旧imageのみの復旧許可。データ復元ではない。

既存コンテナのCompose config-hashと現在の`config --hash`を照合し、不一致なら停止する。
全サービスに明示imageを要求する。ComposeファイルのGit差分を拒否し、展開後モデルのハッシュもapply前後で照合する。
ネットワーク、権限、volume、portを含む構成変更は別作業。各対象に明示imageとローカルbuildを
要求し、build contextはrepoルート限定、Dockerfileはrepo内の通常ファイル限定とする。共有image tag、bind mount、profile、include、
extends、develop、provider、特殊build、未知のserviceキー、submodule、symlink、スケール、
oneoffは停止する。保守的なため無害な未知キーも停止する。対象外もrunning/healthyが前提。
Compose以外の外部設定を変更する作業、DB migration、コードbind mountはv1非対応。

inspectはrefs/作業ツリー/Dockerを変更しない。--planを指定した場合だけ新規の私有計画を出力する。
fetchはrefs変更を伴う独立操作。applyは計画のSHA、設定、envハッシュ、コンテナ基準状態を
再確認し、承認SHAだけへffする。計画後のdirty/untracked、branch、分岐、refs変化は停止する。
既存Git操作中も停止する。Git hookは空の一時ディレクトリを指定して実行しない（`/dev/null`に依存しない）。
ホスト絶対パスの照合はWindowsではdrive/UNC、区切り文字、大小文字を正規化し、
相対driveパスを拒否する。source_paths/composeは両OSで共通のスラッシュ区切りのGit相対パスを
使い、drive、UNC、backslash、親参照、NTFS alternate data streamを拒否する。
Git/Docker出力はUTF-8で取得し、PowerShellのBOM付きUTF-8 JSONも受け付ける。

apply/rollback/fetchはGit common dirの非待機ロックを共有する。同repoの二重実行を拒否する。Linuxではfcntl、Windowsではmsvcrtの非待機byte-range lockを
使う。ロックは必ずbyte 0を取得・解放し、正常終了・例外・プロセス終了でOSが解放する。
ロックファイルは削除せず再利用する。ネットワークファイルシステム上での排他はv1未検証のため
repoとGit common dirはローカルディスクへ置く。
他ツール・別cloneから同じDocker projectを操作する処理はロックできないため、実行中は
運用側でも排他する。外部による同時編集とDocker操作を完全にトランザクション化できない。

旧image IDを専用backup tagでも保持し、全対象をbuildしてから対象名を付けた
`up -d --no-deps --no-build --pull never --force-recreate --wait`を行う。
DockerfileのRUNやentrypointは任意コードなので承認前にレビューする。buildは依存取得の
ネットワークアクセスを伴い得る。旧imageの自動削除はしない。
healthcheckがある場合はhealthy、ない場合は短い間隔のrunning確認に留まり、業務上の正常性を
保証しない。運用上必要な非機密の機能確認も行う。

build失敗でもGitは承認SHAまで進み、タグやbuild成果物が残り得る。recreate/health失敗では
一部サービスだけ更新され得る。失敗をデータの復旧と取り違えず、stateと現状を確認する。
rollbackは同じ構成・SHAのまま承認されたサービスのtagを旧image IDへ戻し、build/pullせず対象のみ
recreateする。データ、Git、秘密ファイルは戻さない。失敗時の自動rollbackはしない。

plan/state/configはローカルの私有成果物であり、共有repoへ追加しない。秘密値を計画へ格納せず
envと展開モデルはハッシュのみ残す。外部コマンドの診断は一律抑制するため、停止後の調査も
必要項目だけ読み、秘密値や展開設定をログへ転記しない。

確認した一次資料（2026-10-21）:

- [Docker Compose up](https://docs.docker.com/reference/cli/docker/compose/up/)
- [Docker Compose config](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Git merge](https://git-scm.com/docs/git-merge)


WindowsではPythonのmode=0600だけでNTFS ACLを制限できない。config/plan/stateはあらかじめ
利用者だけにアクセスを限定したGit管理外ディレクトリへ置く。ACLを設定・変更する外部操作を
ヘルパーが勝手に行わない。実env値はplan/stateへ含めない。Windows実機・実サービス適用は
未実施で、Linuxの統合テストとWindows固有処理の標準ライブラリmockテストで確認する。

Windows APIの確認先（2026-10-21）:

- [Python msvcrt locking](https://docs.python.org/3/library/msvcrt.html)
- [Python pathlib](https://docs.python.org/3/library/pathlib.html)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)


ローカル検証はrepoルートから次を実行する（実env/Docker daemon不要）。Linuxでは一時Gitと
fake Docker実行ファイルの統合テストも含む。WindowsではPOSIX用fake実行ファイルの統合テストを
skipし、WindowsCompatibilityTestsのmockテストを実行する。Windows mockはbyte 0の
非待機取得・競合・解放・再利用、drive/UNC・区切り・大小文字、argv/環境、UTF-8 BOMを確認する。

```text
python -m unittest discover -s skills/update-compose-services/scripts/tests -v
```

state更新は既存symlink/非通常ファイルを拒否し、同じ私有ディレクトリの一時ファイルを
閉じてからatomic replaceする。既存ファイルをtruncateせず、symlink先へ書き込まない。
