---
description: INFO log per item in a hot loop
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def refresh_scores(applicant_refs):        # called with ~200k refs nightly
    for ref in applicant_refs:
        score = compute(ref)
        logger.info("score_computed", extra={"applicant_ref": ref, "score": score})
```
