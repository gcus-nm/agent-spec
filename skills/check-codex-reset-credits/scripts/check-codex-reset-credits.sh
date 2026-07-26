#!/usr/bin/env bash

set -euo pipefail

readonly ENDPOINT='https://chatgpt.com/backend-api/wham/rate-limit-reset-credits'

auth_file="${CODEX_HOME:-$HOME/.codex}/auth.json"
output_mode='table'

usage() {
  cat <<'EOF'
Usage:
  check-codex-reset-credits.sh [--auth-file PATH] [--json]

Options:
  --auth-file PATH  Codex auth.json path
  --json            Print a normalized JSON response
  -h, --help        Show this help
EOF
}

fail() {
  local exit_code="$1"
  shift
  printf 'エラー: %s\n' "$*" >&2
  exit "$exit_code"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 ||
    fail 3 "必要なコマンドが見つかりません: $1"
}

while (($# > 0)); do
  case "$1" in
    --auth-file)
      (($# >= 2)) || fail 2 '--auth-fileにはパスが必要です。'
      auth_file="$2"
      shift 2
      ;;
    --json)
      output_mode='json'
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      fail 2 "不明なオプションです: $1"
      ;;
  esac
done

require_command curl
require_command jq

[[ -r "$auth_file" ]] ||
  fail 3 "認証ファイルを読み取れません: $auth_file"

access_token="$(
  jq -er '.tokens.access_token | strings | select(length > 0)' "$auth_file"
)" || fail 3 'auth.jsonにアクセストークンがありません。Codexへ再ログインしてください。'

account_id="$(
  jq -r '.tokens.account_id // empty | strings' "$auth_file"
)"

response="$(
  {
    printf 'header = "Authorization: Bearer %s"\n' "$access_token"
    printf 'header = "OpenAI-Beta: codex-1"\n'
    printf 'header = "originator: Codex Desktop"\n'
    if [[ -n "$account_id" ]]; then
      printf 'header = "ChatGPT-Account-ID: %s"\n' "$account_id"
    fi
  } | curl \
    --config - \
    --fail \
    --silent \
    --show-error \
    --max-time 30 \
    --request GET \
    --url "$ENDPOINT"
)" || fail 4 'Codexのリセット権APIから情報を取得できませんでした。'

unset access_token account_id

jq -e '
  (.available_count | type == "number")
  and ((.credits // []) | type == "array")
' >/dev/null <<<"$response" ||
  fail 5 'APIレスポンスの形式が想定と異なります。'

if [[ "$output_mode" == 'json' ]]; then
  jq '{
    available_count,
    credits: [
      (.credits // [])[]
      | {
          status: (.status // "unknown"),
          granted_at: (.granted_at // null),
          expires_at: (.expires_at // null)
        }
    ]
  }' <<<"$response"
  exit 0
fi

available_count="$(jq -r '.available_count' <<<"$response")"
printf '利用可能なリセット権: %s個\n' "$available_count"

if [[ "$(jq -r '(.credits // []) | length' <<<"$response")" == '0' ]]; then
  exit 0
fi

jq -r '
  def local_datetime:
    if . == null or . == "" then
      "不明"
    elif type == "number" then
      localtime | strftime("%Y-%m-%d %H:%M:%S %z")
    else
      . as $original
      | try (
          tostring
          | sub("\\.[0-9]+Z$"; "Z")
          | sub("\\.[0-9]+\\+00:00$"; "Z")
          | sub("\\+00:00$"; "Z")
          | fromdateiso8601
          | localtime
          | strftime("%Y-%m-%d %H:%M:%S %z")
        ) catch $original
    end;

  (.credits // [])[]
  | [
      (.status // "unknown"),
      ((.granted_at // null) | local_datetime),
      ((.expires_at // null) | local_datetime)
    ]
  | @tsv
' <<<"$response" |
  {
    index=0
    while IFS=$'\t' read -r status granted_at expires_at; do
      index=$((index + 1))
      printf '\n[%d]\n' "$index"
      printf '状態: %s\n' "$status"
      printf '付与日時: %s\n' "$granted_at"
      printf '有効期限: %s\n' "$expires_at"
    done
  }
