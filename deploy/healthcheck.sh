#!/usr/bin/env bash
set -euo pipefail

response="$(curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/health)"
readiness="$(curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/ready)"
python3 -c '
import json, sys
payload = json.loads(sys.argv[1])
assert payload.get("healthy") is True, payload
assert payload.get("execution_mode") == "paper", payload
assert payload.get("live_trading_enabled") is False, payload
worker = payload.get("worker") or {}
assert worker.get("current_status") == "running", payload
ready = json.loads(sys.argv[2])
assert ready.get("ready") is True, ready
' "${response}" "${readiness}"
