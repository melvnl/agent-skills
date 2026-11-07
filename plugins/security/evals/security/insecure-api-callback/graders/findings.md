---
type: llm
---

PASS if the reply flags that anyone can forge the callback (no signature verification over the raw body, no timestamp/replay protection, no idempotency) and recommends verifying the provider's signature with a constant-time compare, rejecting stale timestamps, deduplicating by event id, and re-fetching authoritative status from the provider.

FAIL if the reply only suggests adding authentication via a shared query parameter or IP allowlist alone.
