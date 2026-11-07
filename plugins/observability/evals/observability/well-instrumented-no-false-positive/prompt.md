---
description: Already well-instrumented code must not draw invented findings
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def evaluate(application_ref, request_id):
    start = time.perf_counter()
    status = "failed"
    try:
        decision = engine.evaluate(application_ref)
        status = decision.status
        return decision
    finally:
        logger.info("eligibility_evaluation_completed", extra={
            "request_id": request_id, "application_ref": application_ref,   # approved internal reference
            "status": status, "rule_version": engine.rule_version,
            "duration_ms": round((time.perf_counter() - start) * 1000, 1)})
```
