---
description: Read-modify-write on a credit limit
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
def reserve(limit_id, amount):
    limit = CreditLimit.objects.get(pk=limit_id)
    if limit.available >= amount:
        limit.available -= amount
        limit.save()
        return True
    return False
```
