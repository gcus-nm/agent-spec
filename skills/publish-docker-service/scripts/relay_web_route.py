#!/usr/bin/env python3
"""Safely inspect and mutate OCI Relay Control web routes."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib import error, parse, request


ROUTE_FIELDS = ("name", "hostname", "docker_alias", "container_port", "description")
HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
ALIAS_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")
BASIC_AUTH_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class RelayError(RuntimeError):
    """A safe-to-display Relay Control error."""


def load_env(path: Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if path is None:
        return values
    if not path.is_file():
        raise RelayError(f"認証用envファイルがありません: {path}")
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def credentials(env_file: Path | None) -> tuple[str, str]:
    values = load_env(env_file)
    username = os.environ.get("RELAY_DASHBOARD_USERNAME") or values.get(
        "DASHBOARD_USERNAME", ""
    )
    password = os.environ.get("RELAY_DASHBOARD_PASSWORD") or values.get(
        "DASHBOARD_PASSWORD", ""
    )
    if not username or not password:
        raise RelayError(
            "Relay Control認証情報がありません。--env-fileまたは"
            "RELAY_DASHBOARD_USERNAME/RELAY_DASHBOARD_PASSWORDを設定してください。"
        )
    return username, password


def normalize_base_url(value: str) -> str:
    parsed = parse.urlsplit(value.rstrip("/"))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RelayError("--base-urlにはhttpまたはhttpsのURLを指定してください。")
    if parsed.username or parsed.password:
        raise RelayError("--base-urlへ認証情報を埋め込まないでください。")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise RelayError("--base-urlにはパス、クエリ、フラグメントを含めないでください。")
    return value.rstrip("/")


class RelayClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = normalize_base_url(base_url)
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
        self.authorization = f"Basic {encoded}"
        self.csrf_token = ""

    def call(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Authorization": self.authorization,
        }
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if method != "GET":
            if not self.csrf_token:
                self.state()
            headers["X-Relay-CSRF"] = self.csrf_token
        req = request.Request(
            f"{self.base_url}{path}", method=method, headers=headers, data=data
        )
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read()
        except error.HTTPError as exc:
            body = exc.read()
            message = f"HTTP {exc.code}"
            try:
                decoded = json.loads(body.decode("utf-8"))
                if isinstance(decoded, dict) and isinstance(decoded.get("error"), str):
                    message = f"HTTP {exc.code}: {decoded['error']}"
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            raise RelayError(message) from exc
        except error.URLError as exc:
            raise RelayError(f"Relay Controlへ接続できません: {exc.reason}") from exc
        if not body:
            return {}
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RelayError("Relay ControlがJSON以外を返しました。") from exc
        if not isinstance(decoded, dict):
            raise RelayError("Relay Controlの応答形式が不正です。")
        return decoded

    def state(self) -> dict[str, Any]:
        state = self.call("GET", "/api/state")
        token = state.get("csrf_token")
        if not isinstance(token, str) or not token:
            raise RelayError("Relay ControlのCSRFトークンを取得できません。")
        self.csrf_token = token
        return state

    def routes(self) -> list[dict[str, Any]]:
        payload = self.call("GET", "/api/web-routes")
        routes = payload.get("web_routes")
        if not isinstance(routes, list):
            raise RelayError("Relay ControlのWebルート一覧形式が不正です。")
        return [item for item in routes if isinstance(item, dict)]


def public_route(route: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "name",
        "hostname",
        "docker_alias",
        "container_port",
        "description",
        "basic_auth_enabled",
        "basic_auth_username",
        "state",
        "desired_enabled",
    )
    return {key: route.get(key) for key in keys if key in route}


def select_route(
    routes: list[dict[str, Any]], name: str | None, hostname: str | None
) -> dict[str, Any]:
    matches = [
        route
        for route in routes
        if (not name or route.get("name") == name)
        and (not hostname or route.get("hostname") == hostname)
    ]
    if len(matches) != 1:
        raise RelayError(f"対象Webルートは1件必要ですが、{len(matches)}件でした。")
    return matches[0]


def normalize_hostname(value: str) -> str:
    hostname = value.strip().lower().rstrip(".")
    if not HOSTNAME_PATTERN.fullmatch(hostname):
        raise RelayError("FQDNの形式が不正です。")
    return hostname


def valid_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ポートは整数で指定してください。") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("ポートは1〜65535で指定してください。")
    return port


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def validate_credentials_path(path: Path) -> None:
    parent = path.expanduser().resolve().parent
    if not parent.is_dir():
        raise RelayError(f"Basic認証情報の保存先ディレクトリがありません: {parent}")
    if path.exists() and not path.is_file():
        raise RelayError(f"Basic認証情報の保存先がファイルではありません: {path}")


def write_credentials(path: Path, credentials_: object) -> Path:
    if not isinstance(credentials_, dict):
        raise RelayError("Relay Controlが一度限りのBasic認証情報を返しませんでした。")
    username = credentials_.get("username")
    password = credentials_.get("password")
    if (
        not isinstance(username, str)
        or not BASIC_AUTH_USERNAME_PATTERN.fullmatch(username)
        or not isinstance(password, str)
        or len(password) < 40
        or any(character in password for character in "\r\n")
    ):
        raise RelayError("Relay Controlが返したBasic認証情報の形式が不正です。")

    destination = path.expanduser().resolve()
    validate_credentials_path(destination)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            stream.write(f"BASIC_AUTH_USERNAME={username}\n")
            stream.write(f"BASIC_AUTH_PASSWORD={password}\n")
        os.replace(temporary, destination)
        try:
            os.chmod(destination, 0o600)
        except OSError:
            pass
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return destination


def preview_and_publish(
    client: RelayClient,
    name: str,
    hostname: str,
    enabled: bool,
    alias: str | None,
    port: int | None,
    basic_auth_enabled: bool,
    publish: bool,
) -> tuple[bool, bool]:
    preview = client.call("POST", "/api/web-routes/preview", {})
    preview_data = preview.get("preview")
    if not isinstance(preview_data, dict):
        raise RelayError("Webルートプレビュー形式が不正です。")
    config = preview_data.get("config")
    if not isinstance(config, str):
        raise RelayError("Webルートプレビューに生成設定がありません。")
    host_rule = f"Host(`{hostname}`)"
    if enabled:
        backend = f"http://{alias}:{port}"
        if host_rule not in config or backend not in config:
            raise RelayError("プレビューに期待したHostルールまたは転送先がありません。")
        auth_middleware = f"ui-web-{name}-auth"
        if basic_auth_enabled:
            if (
                auth_middleware not in config
                or "basicAuth:" not in config
                or "usersFile:" not in config
                or "removeHeader: true" not in config
            ):
                raise RelayError("プレビューに期待したBasic認証設定がありません。")
        elif auth_middleware in config:
            raise RelayError("Basic認証を無効にしたルートへ認証設定が残っています。")
    elif host_rule in config:
        raise RelayError("無効化対象のHostルールがプレビューに残っています。")
    if publish:
        client.call("POST", "/api/web-routes/publish", {"confirmation": "PUBLISH"})
    return True, publish


def status_action(client: RelayClient, args: argparse.Namespace) -> None:
    routes = client.routes()
    if args.name or args.hostname:
        routes = [select_route(routes, args.name, args.hostname)]
    emit({"action": "status", "routes": [public_route(route) for route in routes]})


def ensure_action(client: RelayClient, args: argparse.Namespace) -> None:
    hostname = normalize_hostname(args.hostname)
    alias = args.docker_alias.strip().lower()
    if not ALIAS_PATTERN.fullmatch(alias):
        raise RelayError("Dockerエイリアスの形式が不正です。")
    desired = {
        "name": args.name.strip().lower(),
        "hostname": hostname,
        "docker_alias": alias,
        "container_port": args.container_port,
        "description": args.description.strip(),
    }
    desired_enabled = bool(args.enabled)
    requested_basic_auth: bool | None = None
    requested_basic_auth_username = ""
    if args.basic_auth_username:
        requested_basic_auth = True
        requested_basic_auth_username = args.basic_auth_username.strip()
        if not BASIC_AUTH_USERNAME_PATTERN.fullmatch(requested_basic_auth_username):
            raise RelayError("Basic認証ユーザー名の形式が不正です。")
    elif args.no_basic_auth:
        requested_basic_auth = False
    routes = client.routes()
    candidates = [
        route
        for route in routes
        if route.get("name") == desired["name"] or route.get("hostname") == hostname
    ]
    if len(candidates) > 1:
        raise RelayError("名前とFQDNが別々の既存ルートに一致しています。")
    current = candidates[0] if candidates else None
    changes: list[str] = []
    if current is None:
        changes.append("create")
    elif any(current.get(field) != desired[field] for field in ROUTE_FIELDS):
        changes.append("update")
    if current is None or bool(current.get("desired_enabled")) != desired_enabled:
        changes.append("enable" if desired_enabled else "disable")
    current_basic_auth = bool(current and current.get("basic_auth_enabled"))
    current_basic_auth_username = (
        str(current.get("basic_auth_username", "")) if current else ""
    )
    desired_basic_auth = (
        requested_basic_auth
        if requested_basic_auth is not None
        else current_basic_auth
    )
    desired_basic_auth_username = (
        requested_basic_auth_username
        if requested_basic_auth
        else current_basic_auth_username if desired_basic_auth else ""
    )
    if requested_basic_auth is not None and (
        current_basic_auth != requested_basic_auth
        or (
            requested_basic_auth
            and current_basic_auth_username != requested_basic_auth_username
        )
    ):
        changes.append(
            "enable-basic-auth" if requested_basic_auth else "disable-basic-auth"
        )
    if args.rotate_basic_auth:
        changes.append("rotate-basic-auth")

    credentials_will_be_generated = bool(
        requested_basic_auth
        and (
            current is None
            or not current_basic_auth
            or current_basic_auth_username != requested_basic_auth_username
            or args.rotate_basic_auth
        )
    )
    if args.apply and credentials_will_be_generated:
        if args.basic_auth_credentials_file is None:
            raise RelayError(
                "新しいBasic認証情報の保存には"
                "--basic-auth-credentials-fileが必要です。"
            )
        validate_credentials_path(args.basic_auth_credentials_file)

    if not args.apply:
        desired_output = {
            **desired,
            "desired_enabled": desired_enabled,
            "basic_auth_enabled": desired_basic_auth,
            "basic_auth_username": desired_basic_auth_username,
        }
        emit(
            {
                "action": "ensure",
                "applied": False,
                "changes": changes,
                "credentials_file_required": credentials_will_be_generated,
                "desired": desired_output,
                "existing": public_route(current) if current else None,
            }
        )
        return

    mutation_payload: dict[str, Any] = dict(desired)
    if current is None and requested_basic_auth is None:
        mutation_payload["basic_auth_enabled"] = False
    elif requested_basic_auth is not None:
        mutation_payload["basic_auth_enabled"] = requested_basic_auth
        mutation_payload["basic_auth_username"] = desired_basic_auth_username
        mutation_payload["rotate_basic_auth"] = bool(args.rotate_basic_auth)

    mutation_response: dict[str, Any] | None = None
    if current is None:
        mutation_response = client.call(
            "POST",
            "/api/web-routes",
            {**mutation_payload, "desired_enabled": desired_enabled},
        )
        current = select_route(
            [
                item
                for item in mutation_response.get("web_routes", [])
                if isinstance(item, dict)
            ],
            desired["name"],
            hostname,
        )
    else:
        record_id = parse.quote(str(current["id"]), safe="")
        if any(
            change in changes
            for change in (
                "update",
                "enable-basic-auth",
                "disable-basic-auth",
                "rotate-basic-auth",
            )
        ):
            mutation_response = client.call(
                "PUT",
                f"/api/web-routes/{record_id}",
                mutation_payload,
            )
        if "enable" in changes or "disable" in changes:
            client.call(
                "PUT",
                f"/api/web-routes/{record_id}/enabled",
                {"enabled": desired_enabled},
            )

    credentials_path: Path | None = None
    if credentials_will_be_generated:
        credentials_path = write_credentials(
            args.basic_auth_credentials_file,
            (mutation_response or {}).get("one_time_basic_auth"),
        )

    previewed, published = preview_and_publish(
        client,
        desired["name"],
        hostname,
        desired_enabled,
        alias,
        args.container_port,
        desired_basic_auth,
        args.publish,
    )
    final = select_route(client.routes(), desired["name"], hostname)
    emit(
        {
            "action": "ensure",
            "applied": True,
            "changes": changes,
            "preview_validated": previewed,
            "published": published,
            "basic_auth_credentials_file": (
                str(credentials_path) if credentials_path else None
            ),
            "route": public_route(final),
        }
    )


def toggle_action(
    client: RelayClient, args: argparse.Namespace, enabled: bool
) -> None:
    hostname = normalize_hostname(args.hostname) if args.hostname else None
    route = select_route(client.routes(), args.name, hostname)
    changes = [] if bool(route.get("desired_enabled")) == enabled else [
        "enable" if enabled else "disable"
    ]
    if not args.apply:
        emit(
            {
                "action": "enable" if enabled else "disable",
                "applied": False,
                "changes": changes,
                "route": public_route(route),
            }
        )
        return
    if changes:
        record_id = parse.quote(str(route["id"]), safe="")
        client.call(
            "PUT",
            f"/api/web-routes/{record_id}/enabled",
            {"enabled": enabled},
        )
    previewed, published = preview_and_publish(
        client,
        str(route["name"]),
        str(route["hostname"]),
        enabled,
        str(route["docker_alias"]) if enabled else None,
        int(route["container_port"]) if enabled else None,
        bool(route.get("basic_auth_enabled")),
        args.publish,
    )
    final = select_route(client.routes(), str(route["name"]), str(route["hostname"]))
    emit(
        {
            "action": "enable" if enabled else "disable",
            "applied": True,
            "changes": changes,
            "preview_validated": previewed,
            "published": published,
            "route": public_route(final),
        }
    )


def mutation_flags(parser_: argparse.ArgumentParser) -> None:
    parser_.add_argument(
        "--apply", action="store_true", help="Relay Controlの下書きを変更する"
    )
    parser_.add_argument(
        "--publish", action="store_true", help="プレビュー検証後にTraefikへ反映する"
    )


def target_flags(parser_: argparse.ArgumentParser, required: bool) -> None:
    group = parser_.add_mutually_exclusive_group(required=required)
    group.add_argument("--name", help="Relay Control上のルート名")
    group.add_argument("--hostname", help="公開FQDN")


def build_parser() -> argparse.ArgumentParser:
    parser_ = argparse.ArgumentParser(
        description="OCI Relay ControlのWebルートを安全に確認・変更します。"
    )
    parser_.add_argument(
        "--base-url",
        default="http://127.0.0.1:41800",
        help="Relay Control URL（既定: http://127.0.0.1:41800）",
    )
    parser_.add_argument("--env-file", type=Path, help="Relay Dashboardの.env")
    subparsers = parser_.add_subparsers(dest="action", required=True)

    status = subparsers.add_parser("status", help="Webルートを読み取りで確認する")
    target_flags(status, required=False)

    ensure = subparsers.add_parser("ensure", help="Webルートを作成または更新する")
    ensure.add_argument("--name", required=True)
    ensure.add_argument("--hostname", required=True)
    ensure.add_argument("--docker-alias", required=True)
    ensure.add_argument("--container-port", required=True, type=valid_port)
    ensure.add_argument("--description", default="")
    basic_auth = ensure.add_mutually_exclusive_group()
    basic_auth.add_argument(
        "--basic-auth-username",
        help="専用Basic認証を有効にし、自動生成資格情報をこのユーザー名へ割り当てる",
    )
    basic_auth.add_argument(
        "--no-basic-auth",
        action="store_true",
        help="このWebルートの専用Basic認証を無効にする",
    )
    ensure.add_argument(
        "--rotate-basic-auth",
        action="store_true",
        help="Basic認証パスワードを自動再生成する",
    )
    ensure.add_argument(
        "--basic-auth-credentials-file",
        type=Path,
        help="一度だけ返るBasic認証情報の保存先envファイル",
    )
    state = ensure.add_mutually_exclusive_group(required=True)
    state.add_argument("--enabled", action="store_true")
    state.add_argument("--disabled", action="store_true")
    mutation_flags(ensure)

    for action in ("enable", "disable"):
        toggle = subparsers.add_parser(action, help=f"Webルートを{action}にする")
        target_flags(toggle, required=True)
        mutation_flags(toggle)
    return parser_


def main() -> int:
    parser_ = build_parser()
    args = parser_.parse_args()
    if getattr(args, "publish", False) and not getattr(args, "apply", False):
        parser_.error("--publishには--applyが必要です。")
    if getattr(args, "rotate_basic_auth", False) and not getattr(
        args, "basic_auth_username", None
    ):
        parser_.error(
            "--rotate-basic-authには--basic-auth-usernameが必要です。"
        )
    if getattr(args, "basic_auth_credentials_file", None) and not getattr(
        args, "basic_auth_username", None
    ):
        parser_.error(
            "--basic-auth-credentials-fileには--basic-auth-usernameが必要です。"
        )
    try:
        username, password = credentials(args.env_file)
        client = RelayClient(args.base_url, username, password)
        if args.action == "status":
            status_action(client, args)
        elif args.action == "ensure":
            ensure_action(client, args)
        elif args.action == "enable":
            toggle_action(client, args, True)
        elif args.action == "disable":
            toggle_action(client, args, False)
        else:
            raise RelayError(f"未対応の操作です: {args.action}")
    except RelayError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
