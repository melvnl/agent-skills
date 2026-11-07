---
description: User email included in structured log fields
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
logger.info("login_succeeded", extra={"user_id": user.id, "email": user.email})
# example value seen in staging logs: sentinel.person@example.com
```
