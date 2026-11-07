---
type: llm
---

PASS if the reply flags that the response exposes sensitive personal and financial fields beyond the use case and recommends an explicit response serializer with only needed fields, plus a test asserting sensitive fields are absent.

FAIL if the reply finds no issue because authentication and owner scoping are present.
