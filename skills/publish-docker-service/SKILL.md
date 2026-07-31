---
name: publish-docker-service
description: 既存のDocker Compose WebサービスをOCI Relay Control経由で安全に公開、更新、停止する。FQDN、固定Dockerネットワークエイリアス、コンテナポートを使ったWebルートの追加、`onprem-relay-ingress`への接続、公開Origin・認証・秘密値・DNS・TLS・ヘルスチェックの検証を依頼されたときに使用する。生のTCP/UDPゲーム経路、Dockerを使わないサービス、一般的なクラウドデプロイだけの依頼には使用しない。
---

# Dockerサービスを公開する

既存サービスのローカル運用を維持しながら、OCI Relay Controlの共有Traefikへ安全に接続する。
公開操作は認証と秘密値の検証後に行い、設定した事実ではなく外部HTTPS応答を完了条件にする。

## 入力を確定する

次の値をコード、Compose、既存の命名規則から特定する。安全に一意に推定できない値だけを
ユーザーへ確認する。ただし、個人データや非公開データを持つサービスの公開FQDNは、
命名規則から推定できても正確な値を示してユーザーの明示承認を得る。

- 対象リポジトリとComposeファイル
- Composeサービス名とHTTPコンテナポート
- 公開FQDN
- `onprem-relay-ingress`上の固定エイリアス
- Relay ControlのURLと認証用`.env`の場所
- 公開後に確認できるヘルスチェックまたは非機密API
- Relay側の専用Basic認証を使うかと、資格情報を保存するGit管理外ファイル

## 1. 現状を調べる

1. 対象に近い`AGENTS.md`、既存差分、Compose、`.env.example`、READMEを読む。
2. 実`.env`は必要なキーだけを読み、秘密値を表示しない。
3. 認証、セッションCookie、Origin検証、アップロード上限、ヘルスチェックを確認する。
4. `docker compose ps -a`と既存ネットワークを読み取りで確認する。
5. 公開FQDNの既存DNSとRelay Controlの既存Webルートを確認し、重複作成を避ける。

## 2. 公開前の安全条件を満たす

次を満たすまでWebルートを有効化しない。

- 蔵書、管理画面、個人データなどの非公開情報をサーバー側認証が保護している。
- 初期設定が完了し、既定または例示パスワードでログインできない。
- JWT、Cookie署名鍵、暗号化鍵など、アプリが要求する秘密値が空や例示値ではない。
- 正式な公開URLを設定へ反映し、HTTPS用Secure CookieとOrigin検証が有効になる。
- 個人データや非公開データを持つ場合、正確な公開FQDNをユーザーが明示承認している。
- Relay側Basic認証を使う場合、管理画面の資格情報を流用せず、ルート専用値を自動生成する。
- 認証がないサービスでは、上流アクセスプロキシなどの保護方針をユーザーと確認する。

安全条件を満たせない場合は、Compose変更と無効ルートの下書きまでに留める。秘密値を
回答、ログ、パッチ、コミットへ出さない。

## 3. Composeを共有ネットワークへ接続する

サービス固有ネットワークを保持し、公開対象サービスだけを外部ネットワークへ追加する。
既存のホスト`ports`は、明示依頼がなければ削除しない。

```yaml
services:
  app:
    expose:
      - "3000"
    networks:
      default:
      relay-ingress:
        aliases:
          - app-service

networks:
  default:
  relay-ingress:
    external: true
    name: onprem-relay-ingress
```

次も同じ変更単位で行う。

- 公開Originを`https://<FQDN>`へ変更する。
- プロキシ信頼設定は、接続元CIDRを実際に検証する実装である場合だけ設定する。
- FQDN、エイリアス、ポート、公開経路、停止方法をREADMEへ記録する。
- プロジェクトの恒久運用が変わる場合は`AGENTS.md`、時系列の変更はCHANGELOGへ記録する。

## 4. アプリを検証して起動する

プロジェクト指示のテスト、リント、ビルドを実行してから、次を確認する。

