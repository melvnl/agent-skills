---
description: A real PRD must go to prd-analysis, not discovery
tags: [discovery]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Please analyze this PRD before we plan:
FR-1 Applicants submit an application with identity and income.
FR-2 Score >= 600 is approved; 550-599 goes to manual review.
NFR-1 Decisions return in under 2 seconds.
