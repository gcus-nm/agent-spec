---
name: update-compose-services
description: 既存Compose構成を変えず、承認したGit SHAのコードだけを許可サービスへ限定更新する。既存サービスの確認、更新計画、承認後のbuildとrecreate、事前許可された旧imageへの復旧を依頼された場合に使う。Relay・DNS・TLS公開、構成変更、DB migration、新規配備には使わない。
---

# 既存Composeサービスを限定更新する

対象repoのAGENTS.md、既存差分と運用文書を最初に確認する。
[設定と制約](references/configuration.md)を読み、[設定例](assets/deployment.example.json)を
Git管理外の専用ディレクトリへコピーする。Windows PowerShellまたはLinux上のPython 3.10以上、Git、Docker Compose v2を
使う。実サービスをテスト台にしない。

1. repo、remote URL、branch、固定するtarget_sha、Docker context、project、Compose、env参照、サービスallowlistを
   明示する。source_pathsはレビュー済みコードだけへ絞る。DB migration、データ形式変更、
   起動時副作用をコードレビューし、問題がなければcode_reviewed_no_migrationsをtrueにする。
2. `inspect`で既存remote refsから読み取り検査する。refsが古い場合だけ、fetchの影響を説明し
   明示承認を受けて別段階の`fetch`を実行する。inspectはfetchせず、remote branchがtarget_shaと
   一致しなければ停止する。対象外の停止済みコンテナも基準状態として記録し、起動しない。
3. 計画ファイルを作り、SHA、全設定、変更ファイル、対象と対象外、停止時間、旧image復旧範囲を
   人が確認できるよう秘密値を伏せて提示する。表示されたapprovalハッシュを計画全体への承認に使う。
4. 承認後に同じconfig・planと、新規stateパス、approvalを指定してapplyする。applyは再検査し、
   再fetchせず承認SHAへff更新する。build失敗時はrecreateしない。
5. 終了コード0と対象の状態・health、対象外不変を確認する。失敗時は自動再実行せず、
   Git HEAD、image、コンテナの現在状態を秘密値なしで調べる。stateのstartedは部分実行を意味する。
6. rollback_allowedを計画時にtrueとして事前承認した場合だけ、旧imageへのrollbackを実行する。
   データ復元やGit巻き戻しはしない。再発行した計画・承認で失敗を隠さない。

PowerShellでもLinuxでも以下を各1行で実行する。Python 3が`python3`名の場合は読み替える。
空白・日本語を含むパスは各引数を引用符で囲む。PowerShellからはGit/DockerをPATH上の
ネイティブ実行ファイルで利用し、WSLのパスとWindowsのパスを混ぜない。すべてのパスは利用環境で具体化し、共有repoへ実値を保存しない。

```text
python <SKILL_DIRECTORY>/scripts/update_compose_services.py inspect --config <PRIVATE_CONFIG> --plan <NEW_PRIVATE_PLAN>
python <SKILL_DIRECTORY>/scripts/update_compose_services.py fetch --config <PRIVATE_CONFIG>
python <SKILL_DIRECTORY>/scripts/update_compose_services.py apply --config <PRIVATE_CONFIG> --plan <PRIVATE_PLAN> --state <NEW_PRIVATE_STATE> --approve <APPROVAL_HASH>
python <SKILL_DIRECTORY>/scripts/update_compose_services.py rollback --config <PRIVATE_CONFIG> --state <PRIVATE_STATE> --approve <APPROVAL_HASH>
```

inspectの標準出力はSHA、対象名、変更数、承認ハッシュのみ。成功は0、停止は1。
診断は実envの内容、展開済秘密値、コンテナ環境変数を取得しない。Compose構造、非秘密の
コンテナ項目、env参照先のファイルメタデータで変化を検査する。これは秘密値の同一性検証ではない。
計画から適用・復旧の終了まで、他ツールによるenv・シェル環境・対象projectの変更を止める。
build/upだけは既存env参照を通常どおりComposeへ渡す。外部コマンドの出力を表示しない。
計画・状態には端末パスとimage IDがあるため、Git管理外の私有ファイルとして保持する。Linuxは権限0600、Windowsは利用者だけがアクセスできる
NTFS ACLを持つディレクトリを事前に用意する（0600をWindows ACLの代替としない）。

`down`、volume削除、prune、reset、clean、stash、force pushを実行しない。
Relay/DNS/TLSの公開・変更は[公開Skill](../publish-docker-service/SKILL.md)へ引き渡す。
導入は[共通Skill管理](../../docs/SKILL_MANAGEMENT.md)に従い、正本を検証後に必要な範囲へ同期する。
今回の実装だけで本番適用の承認とみなさない。