1. `docker compose config --quiet`が成功する。
2. `docker compose up -d --build`が成功する。
3. 対象コンテナがhealthyまたは安定してrunningになる。
4. `docker inspect`で固定エイリアスが`onprem-relay-ingress`に存在する。
5. 共有ネットワーク内から`http://<alias>:<port>`へ到達できる。
6. ローカル経路を維持する要件がある場合は、その応答も確認する。

## 5. Relay ControlへWebルートを反映する

まず同梱スクリプトを読み取りで実行し、既存状態を確認する。

```text
python <SKILL_DIRECTORY>/scripts/relay_web_route.py --base-url <RELAY_CONTROL_URL> --env-file <RELAY_DASHBOARD_ENV> status --hostname <FQDN>
```

`ensure`は既定でdry-runとする。FQDN、エイリアス、ポート、変更内容を確認する。

```text
python <SKILL_DIRECTORY>/scripts/relay_web_route.py --base-url <RELAY_CONTROL_URL> --env-file <RELAY_DASHBOARD_ENV> ensure --name <NAME> --hostname <FQDN> --docker-alias <ALIAS> --container-port <PORT> --description <DESCRIPTION> --enabled
```

個人データを扱うWebサービスを二重保護する場合は、専用Basic認証とGit管理外の保存先を
指定する。Relay Controlが256ビット相当のパスワードを自動生成し、スクリプトは一度だけ
返る平文を指定ファイルへ保存する。資格情報の値は標準出力へ表示しない。

```text
python <SKILL_DIRECTORY>/scripts/relay_web_route.py --base-url <RELAY_CONTROL_URL> --env-file <RELAY_DASHBOARD_ENV> ensure --name <NAME> --hostname <FQDN> --docker-alias <ALIAS> --container-port <PORT> --description <DESCRIPTION> --basic-auth-username <USERNAME> --basic-auth-credentials-file <GIT_IGNORED_ENV> --enabled
```

公開前の安全条件を再確認してから、明示的に適用・公開する。

```text
python <SKILL_DIRECTORY>/scripts/relay_web_route.py --base-url <RELAY_CONTROL_URL> --env-file <RELAY_DASHBOARD_ENV> ensure --name <NAME> --hostname <FQDN> --docker-alias <ALIAS> --container-port <PORT> --description <DESCRIPTION> --basic-auth-username <USERNAME> --basic-auth-credentials-file <GIT_IGNORED_ENV> --enabled --apply --publish
```

スクリプトは管理画面とルート専用Basic認証の値、CSRFトークンを表示せず、プレビュー内の
Hostルール、転送先、Basic認証ミドルウェアを検証してから`PUBLISH`する。`--apply`なしでは
Relay Controlを変更しない。資格情報を失った場合は`--rotate-basic-auth`で再生成する。

## 6. DNS、TLS、外部応答を検証する

1. FQDNのAレコードがOCI予約IPv4へ解決することを確認する。
2. 現行リレーがIPv4専用ならAAAAレコードを追加しない。
3. DNS伝播前のACME失敗と、伝播後の失敗を区別する。
4. 必要な場合だけGateway Traefikを限定再起動し、証明書取得を再試行する。
5. 最終確認ではTLS検証を無効化せず、公開URL、ヘルスAPI、ログイン保護を確認する。
   Basic認証を有効にした場合は、資格情報なしの`401`と正しい資格情報での成功を両方確認する。
6. Relay Controlの状態、生成設定、実際のHTTP応答が一致しない場合は完了扱いにしない。

## 公開を停止する

同梱スクリプトでdry-run後に無効化し、公開まで反映する。

```text
python <SKILL_DIRECTORY>/scripts/relay_web_route.py --base-url <RELAY_CONTROL_URL> --env-file <RELAY_DASHBOARD_ENV> disable --hostname <FQDN> --apply --publish
```

停止後も旧ルートが応答する場合は、生成設定とTraefikログを確認する。ファイル監視エラーで
旧設定が残る場合だけ、影響を説明してGateway Traefikを限定再起動する。

## 引き渡す

次を簡潔に報告する。

- 公開URLと現在の有効・無効状態
- Compose、公開Origin、ドキュメントの主要変更
- 実行したテスト、ビルド、ヘルス、DNS、TLS、外部HTTP検証
- 秘密値を表示していないこと
- 未解決のセキュリティ条件、手動DNS作業、既知の運用制約
