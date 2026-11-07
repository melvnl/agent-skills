---
description: A precise PRD must not draw invented problems
tags: [prd]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Analyze this PRD excerpt before we plan implementation. List the problems you find and what you need from the product owner.

---
FR-1 POST /v1/eligibility accepts application_ref (string, required) and returns status in {approved, rejected, manual_review} with reason_codes.
BR-1 score >= 600 -> approved; 550 <= score <= 599 -> manual_review; score < 550 -> rejected.
NFR-1 p95 latency < 300 ms at 50 rps, measured in the staging load test.
NFR-2 If the bureau does not respond within 1.5 s, status is manual_review with reason BUREAU_TIMEOUT (approved by Risk, 2026-10-02).
NFR-3 Every decision is stored with inputs snapshot, rule version and reason codes for 5 years.
---
