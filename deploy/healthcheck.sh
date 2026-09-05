#!/usr/bin/env bash
set -euo pipefail

response="$(curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/health)"
python3 -c '
import json, sys
payload = json.loads(sys.argv[1])
assert payload.get("healthy") is True, payload
assert payload.get("execution_mode") == "paper", payload
assert payload.get("live_trading_enabled") is False, payload
' "${response}"

