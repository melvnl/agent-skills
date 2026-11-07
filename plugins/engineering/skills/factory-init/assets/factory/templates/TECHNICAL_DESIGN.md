<!--
TEMPLATE: Technical Design
Location convention: specs/<feature-id>-<slug>/DESIGN.md
Purpose: Define HOW a specified feature will be built, consistent with the project's architecture.
Instructions for agents:
- Read the spec, ARCHITECTURE, DATA_MODEL, API_CONTRACTS, SECURITY docs, and the affected code first.
- Every functional requirement in the spec must map to at least one component (§ 3 table).
- Significant decisions → also write an ADR and link it.
- Every dependency in § 7 has a defined timeout, retry, and failure behavior; § 8 is filled for any backend change (write "None" with a reason rather than deleting it).
- Prefer the simplest design that satisfies the spec; justify any new abstraction or dependency.
-->

# {{Feature ID}} — {{Feature Name}}: Technical Design

| Field | Value |
|---|---|
| Status | {{Draft / Approved / Implemented}} |
| Spec | {{link to SPEC.md}} |
| Related ADRs | {{links}} |
| Last updated | {{YYYY-MM-DD}} |

## 1. Summary
{{2–4 sentences: the approach.}}

## 2. Proposed architecture
<!-- Where this sits in the existing architecture. Diagram encouraged. -->
```mermaid
flowchart LR
  UI[{{UI component}}] --> SVC[{{application service}}] --> DOM[{{domain logic}}]
  SVC --> REPO[{{repository / adapter}}]
```

## 3. Component responsibilities
| Component | Module / path | Responsibility | Requirements covered |
|---|---|---|---|
| {{name}} | {{path}} | {{single responsibility}} | {{FR ids}} |

## 4. Data models
<!-- New/changed entities, fields (with types and units), indexes, invariants, migrations, backward compatibility. -->
{{changes or "No changes"}}

## 5. API / service contracts
<!-- Function signatures, request/response schemas, error codes. -->
```ts
// {{example signature}}
```

## 6. Data flows
<!-- Sequence for the main paths, including failure paths. -->
```mermaid
sequenceDiagram
  actor User
  User->>{{UI}}: {{action}}
  {{UI}}->>{{Service}}: {{call}}
  {{Service}}-->>{{UI}}: {{result}}
```

## 7. Failure scenarios and error handling
<!-- One row per dependency failure, invalid state, concurrency conflict, and duplicate/retry case. Business fallbacks need owner approval. -->
| Failure | Detection | Behavior (user / business) | Recovery | Owner-approved? |
|---|---|---|---|---|
| {{failure}} | {{how: error, timeout, metric, check}} | {{message/state/fallback}} | {{retry/rollback/reconcile}} | {{Yes / n.a. / Pending}} |

## 8. Observability plan
<!-- What on-call must be able to answer, and the signals that answer it. Useful signals only: no logs without diagnostic value. -->
- **Questions to answer:** {{e.g. is it succeeding, for whom is it failing, which dependency is slow}}
- **Important operations:** {{operation: success, failure, latency signals}}
- **Identifiers and propagation:** {{request/correlation/trace ids; boundaries crossed}}
- **Log events:** {{event, level, fields, why}}; deliberately not logged: {{...}}
- **Sensitive fields:** {{field: handling (never logged / pseudonymized)}}
- **Metrics:** {{name, type, bounded labels, unit}}
- **Traces:** {{spans, propagation, or "existing auto-instrumentation"}}
- **Alerts:** {{condition, threshold, owner, runbook}}

## 9. Security and privacy considerations
- **Data accessed/stored:** {{what, classification}}
- **Authorization / isolation:** {{how enforced}}
- **Input validation:** {{where}}
- **Secrets / external services:** {{none / details}}

## 10. Performance considerations
{{expected data volumes, hot paths, caching, bundle impact}}

## 11. Testing strategy
| Level | What is tested | Acceptance criteria covered |
|---|---|---|
| Unit | {{domain functions}} | {{AC ids}} |
| Integration | {{adapters/services}} | {{AC ids}} |
| E2E | {{journeys}} | {{AC ids}} |

## 12. Trade-offs and alternatives considered
| Option | Pros | Cons | Decision |
|---|---|---|---|
| {{option A}} | | | {{Chosen / Rejected}} |

## 13. Rollout and migration
{{feature flags, data migration steps, backward compatibility, rollback plan — or "N/A"}}

## 14. Open questions
| # | Question | Blocks | Status |
|---|---|---|---|
| Q1 | {{question}} | {{what}} | {{Open}} |
