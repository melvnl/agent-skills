---
description: Endpoint logs without any request or correlation id
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
@api_view(["POST"])
def evaluate_eligibility(request):
    logger.info("eligibility_requested")
    decision = service.evaluate(request.data["application_ref"])
    logger.info("eligibility_completed", extra={"status": decision.status})
    return Response({"status": decision.status})
```
