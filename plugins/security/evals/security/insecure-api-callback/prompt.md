---
description: Payment-provider callback trusted without verification
tags: [security]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Security review of this backend change. Report exploitable issues with an exploit scenario and a fix.

```python
@csrf_exempt
def verification_callback(request):
    payload = json.loads(request.body)
    Verification.objects.filter(ref=payload["ref"]).update(status=payload["status"])
    return HttpResponse("ok")
```
