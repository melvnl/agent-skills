---
type: llm
---

PASS if the reply identifies that client retries create duplicate decisions and duplicate events, and recommends an idempotency key or unique constraint per application/request, returning the existing decision, and publishing via on_commit or an outbox.

FAIL if the reply misses duplicate creation on retry.
