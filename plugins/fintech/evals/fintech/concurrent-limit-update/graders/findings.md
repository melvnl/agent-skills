---
type: llm
---

PASS if the reply identifies the lost-update race (two concurrent reservations can both pass the check and overspend the limit) and recommends a fix that removes the race: a conditional atomic UPDATE, an F() expression with a guard, or select_for_update inside a transaction. Mentioning a concurrency test is good but not required.

FAIL if the reply misses the race or only adds a try/except.
