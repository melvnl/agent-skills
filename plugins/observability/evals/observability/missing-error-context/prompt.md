---
description: Failure logged without actionable context
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
try:
    publish_decision(decision)
except Exception:
    logger.error("something went wrong")
```
