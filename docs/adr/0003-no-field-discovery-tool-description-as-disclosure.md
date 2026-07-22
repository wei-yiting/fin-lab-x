# ADR-0003: No field-discovery tool — the tool description is the disclosure channel (2026-07-21)

**Decision**: the agent's market-data surface is exactly two Finnhub tools split by call
economics — real-time quote (`/quote`) and curated fundamentals (`/stock/metric`) — so one
common question costs one API call. Field disclosure lives in the fundamentals tool's
description: a grouped summary of the curated catalog (22 keys, each live-verified against
the free tier), visible to the LLM at zero cost before it decides to call. No runtime
discovery tool. **Reopen when** the catalog grows past ~40–50 fields or exposes the raw
`/stock/metric` namespace (~130 keys) — then a static-catalog tool + `fields` selection
(progressive disclosure) starts paying for itself.

**Rejected**: a `finnhub_get_available_fields` discovery tool — it would hit the same
endpoint as the fundamentals tool while returning a strict information subset (a static key
list), doubling the API cost and tool-call budget of every fundamentals question; its shape
was inherited from a yfinance-era tool whose promised `fields` parameter was never
implemented. Also rejected for now: progressive disclosure over the full raw namespace —
disclosure machinery only pays when the disclosed space vastly exceeds typical need.

**Why**: under the free-tier budget (60 calls/min; envelope §2 treats upstream 429 as a
normal path) tool boundaries are drawn by call economics, and a function-calling schema is
already a zero-round-trip disclosure channel — a runtime tool that returns constants is
pure waste.
