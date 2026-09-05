#!/usr/bin/env bash
set -euo pipefail

readonly interval_seconds="${POLIBOT_VERIFY_INTERVAL_SECONDS:-30}"
readonly status_url="http://127.0.0.1:8000/status"

if [[ ! "${interval_seconds}" =~ ^[0-9]+$ ]] || ((interval_seconds < 10)); then
  echo "Worker verification interval must be an integer of at least 10 seconds." >&2
  exit 2
fi

first="$(curl --fail --silent --show-error --max-time 5 "${status_url}")"
sleep "${interval_seconds}"
second="$(curl --fail --silent --show-error --max-time 5 "${status_url}")"

python3 - "${first}" "${second}" <<'PY'
import json
import sys

first = json.loads(sys.argv[1])
second = json.loads(sys.argv[2])
assert second["mode"] == "paper", second
assert second["live_trading"] is False, second
assert second["worker"]["current_status"] == "running", second
assert second["worker"]["ready"] is True, second
assert second["markets"]["selected"] > 0, second
assert second["markets"]["books_healthy"] > 0, second
assert second["markets"]["messages_received"] > first["markets"]["messages_received"], (
    first,
    second,
)
assert (
    second["strategies"]["binary_complete_set"]["evaluations"]
    > first["strategies"]["binary_complete_set"]["evaluations"]
), (first, second)
assert second["system"]["recorder_dropped_events"] == 0, second
assert second["system"]["database_errors"] == 0, second
print(json.dumps(second, sort_keys=True))
PY

record_count="$(
  docker exec polibot-paper-postgres-1 \
    psql -U polibot -d polibot -Atc 'select count(*) from recorded_events'
)"
if [[ ! "${record_count}" =~ ^[0-9]+$ ]] || ((record_count < 1)); then
  echo "No durable worker records were found." >&2
  exit 1
fi
printf 'recorded_events=%s\n' "${record_count}"
