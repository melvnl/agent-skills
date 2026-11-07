---
description: Retried decision request creates duplicates
tags: [fintech]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this credit decisioning code for correctness. Report concrete problems and fixes.

```python
@api_view(["POST"])
def decide(request):
    app = Application.objects.get(reference=request.data["application_ref"])
    decision = Decision.objects.create(application=app, **engine.evaluate(app))
    publish_decision(decision)          # SNS
    return Response({"decision_id": decision.id}, status=201)
```
