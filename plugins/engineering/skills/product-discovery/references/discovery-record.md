# Discovery record

Save at `product/sources/discovery-<YYYY-MM-DD>-<slug>.md`. It is the source the PRD traces to, so record the owner's answers in their words, not your paraphrase of what they should have said.

```markdown
# Discovery: {{name}}

| Field | Value |
|---|---|
| Date | {{YYYY-MM-DD}} |
| Mode | {{A: idea to product / B: request without PRD}} |
| Owner | {{name / role}}; other approvers: {{...}} |
| Depth | {{personal / business / regulated-financial}} |
| Starting material | {{links to notes, README, existing docs, or "none"}} |

## Interview
| # | Question | Answer (owner's words) | Decision / label |
|---|---|---|---|
| Q1 | {{question}} | {{answer}} | {{Confirmed: ... / Proposed: ... / Open question: ... (blocks ...)}} |

## Reflections confirmed
- {{YYYY-MM-DD}}: "{{summary read back}}": confirmed / corrected to "{{...}}"

## Open questions
| Id | Question | Blocks | Owner |
|---|---|---|---|
| Q-1 | {{...}} | {{phase 1 scope}} | {{who}} |
```

## Record-to-document mapping

| Interview content | Goes to | Template |
|---|---|---|
| Problem, users, outcome, success measure, goals, non-goals, constraints | `product/product-brief.md` | `.factory/templates/project-brief.md` |
| User descriptions, context, goals, pain points | `product/personas.md` | (factory `new-project` step 5) |
| Core journeys | `product/prd.md` § Users and key journeys (`J-n`, critical flag) | `.factory/templates/prd.md` |
| Capabilities | `product/prd.md` § Functional requirements (`FR-n`, priority, phase) | same |
| Limits, thresholds, formulas | `product/prd.md` § Business rules (`BR-n`) with exact values and inclusivity | same |
| Scale, latency, availability, security, privacy, audit, observability | `product/prd.md` § Non-functional requirements (`NFR-n`) | same |
| Non-goals and "later" ideas | PRD § Out of scope; ROADMAP later phases (Future consideration) | same |
| Unknowns | PRD § Open questions (`Q-n`, with what they block) | same |
| First version and later phases | `product/roadmap.md`: phase 1 independently useful, each phase with acceptance and exit criteria | (factory `new-project` step 8) |

Every PRD row cites its source: `discovery 2026-11-08 Q5` (or the existing document it came from), and carries a decision label.
