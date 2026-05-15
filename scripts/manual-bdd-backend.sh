#!/usr/bin/env bash
# Helper: boot the backend in one of several BDD profiles for manual verification.
# Usage:
#   ./scripts/manual-bdd-backend.sh <profile>           # foreground
#   ./scripts/manual-bdd-backend.sh <profile> --bg      # background; logs to /tmp/uvicorn-bdd-<profile>.log
#   ./scripts/manual-bdd-backend.sh restore             # restore v1_baseline.yaml (no boot)
#
# Profiles:
#   openai-on           default v1_baseline (OpenAI gpt-5-mini + reasoning summary)
#   openai-off          OpenAI gpt-5-mini reasoning off (yaml swap)
#   gemini-on           Gemini 2.5 Flash + thinking_budget=1024  (yaml swap)
#   gemini-off          Gemini reasoning off  (yaml swap)
#   anthropic-on        Anthropic Sonnet 4.5 + extended thinking (yaml swap, temp=1.0)
#   anthropic-off       Anthropic Sonnet 4.5 reasoning off (yaml swap)
#   delayed-reasoning   default + EMIT_DELAYED_REASONING=1  (S-rsn-06 stalled)
#   late-reasoning      default + EMIT_LATE_REASONING=1     (S-rsn-12)
#   force-llm-fail      default + FORCE_LLM_FAIL=1          (S-stream-04)
#   non-transient-prod  default + FORCE_REASONING_NON_TRANSIENT=1 APP_ENV=production
set -euo pipefail

cd "$(dirname "$0")/.."
YAML=backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml
BAK=${YAML}.bak

profile=${1:-openai-on}
mode=${2:-fg}

case "$profile" in
  restore)
    if [[ -f "$BAK" ]]; then
      mv "$BAK" "$YAML"
      echo "restored $YAML"
    else
      echo "no backup to restore (already clean)"
    fi
    exit 0
    ;;
esac

# Stop anything on :8000
if lsof -ti:8000 >/dev/null 2>&1; then
  kill "$(lsof -ti:8000)" || true
  sleep 1
fi

# Backup yaml the first time we mutate it
if [[ ! -f "$BAK" ]]; then
  cp "$YAML" "$BAK"
fi

# Always reset yaml to openai-on baseline before each run, then patch per profile
cat > "$YAML" <<'YAML'
version: "0.1.0"
name: "v1_baseline"
description: "Naive single-chain financial analysis with basic tool access"

tools:
  - yfinance_stock_quote
  - yfinance_get_available_fields
  - tavily_financial_search
  - sec_filing_list_sections
  - sec_filing_get_section

model:
  name: "openai:gpt-5-mini"
  temperature: 0.0
  reasoning: "on"
  thinking_budget: null

constraints:
  max_tool_calls_per_run: 10
YAML

env_extra=()

case "$profile" in
  openai-on) ;;
  openai-off)
    sed -i '' 's/reasoning: "on"/reasoning: "off"/' "$YAML"
    ;;
  gemini-on)
    sed -i '' \
      -e 's|name: "openai:gpt-5-mini"|name: "google_genai:gemini-2.5-flash"|' \
      -e 's/thinking_budget: null/thinking_budget: 1024/' \
      "$YAML"
    ;;
  gemini-off)
    sed -i '' \
      -e 's|name: "openai:gpt-5-mini"|name: "google_genai:gemini-2.5-flash"|' \
      -e 's/reasoning: "on"/reasoning: "off"/' \
      -e 's/thinking_budget: null/thinking_budget: 0/' \
      "$YAML"
    ;;
  anthropic-on)
    sed -i '' \
      -e 's|name: "openai:gpt-5-mini"|name: "anthropic:claude-sonnet-4-5-20250929"|' \
      -e 's/temperature: 0.0/temperature: 1.0/' \
      -e 's/thinking_budget: null/thinking_budget: 1024/' \
      "$YAML"
    ;;
  anthropic-off)
    sed -i '' \
      -e 's|name: "openai:gpt-5-mini"|name: "anthropic:claude-sonnet-4-5-20250929"|' \
      -e 's/reasoning: "on"/reasoning: "off"/' \
      "$YAML"
    ;;
  delayed-reasoning) env_extra+=("EMIT_DELAYED_REASONING=1") ;;
  late-reasoning)    env_extra+=("EMIT_LATE_REASONING=1") ;;
  force-llm-fail)    env_extra+=("FORCE_LLM_FAIL=1") ;;
  non-transient-prod)
    env_extra+=("FORCE_REASONING_NON_TRANSIENT=1" "APP_ENV=production") ;;
  *)
    echo "unknown profile: $profile" >&2
    exit 2
    ;;
esac

set -a; source backend/.env; set +a
echo "Starting backend with profile=$profile env=${env_extra[*]:-<none>} mode=$mode"
# ${env_extra[@]:-} avoids "unbound variable" under `set -u` when the array
# is empty (gemini-on case has no extra env). Without :-, bash treats
# expansion of an empty array as referencing an unset variable.

if [[ "$mode" == "--bg" || "$mode" == "bg" ]]; then
  log=/tmp/uvicorn-bdd-${profile}.log
  nohup env ${env_extra[@]:-} uv run uvicorn backend.api.main:app \
      --host 127.0.0.1 --port 8000 > "$log" 2>&1 &
  pid=$!
  # Wait up to 10s for the backend to bind
  for _ in $(seq 1 20); do
    if curl -s -o /dev/null http://127.0.0.1:8000/health; then
      echo "backend up (pid=$pid, log=$log)"
      exit 0
    fi
    sleep 0.5
  done
  echo "ERROR: backend did not become healthy within 10s. Log tail:" >&2
  tail -20 "$log" >&2
  exit 1
else
  env ${env_extra[@]:-} uv run uvicorn backend.api.main:app \
      --host 127.0.0.1 --port 8000
fi
