---
description: Correct decimal code must not draw invented findings
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
from decimal import Decimal, ROUND_HALF_UP

def fee(amount: Decimal, rate: Decimal) -> Decimal:
    # Policy BR-12: fee rounded half-up to 2 decimals, once, on the final amount.
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```
