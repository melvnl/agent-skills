---
description: Same failure logged at repository, service and view layers
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
class Repo:
    def get(self, ref):
        try: return Application.objects.get(reference=ref)
        except Application.DoesNotExist:
            logger.error("application_not_found", extra={"ref": ref}); raise

class Service:
    def evaluate(self, ref):
        try: return decide(self.repo.get(ref))
        except Application.DoesNotExist:
            logger.error("evaluation_failed_not_found", extra={"ref": ref}); raise

def view(request, ref):
    try: return Response(Service().evaluate(ref))
    except Application.DoesNotExist:
        logger.error("not_found", extra={"ref": ref}); return Response(status=404)
```
