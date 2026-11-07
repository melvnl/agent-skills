# PRD analysis template

```markdown
# Analysis: {{source name}}

| Field | Value |
|---|---|
| Source | `product/sources/{{file}}` |
| Version / date | {{version}} / {{YYYY-MM-DD}} |
| Analyzed | {{YYYY-MM-DD}} by {{agent/human}} |
| Status | {{Draft / Awaiting owner / Resolved}} |

## 1. Inventory
| Ref | Section | Size | Notes |
|---|---|---|---|
| S1 §1 | {{Overview}} | {{~40 lines}} | {{diagram not converted}} |

## 2. Extracted statements
| # | Type | Statement | Source | vs existing |
|---|---|---|---|---|
| E-1 | FR | {{The system must ...}} | S1 §3.2 | {{new / FR-12 / implemented / conflicts FR-4}} |
| E-2 | BR | {{Applicants scoring >= 600 are eligible}} | S1 §4.1 | new |
| E-3 | NFR | {{...}} | S1 §6 | new |

## 3. Domain model
- Actors and roles: {{actor: capabilities}}
- Entities and states: {{entity: state1 -> state2 -> ...}}
- External systems: {{system: purpose, direction}}
- Glossary: {{term: definition (source)}}; synonyms: {{A = B?}}

## 4. NFR coverage
| Category | Status | Source / note |
|---|---|---|
| Performance | {{present / missing / n.a.}} | {{S1 §6.1}} |

## 5. Issues
| ID | Type | Severity | Sources | Description | Question for owner | Recommendation |
|---|---|---|---|---|---|---|
| I-1 | Contradiction | Blocking | S1 §2, S1 §7 | {{5/day vs 10/day}} | {{Which limit applies?}} | {{5/day (stricter)}} |

## 6. Owner decisions
| Issue | Decision | Decided by | Date |
|---|---|---|---|
| I-1 | {{...}} | {{name}} | {{YYYY-MM-DD}} |

## 7. Next step
{{e.g. Resolve I-1..I-4, then run specification-decomposition.}}
```
