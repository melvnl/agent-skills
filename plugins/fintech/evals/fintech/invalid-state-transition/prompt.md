---
description: Override path allows illegal transitions and overwrites history
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
def override_decision(decision_id, new_status, user):
    d = Decision.objects.get(pk=decision_id)
    d.status = new_status          # any status, from any status
    d.save()
```
