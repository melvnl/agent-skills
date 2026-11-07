---
description: Float arithmetic and implicit rounding on amounts
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
def installment(amount: float, months: int, monthly_rate: float) -> float:
    total = amount * (1 + monthly_rate * months)
    return round(total / months, 2)
```
