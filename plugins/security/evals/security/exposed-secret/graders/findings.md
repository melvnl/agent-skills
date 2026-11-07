---
type: llm
---

PASS if the reply flags the hard-coded live key, recommends loading it from the environment or a secret manager, and says the key must be rotated because it reached source control.

FAIL if the reply only suggests moving it to a constants module, or repeats the key value.
