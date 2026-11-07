---
description: Migration drops and renames columns in one step
tags: [security]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Security review of this backend change. Report exploitable issues with an exploit scenario and a fix.

```python
class Migration(migrations.Migration):
    operations = [
        migrations.RenameField("application", "score", "bureau_score"),
        migrations.RemoveField("application", "legacy_flag"),
        migrations.AddField("application", "reason", models.CharField(max_length=64)),
    ]
```
