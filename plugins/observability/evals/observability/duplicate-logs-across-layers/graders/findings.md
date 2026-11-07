---
type: llm
---

PASS if the reply identifies that one expected not-found condition is logged three times, recommends logging it once at the handling layer (the view) and at an appropriate level (a 404 for a missing record is usually not ERROR).

FAIL if the reply recommends keeping all three logs or adding more.
