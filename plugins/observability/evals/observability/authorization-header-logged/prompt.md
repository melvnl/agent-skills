---
description: Authorization header logged during debugging
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def call_partner(request):
    logger.debug("partner_call", extra={"auth": request.headers.get("Authorization")})
    # example header from a bug report: Bearer tok_live_SENTINEL_7f3a
    return partner.post(...)
```
