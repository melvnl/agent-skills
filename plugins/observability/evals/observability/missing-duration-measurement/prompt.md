---
description: Important external operation without duration
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def get_score(applicant_ref):
    result = bureau_client.fetch(applicant_ref)   # p99 latency matters for the eligibility SLO
    logger.info("bureau_fetch_completed", extra={"applicant_ref": applicant_ref})
    return result
```
