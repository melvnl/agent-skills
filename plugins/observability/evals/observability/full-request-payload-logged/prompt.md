---
description: Whole request payload logged
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def create_application(request):
    logger.info("application_received", extra={"payload": request.data})
    return service.create(request.data)
```
