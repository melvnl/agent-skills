---
description: Endpoint returns the full applicant record
tags: [security]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Security review of this backend change. Report exploitable issues with an exploit scenario and a fix.

```python
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def application_detail(request, ref):
    app = Application.objects.get(reference=ref, owner=request.user)
    return Response(model_to_dict(app))   # includes national_id, income, bureau_report
```
