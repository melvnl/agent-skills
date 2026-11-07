<!--
TEMPLATE: Implementation Report
Location convention: tasks/reports/<feature-id or date>-<slug>.md
Purpose: Factual record of what was delivered, how it was verified, and what remains.
Instructions for agents:
- Report only commands you actually ran, with actual results. Mark anything not run as "Not run" with the reason.
- Do not overstate completeness. Unmet Definition-of-Done items must be listed.
-->

# Implementation Report — {{Feature ID / Task}}: {{Title}}

| Field | Value |
|---|---|
| Date | {{YYYY-MM-DD}} |
| Author | {{human / agent}} |
| Spec / Design | {{links}} |
| Workflow followed | {{NEW_FEATURE / BUG_FIX / REFACTORING / …}} |

## 1. Summary
{{What was delivered, in 2–4 sentences.}}

## 2. Changes
| Type | Path | Notes |
|---|---|---|
| Created / Updated / Deleted | {{path}} | {{why}} |

## 3. Requirements and acceptance criteria
| ID | Status | Evidence |
|---|---|---|
| {{AC-1}} | {{Met / Partially / Not met}} | {{test name / manual check}} |

## 4. Verification
| Gate | Command | Result |
|---|---|---|
| Lint | {{cmd}} | {{e.g. pass, 0 errors / Not run: reason}} |
| Type check | {{cmd}} | {{result}} |
| Unit tests | {{cmd}} | {{x passed, y failed}} |
| Integration tests | {{cmd}} | {{result}} |
| E2E tests | {{cmd}} | {{result}} |
| Build | {{cmd}} | {{result}} |

## 5. Instrumentation
<!-- What was added for observability and why, or an explicit statement that none was justified. -->
| Signal | Location | Purpose |
|---|---|---|
| {{event / metric / span}} | {{path:line}} | {{why it is needed}} |
Deliberately not added: {{...}} · Correlation verified: {{how}} · Sensitive data check: {{how}}

## 6. Key decisions
- {{decision — link ADR if any}}

## 7. Assumptions
- {{assumption and why it was reasonable}}

## 8. Known limitations and issues
| Issue | Severity | Follow-up task |
|---|---|---|
| {{issue}} | {{Critical/High/Medium/Low}} | {{task ref}} |

## 9. Open questions
- {{question — what it blocks}}

## 10. Definition of Done status
{{All met / list unmet items}}

## 11. Recommended next step
{{next step}}
