# BYOK key transport: RSA-OAEP per-request, server never stores the key

Status: accepted (2026-08-26) — DEV-189, implementing the transport decisions from DEV-188's BYOK spec.

**Decision**: a user's OpenAI API key is encrypted client-side with RSA-OAEP
(SHA-256, 4096-bit) against the server's public key and sent on every request
via the `X-Custom-Openai-Api-Key` header. The server holds only the RSA
private key (env-configured, loaded once per process); it decrypts the header
value, uses the plaintext key for that one request, and discards it — no
database row, cache entry, session field, or log line ever holds it. Any
decryption failure (malformed base64, wrong/corrupted ciphertext, non-UTF-8 or
empty plaintext, or an empty header value) is a structured 401; the server
never falls back to its own key on a BYOK failure.

**Why RSA-OAEP over the JSEncrypt/PKCS1v15 pattern this was adapted from**
([jin-t-backend](https://github.com/wei-yiting/jin-t-backend)): OAEP is the
padding scheme both NIST and the Web Crypto spec treat as current for RSA
encryption; PKCS1v15 is legacy, kept alive mainly by libraries like JSEncrypt
that predate native browser crypto. Since the frontend targets Web Crypto
directly (`crypto.subtle.encrypt({name: "RSA-OAEP"}, ...)`), there is no
JSEncrypt compatibility constraint to trade against. One concrete consequence:
Web Crypto's `importKey` only accepts SPKI-formatted public keys, not the
PKCS1 format jin-t-backend generates for JSEncrypt — the keypair script here
emits PKCS8 (private) / SPKI (public) instead.

**Why 4096-bit, not 2048-bit**: RSA-OAEP's plaintext capacity is
`key_size_bytes − 2×hash_bytes − 2`. At 2048-bit/SHA-256 that's 190 bytes —
current OpenAI keys (`sk-proj-...`, ~160-170 chars) fit, but with only ~20
bytes of headroom. At 4096-bit it's 446 bytes, which absorbs a future key
format change without a coordinated keypair rotation across every deployed
client. The cost is a longer key (header grows to ~684 base64 chars, still
far under any header-size limit) and a few extra milliseconds per decrypt —
negligible against this project's request volume.

## Considered options

1. **RSA-OAEP + Web Crypto (chosen).**
2. **JSEncrypt + PKCS1v15** (the reference implementation's approach) —
   rejected: weaker padding scheme, and pulls in a third-party JS library the
   native Web Crypto API makes unnecessary.
3. **Plaintext header over TLS** — rejected: TLS protects the transport hop,
   but the key would still appear in plaintext at every TLS-terminating
   point (load balancer, reverse proxy, access logs). Application-layer
   encryption is defense in depth against exactly that class of exposure.
4. **Server-side key storage** (session or database row) — rejected: there is
   no account system to scope storage to, and a stored credential is a
   standing liability with no corresponding benefit — the key is only ever
   needed for the single request carrying it.
5. **Per-request preflight validation** (call OpenAI to check the key before
   every chat turn) — rejected: adds 100-300ms of latency to every BYOK
   request to catch a failure mode (a key that validated fine at save-time
   but was later revoked or exhausted) that is already rare because the
   dedicated `/byok/validate-key` endpoint checks the key before it's saved.
   The residual case is handled by catching the provider's rejection
   mid-request instead of guarding against it in advance.

## Consequences

- The private key is loaded and validated once at process startup
  (`validate_byok_config`, `backend/api/byok.py`): missing entirely is a
  supported no-op (BYOK disabled, free tier unaffected — the local-dev
  default), but present-and-malformed fails fast, matching the existing
  `EDGAR_IDENTITY` precedent of catching a broken deployment before its
  first affected request rather than on it.
- Key rotation is a manual runbook (`docs/byok_key_rotation.md`), not an
  automated dual-key transition — a request encrypted with a rotated-out
  public key gets the same 401 as any other decrypt failure, and the user's
  own retry (after their browser picks up the new public key on next page
  load) recovers it.
- This ADR covers transport only. The engine-side per-request model
  injection mechanism (LangChain `wrap_model_call` middleware + Runtime
  Context) is not recorded here — it's freely reversible and its rationale
  lives as a docstring on `ByokModelOverrideMiddleware` in
  `backend/agent_engine/agents/base.py`.
