---
type: llm
---

PASS if the reply flags that the error log has no event name, error code, exception type, correlation id or decision reference, swallows the exception silently, and recommends a structured error event with that context and a decision on re-raise or retry.

FAIL if the reply only rewords the message.
