<!--
TEMPLATE: Product Requirements Document (PRD)
Purpose: The authoritative list of product requirements, with stable IDs that specs, designs, tests, and reports trace to.
Instructions for agents:
- Every requirement gets a stable ID (FR-x / NFR-x). Never renumber; deprecate instead.
- Each requirement must be testable. Replace vague words with measurable criteria.
- Mark phase for every requirement. Do not invent requirements; list candidates under Open questions.
-->

# {{Project Name}} — Product Requirements Document

| Field | Value |
|---|---|
| Owner | {{accountable human}} |
| Status | {{Draft / Approved}} |
| Version | {{x.y}} |
| Last updated | {{YYYY-MM-DD}} |
| Related | {{links: brief, personas, roadmap}} |

## 1. Overview
{{Short summary of the product and this document's scope.}}

## 2. Users and key journeys
| Journey ID | Persona | Journey | Phase | Critical? |
|---|---|---|---|---|
| J-1 | {{persona}} | {{start → end in one line}} | {{1}} | {{Yes/No}} |

<!-- Critical journeys require E2E tests (see TESTING_STANDARDS). -->

## 3. Functional requirements
<!-- Group by capability area. Use "must/should/may" (MoSCoW-like): must = required for phase exit. -->
### 3.x {{Capability area}}
| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-{{n}} | {{The system must …}} | {{Must/Should/May}} | {{1}} |

## 4. Non-functional requirements
| ID | Category | Requirement (measurable) | Phase |
|---|---|---|---|
| NFR-{{n}} | {{Performance / Accessibility / Security / Privacy / Reliability / Offline / Compatibility}} | {{measurable statement}} | {{1}} |

## 5. Business rules and calculations
<!-- Formulas, thresholds, rounding, units, boundary inclusivity. These become unit tests. -->
| ID | Rule |
|---|---|
| BR-{{n}} | {{rule}} |

## 6. Out of scope
- {{explicitly excluded item}}

## 7. Assumptions, open questions, future considerations
| Type | Item | Status / blocks |
|---|---|---|
| {{Assumption / Open question / Future}} | {{item}} | {{status}} |

## 8. Change log
| Date | Change | Approved by |
|---|---|---|
| {{YYYY-MM-DD}} | {{change}} | {{name}} |
