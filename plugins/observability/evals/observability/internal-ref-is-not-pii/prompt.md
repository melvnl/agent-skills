---
description: Approved internal reference must not be treated as PII by name alone
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
# Per engineering/SECURITY_AND_PRIVACY.md, customer_ref is an approved, non-linkable internal reference.
logger.warning("bureau_timeout_fallback", extra={"customer_ref": customer_ref, "dependency": "bureau",
                                                 "error_code": "BUREAU_TIMEOUT", "retry_count": 2})
```
