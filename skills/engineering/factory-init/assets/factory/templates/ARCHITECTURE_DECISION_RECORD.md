<!--
TEMPLATE: Architecture Decision Record (ADR)
Location convention: engineering/adr/NNNN-<kebab-slug>.md (NNNN zero-padded, never reused)
Purpose: Record one significant decision, its context, and its consequences so future contributors understand WHY.
When to write one: architecture/topology, data model or storage, auth/security model, major dependency, contract/versioning strategy, anything expensive to reverse.
Rules: ADRs are immutable once Accepted — to change a decision, write a new ADR that supersedes it and update the old one's status.
-->

# ADR-{{NNNN}}: {{Decision title}}

| Field | Value |
|---|---|
| Status | {{Proposed / Accepted / Superseded by ADR-XXXX / Deprecated}} |
| Date | {{YYYY-MM-DD}} |
| Deciders | {{names}} |
| Related | {{specs, ADRs, issues}} |

## Context
{{The forces at play: requirements, constraints, current state, what problem forces a decision now.}}

## Decision
{{The decision, stated actively: "We will …". Include scope (what it applies to).}}

## Options considered
| Option | Pros | Cons |
|---|---|---|
| {{A (chosen)}} | | |
| {{B}} | | |

## Consequences
- **Positive:** {{…}}
- **Negative / costs:** {{…}}
- **Follow-ups required:** {{tasks, docs to update}}

## Revisit when
{{Concrete triggers that would justify reconsidering this decision.}}
