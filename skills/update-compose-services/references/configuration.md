# 設定とv2の境界

設定はassetsの全キーを必須とする。repoとenv_file、CLIのconfig/plan/stateは利用環境の絶対パス、remote_urlは資格情報を
含まない正確なURL、composeとsource_pathsはrepoルート相対とする。branch/context/project/
remoteは英数字・ピリオド・ハイフン・下線の識別子に限る。環境から暗黙に選ばず明示する。
Dockerの接続先contextは利用者が別途確認し、誤った本番接続を避ける。

- target_sha: 承認した40桁16進のcommit SHA。remote branchの参照先との一致を必須とする。
- services: 空を拒否するサービスallowlist。各対象は既存の1コンテナがrunningで、healthcheckが
  ある場合はhealthyであること。対象外も各1コンテナを要求するが、正常終了した一回限りの
  サービスなどの停止状態はそのまま記録し、適用・復旧時に変化していないことを確認する。
- source_paths: 更新を許すコードファイル/ディレクトリ。各変更の意味をレビューする。
- code_reviewed_no_migrations: DB migration、起動時のデータ変換や不可逆操作がないという
  コードレビューの結果。falseのままでは実行しない。機械的なmigration名検出だけに頼らない。
- rollback_allowed: 計画に含めて事前承認する旧imageのみの復旧許可。データ復元ではない。

診断は空の一時envを明示して`config --no-interpolate --no-env-resolution --no-normalize --no-path-resolution --format json`を使う。
未展開のportやpathを正規化しない。対象volumeは名前付きだけを許し、bindと匿名volumeを拒否する。
実envの内容や展開済秘密値を取得せず、未展開のCompose構造のハッシュをapply前後で照合する。
Docker inspectはidentity、状態、config-hash等の必要なラベル、read_only、tmpfs、mount、network、
port等の非秘密項目だけをformatで取得する。環境変数やConfig全体を取得しない。
既存config-hashラベルは基準状態との比較に使い、対象の再作成後も一致を確認する。
秘密を展開する`config --hash`は実行しない。

ComposeファイルのGit差分、ネットワーク、権限、volume、portを含む構成変更は別作業とする。
既存のread_onlyとtmpfsは変更せず許容する。各対象にはローカルbuildを要求し、build contextは
repoルート限定、Dockerfileはrepo内の通常ファイル限定とする。明示imageは未展開のリテラル値を
使う。image未指定のbuildサービスはComposeのproject-serviceタグを導出し、現コンテナのimage参照と
一致することを確認する。対象と共有するimage tag、対象のbind mount、profile、include、extends、
develop、provider、特殊build、未知のserviceキー、submodule、symlink、スケール、oneoffは停止する。
対象外の既存Docker socket等のbind mountは、対象外コンテナの基準状態との一致を条件に保持する。
Compose以外の外部設定を変更する作業、DB migration、対象コードのbind mountは非対応。

inspectはrefs/作業ツリー/Dockerを変更しない。--planを指定した場合だけ新規の私有計画を出力する。
fetchはrefs変更を伴う独立操作。applyは計画のSHA、設定、env参照先のメタデータ、コンテナ基準状態を
再確認し、承認SHAだけへffする。計画後のdirty/untracked、branch、分岐、refs変化は停止する。
既存Git操作中も停止する。Git hookは空の一時ディレクトリを指定して実行しない（`/dev/null`に依存しない）。
rebase中はGitが解決した`rebase-merge`/`rebase-apply`の存在で判定する。完了後に残ることのある
`REBASE_HEAD`単独では停止せず、参照を削除・変更しない。他の操作中マーカーは引き続き停止する。
ホスト絶対パスの照合はWindowsではdrive/UNC、区切り文字、大小文字を正規化し、
相対driveパスを拒否する。source_paths/composeは両OSで共通のスラッシュ区切りのGit相対パスを
使い、drive、UNC、backslash、親参照、NTFS alternate data streamを拒否する。
Git/Docker出力はUTF-8で取得し、PowerShellのBOM付きUTF-8 JSONも受け付ける。

apply/rollback/fetchはGit common dirの非待機ロックを共有する。同repoの二重実行を拒否する。Linuxではfcntl、Windowsではmsvcrtの非待機byte-range lockを
使う。ロックは必ずbyte 0を取得・解放し、正常終了・例外・プロセス終了でOSが解放する。
ロックファイルは削除せず再利用する。ネットワークファイルシステム上での排他は未検証のため
repoとGit common dirはローカルディスクへ置く。
他ツール・別cloneから同じDocker projectを操作する処理はロックできないため、実行中は
運用側でも排他する。envやシェル環境の変更も止める。外部による同時編集とDocker操作を
完全にトランザクション化できない。

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

plan/state/configはローカルの私有成果物であり、共有repoへ追加しない。実envをバイト列で読まず、
参照先のsize、mtime、ctime、ファイルidentity等のメタデータだけを記録する。秘密値や展開済モデルは
保存しない。build/upでは既存env参照を通常どおりComposeへ渡し、出力を抑制する。

この診断はv1の秘密を含む内容ハッシュと同じ保証を持たない。メタデータを維持するenvの編集や、
計画前からある実envと稼働コンテナの実効設定の不一致、シェル環境による実効値の違いは証明できない。
計画から適用・復旧の終了までenvとシェル環境を変えないことを運用条件とする。停止後の調査も
必要項目だけ読み、秘密値や展開設定をログへ転記しない。

確認した一次資料（2026-10-21）:

- [Docker Compose up](https://docs.docker.com/reference/cli/docker/compose/up/)
- [Docker Compose config](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Docker inspect format](https://docs.docker.com/reference/cli/docker/inspect/)
- [Git merge](https://git-scm.com/docs/git-merge)


WindowsではPythonのmode=0600だけでNTFS ACLを制限できない。config/plan/stateはあらかじめ
利用者だけにアクセスを限定したGit管理外ディレクトリへ置く。ACLを設定・変更する外部操作を
ヘルパーが勝手に行わない。実env値はplan/stateへ含めない。Windowsの既存構成への限定適用と
health確認は実機で実施済みだが、全構成の互換性や実サービスでのrollbackまでは検証していない。
両OSで実Git・mock Dockerの秘密非取得と限定apply/rollbackテストを実行できる。
これに加え、Linuxのfake実行ファイル統合テストとWindows固有処理の標準ライブラリmockテストを持つ。

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
