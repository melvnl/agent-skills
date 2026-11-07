---
description: Metric labels with unbounded identifiers
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
DECISIONS = Counter("decisions_total", "Decisions", ["outcome", "applicant_ref", "request_path"])

def record(decision, request):
    DECISIONS.labels(outcome=decision.outcome, applicant_ref=decision.applicant_ref, request_path=request.path).inc()
```
