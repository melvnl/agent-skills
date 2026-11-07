<!--
TEMPLATE: Task Breakdown
Location convention: tasks/<feature-id>-<slug>.md
Purpose: An ordered list of small, verifiable implementation tasks that a human or agent can execute and resume.
Instructions for agents:
- Each task: ≈ ≤ half a day, leaves the build green, has an explicit "done when".
- Typical order: domain/data → services/adapters → UI → E2E → docs.
- Keep Status current while working (this file is the resume point).
Status values: ⬜ Pending · 🟨 In progress · ✅ Done · ⛔ Blocked (say why)
-->

# {{Feature ID}} — {{Feature Name}}: Task Breakdown

| Field | Value |
|---|---|
| Spec | {{link}} |
| Design | {{link}} |
| Last updated | {{YYYY-MM-DD}} |

## Tasks

| ID | Task | Depends on | Covers (FR/AC) | Done when | Status |
|---|---|---|---|---|---|
| T-1 | {{task}} | — | {{ids}} | {{verifiable condition, e.g. "unit tests for X pass"}} | ⬜ |
| T-2 | {{task}} | T-1 | {{ids}} | {{condition}} | ⬜ |

## Notes / decisions made during implementation
- {{YYYY-MM-DD}}: {{note}}

## Blockers
| Task | Blocked by | Owner |
|---|---|---|
| {{T-x}} | {{question/approval}} | {{who}} |
