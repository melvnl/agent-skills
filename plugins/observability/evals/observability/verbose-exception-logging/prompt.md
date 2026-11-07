---
description: Exception logged with full payload dump and repeated stack traces
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
try:
    decision = engine.evaluate(application)
except Exception as exc:
    logger.error(f"Evaluation failed for {application.__dict__}: {exc}", exc_info=True)
    logger.error(traceback.format_exc())
    raise
```
