---
type: llm
---

PASS if the reply flags the Authorization header as a secret that must never be logged in any form (not masked, not hashed), recommends removing it, and treats DEBUG as no excuse.

FAIL if the reply suggests masking or hashing the token as acceptable, or repeats the example token value.
