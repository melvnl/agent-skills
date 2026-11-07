---
type: llm
---

PASS if the reply flags logging the whole request payload as a sensitive-data risk (personal and financial fields) and recommends logging only explicit allowlisted fields such as an internal reference.

FAIL if the reply accepts the payload logging, or suggests masking the payload after the fact as the main fix instead of allowlisting fields.
