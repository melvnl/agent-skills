---
description: Correctly secured endpoint must not draw invented findings
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
    decision = get_object_or_404(Decision.objects.filter(application__owner=request.user), pk=decision_id)
    return Response(PublicDecisionSerializer(decision).data)   # status, reason_codes, decided_at only
```
