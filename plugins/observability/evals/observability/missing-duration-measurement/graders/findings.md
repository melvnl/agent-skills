---
type: llm
---

PASS if the reply recommends recording the call's duration (duration_ms measured with a monotonic clock) and outcome, and/or a latency histogram metric for the dependency, because the operation's latency is SLO-relevant.

FAIL if the reply suggests time.time() differences as the measurement or doesn't mention latency at all.
