#!/usr/bin/env bash
# V-1: S1 partial-turn regenerate probe.
#
# Purpose: Observe how backend S1 (`POST /api/v1/chat`) responds when the
# client tries to regenerate a turn whose previous stream was killed mid-flight.
#
# This is a one-shot observation, NOT an automated test. The goal is to record
# whether the regenerate endpoint returns 200 (direct retry possible),
# 422 (must fall back to sendMessage), or 500/hang (escalate).
#
# Burns LLM API tokens. Do not loop. Keep the partial-stream window short.
set -euo pipefail

BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
PARTIAL_FILE=/tmp/v1-partial.sse
REGEN_FILE=/tmp/v1-regen.out

echo "=== V-1: S1 partial-turn regenerate probe ==="
echo "backend: $BACKEND_URL"
echo "session: $SESSION_ID"

# Clear any stale capture files from a previous run.
rm -f "$PARTIAL_FILE" "$REGEN_FILE"

# 1. Start a long stream and let curl self-terminate after a short window
#    via --max-time. This simulates a user pressing Stop mid-stream while
#    avoiding the race that results from sending SIGTERM to a backgrounded
#    curl (TERM kills curl before it flushes its stdout buffer to disk,
#    leaving an empty SSE capture file).
#
#    `-o "$PARTIAL_FILE"` makes curl write directly to file, and curl flushes
#    each SSE chunk it receives. We expect curl to exit code 28 (operation
#    timeout) — that is the simulated stop event.
set +e
curl -s -N --max-time 4 -X POST "$BACKEND_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"$SESSION_ID\",\"message\":\"Give me a detailed analysis of NVDA: current price, recent news, key fundamentals, and price action over the past month. Use available tools.\"}" \
  -o "$PARTIAL_FILE"
CURL_EXIT=$?
set -e
echo "long-stream curl exit code: $CURL_EXIT (28 = timeout, expected)"

echo "--- partial SSE captured (first 800 bytes) ---"
head -c 800 "$PARTIAL_FILE" || true
echo
echo "--- end partial SSE ---"

# Sanity check: a true partial-turn capture must NOT contain a `finish` chunk.
# If the LLM finished within the timeout window, the regenerate request would
# act on a fully-committed turn rather than the partial one we want to probe,
# producing a misleading result. Fail loudly so the operator can rerun with a
# longer prompt.
if grep -q '"type":[[:space:]]*"finish"' "$PARTIAL_FILE"; then
  echo "ERROR: captured stream contains a 'finish' chunk — the LLM completed"
  echo "       its response within the timeout window. This is NOT a partial"
  echo "       turn. Rerun with a longer prompt or shorter --max-time."
  exit 2
fi

# 4. Extract messageId from the AI SDK v6 start chunk.
#    Backend serializes JSON with spaces after colons (`"messageId": "lc_run-..."`),
#    so the regex must allow optional whitespace.
#    Use grep+sed instead of jq so this script has no extra dependencies.
MSG_ID=$(grep -oE '"messageId":[[:space:]]*"[^"]*"' "$PARTIAL_FILE" | head -1 | sed -E 's/"messageId":[[:space:]]*"(.*)"/\1/')

if [[ -z "${MSG_ID:-}" ]]; then
  echo "ERROR: could not extract messageId from partial SSE."
  echo "       Either the backend never started streaming, or the start chunk"
  echo "       schema differs from AI SDK v6 wire format."
  exit 1
fi

echo "partial messageId: $MSG_ID"

# 5. Attempt regenerate against the partial messageId.
#    If S1 accepts it the response is itself an SSE stream — cap it with
#    --max-time 5 so we capture the head of the response without hanging
#    on the long tail.
HTTP_STATUS=$(curl -s -o "$REGEN_FILE" -w "%{http_code}" \
  --max-time 5 \
  -X POST "$BACKEND_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{\"id\":\"$SESSION_ID\",\"trigger\":\"regenerate\",\"messageId\":\"$MSG_ID\"}" || true)

echo "=== V-1 RESULT ==="
echo "HTTP_STATUS=$HTTP_STATUS"
echo "--- regen response body (first 1000 bytes) ---"
head -c 1000 "$REGEN_FILE" || true
echo
echo "--- end regen body ---"
