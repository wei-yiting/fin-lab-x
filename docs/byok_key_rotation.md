# BYOK Keypair Rotation Runbook

Rationale for why this exists at all (RSA-OAEP, 4096-bit, no server-side
storage) is [ADR-0018](adr/0018-byok-rsa-per-request-key-transport.md). This
document is the "how", not the "why" — follow it when you need to actually
rotate the keypair.

## When to rotate

- Suspected exposure of `BYOK_RSA_PRIVATE_KEY` (leaked env dump, accidental
  commit, compromised deployment credential store).
- Routine security hygiene.

## What rotation costs

There is no dual-key transition window. Any request encrypted against the
old public key fails to decrypt against the new private key and gets the
standard `byok_key_invalid` 401 — indistinguishable from any other decrypt
failure. This is accepted (see ADR-0018, Consequences): the user's next
retry, after their browser reloads and picks up the new public key from the
frontend build, recovers automatically. There is no user-visible data loss —
BYOK keys are never stored server-side, so rotation touches transport
config only, never user data.

## Steps

1. **Generate a fresh keypair:**

   ```bash
   uv run python backend/scripts/generate_byok_keypair.py
   ```

   This prints two lines — `BYOK_RSA_PRIVATE_KEY=...` and
   `VITE_BYOK_RSA_PUBLIC_KEY=...` — and never writes anything to disk.

2. **Update the backend deployment environment**: set `BYOK_RSA_PRIVATE_KEY`
   to the new private-key line's value.

3. **Update the frontend build environment** (Vercel or equivalent): set
   `VITE_BYOK_RSA_PUBLIC_KEY` to the new public-key line's value. This is a
   *build-time* variable — it gets baked into the JS bundle, so a redeploy
   is required, not just a running-instance restart.

4. **Redeploy both sides.** Order doesn't matter for correctness (a
   mismatched pair just produces 401s until both sides catch up), but
   redeploying the backend first minimizes the mismatch window since backend
   deploys are typically faster than a frontend build.

5. **Verify**: run `POST /api/v1/byok/validate-key` with a real test key
   encrypted against the *new* public key. A `valid` response confirms both
   sides are on the new keypair and decrypting correctly.

6. **Discard the old keypair.** Nothing references it once step 4 completes
   — there is no "previous key" concept to clean up beyond your own shell
   history / password manager, if you saved it anywhere while rotating.

## If something goes wrong mid-rotation

If only one side has redeployed (e.g., backend has the new private key but
the frontend build is still serving the old public key), every BYOK request
in that window gets `byok_key_invalid`. This is expected and self-resolving
once the second side finishes deploying — no rollback needed. Free-tier
(non-BYOK) traffic is completely unaffected throughout.
