---
description: Decision explanation joins to mutable current rules
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
def explain(decision_id):
    d = Decision.objects.get(pk=decision_id)
    rules = RuleSet.objects.get(active=True)      # current rules
    applicant = Applicant.objects.get(pk=d.applicant_id)   # current data
    return rules.explain(applicant)
```
