---
type: llm
---

PASS if the reply identifies that any authenticated user can read any decision by changing the id (object-level authorization missing), recommends scoping the query to the caller's records (and 404 for others), and a cross-user test.

FAIL if the reply says IsAuthenticated is sufficient.
