---
description: Fetch by id without owner scoping (IDOR)
tags: [security]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Security review of this backend change. Report exploitable issues with an exploit scenario and a fix.

```python
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def decision_detail(request, decision_id):
    return Response(DecisionSerializer(Decision.objects.get(pk=decision_id)).data)
```
