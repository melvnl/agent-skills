---
description: Secret committed in settings
tags: [security]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Security review of this backend change. Report exploitable issues with an exploit scenario and a fix.

```python
# settings.py
BUREAU_API_KEY = "bk_live_SENTINEL_51e9c2"
```
