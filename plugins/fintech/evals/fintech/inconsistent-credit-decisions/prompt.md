---
description: Thresholds duplicated in two services drift apart
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
# decision-service/rules.py
APPROVE_MIN_SCORE = 600
# mobile-bff/precheck.py  (shows "you are likely eligible" before applying)
LIKELY_ELIGIBLE_SCORE = 580
```
