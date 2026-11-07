---
type: llm
---

PASS if the reply identifies the lost-update race (two concurrent reservations can both pass the check and overspend the limit) and recommends a conditional atomic UPDATE, F() expression with a guard, or select_for_update inside a transaction, plus a concurrency test.

FAIL if the reply misses the race or only adds a try/except.
