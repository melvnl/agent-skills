<!--
TEMPLATE: Feature Specification
Location convention: specs/<feature-id>-<slug>/SPEC.md
Purpose: Define WHAT a feature must do and HOW we will know it is done. No implementation detail (that goes in DESIGN.md).
Instructions for agents:
- Trace every requirement to PRD IDs where they exist.
- Acceptance criteria must be Given/When/Then and each must name a verification method.
- Do not invent requirements. Put candidates in Open questions.
- After approval, acceptance criteria change only via the Change log with approval.
-->

# {{Feature ID}} — {{Feature Name}}: Specification

| Field | Value |
|---|---|
| Status | {{Draft / In review / Approved / Implemented}} |
| Phase | {{n}} |
| Owner | {{human}} |
| PRD references | {{FR-x, NFR-y}} |
| Design | {{link to DESIGN.md}} |
| Last updated | {{YYYY-MM-DD}} |

## 1. Problem statement
{{Who has what problem, in what situation, and what it costs them today.}}

## 2. Goals
- {{goal — outcome-oriented}}

## 3. Non-goals
- {{explicitly out of scope for this feature}}

## 4. User stories
| ID | As a… | I want… | So that… |
|---|---|---|---|
| US-1 | {{persona}} | {{capability}} | {{benefit}} |

## 5. Functional requirements
| ID | Requirement | Traces to |
|---|---|---|
| {{FID}}-FR-1 | {{The system must …}} | {{FR-x / US-1}} |

## 6. Non-functional requirements
| ID | Requirement (measurable) | Traces to |
|---|---|---|
| {{FID}}-NFR-1 | {{e.g. view renders with data in < 1 s on mid-range mobile}} | {{NFR-x}} |

## 7. UX notes
<!-- Optional: key screens/states, copy, wireframe links. Include loading / empty / error states. -->
{{notes}}

## 8. Acceptance criteria
| ID | Given | When | Then | Verifies | Method |
|---|---|---|---|---|---|
| AC-1 | {{precondition}} | {{action}} | {{observable outcome}} | {{FR ids}} | {{Unit / Integration / E2E / Manual}} |

## 9. Edge cases
| Case | Expected behavior |
|---|---|
| {{empty / zero / boundary / invalid / concurrent / timezone / offline}} | {{behavior}} |

## 10. Dependencies
- **Features/specs:** {{ids}}
- **Technical:** {{modules, libraries, services}}
- **External / decisions:** {{ADRs, approvals}}

## 11. Open questions
| # | Question | Blocks | Proposed answer | Status |
|---|---|---|---|---|
| Q1 | {{question}} | {{what}} | {{recommendation}} | {{Open/Resolved}} |

## 12. Change log
| Date | Change | Approved by |
|---|---|---|
| {{YYYY-MM-DD}} | Initial draft | — |
