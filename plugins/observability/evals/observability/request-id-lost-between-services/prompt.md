---
description: Outbound call drops the inbound request id
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def fetch_bureau_score(application_ref):
    # inbound request carried X-Request-ID; it is available via get_request_id()
    resp = requests.post(BUREAU_URL, json={"ref": application_ref}, timeout=3)
    logger.info("bureau_called", extra={"status_code": resp.status_code})
    return resp.json()["score"]
```
