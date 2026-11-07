---
type: llm
---

PASS if the reply identifies that the logs carry no request or correlation id, and recommends obtaining or propagating one (e.g. via middleware or the existing context mechanism) rather than inventing a second id scheme.

FAIL if the reply misses the missing correlation, or recommends logging the request body or applicant data to compensate.
