# Workflow overlay: Fintech Feature

> **Scope:** Project-agnostic overlay on `NEW_FEATURE.md`. It applies when the project's `CLAUDE.md` declares a financial domain, or when a feature changes credit, eligibility, or risk decisions, limits, pricing, or other financially relevant data. It adds gates to each `NEW_FEATURE` stage; it doesn't replace them.

## Purpose

Ship financial decision features that are correct per the approved policy, reconstructable, safe under failure, and released without silent changes to customer outcomes.

## Entry conditions

- `NEW_FEATURE.md` applies, and one of the scope conditions above holds.
- A named policy owner exists for the business rules involved.

## Additional inputs

- The authoritative policy (rules, thresholds, fallbacks, reason codes) and its owner.
- The invariant catalog and audit requirements for the affected data.
- The authorization policy for the affected operations (roles, caps, maker-checker).

## Additional outputs

- Policy traceability: every rule in code traced to an approved policy statement.
- Decision record design, versioning and activation plan, fallback table with owner approvals.
- Golden dataset results and, for migrations of logic, a parity report.
- Domain and invariant review records.

## Additional steps per `NEW_FEATURE` stage

| Stage | Additional gate |
|---|---|
| Spec (steps 3–4) | The policy source is cited for every rule; acceptance criteria cover each threshold at its boundary, missing inputs, each dependency fallback, reason codes, audit records, and authorization (including maker-checker). Monetary values have precision and rounding rules. |
| Design (step 5) | Decision record contents; immutable versions and a separate, audited activation step; owner-approved fallback per dependency (no silent approvals); invariants touched and how each is enforced; audit events written atomically; authorization matrix updates; failure behavior chosen as fail-closed, degraded, or (only with owner acceptance) fail-open; a parity plan when logic moves between services. |
| Tasks (step 6) | Tasks for golden-dataset and boundary tests, duplicate and concurrency tests, audit-record tests, and decision metrics. |
| Implementation (step 7) | Exact decimal arithmetic; idempotent writes; no copied thresholds outside the policy's single source of truth. |
| Verification (steps 8–9) | Golden dataset run and every outcome change explained as an approved policy change; reviews by someone other than the implementer for: domain policy, financial invariants, security, and observability (`SECURITY_REVIEW.md`, `OBSERVABILITY_REVIEW.md`). Schema changes follow `DATABASE_MIGRATION.md`. |
| Release | Behind a flag or versioned activation; canary compares decision distributions (approval rate, limits, fallback rate, reason codes) with the baseline; rollback rehearsed; activation approved by someone other than the proposer. |

If the fintech skills (`credit-scoring-and-eligibility`, `risk-decision-engineering`, `financial-data-integrity`, `financial-auditability`, `financial-authorization`, `financial-system-reliability`, `money-and-decimal-arithmetic`) and the `fintech-domain-reviewer` and `financial-invariant-reviewer` agents are available, use them for these gates.

## Quality gates

| Gate | Passes when |
|---|---|
| Policy fidelity | No rule without an approved policy source; no unexplained golden-set outcome change |
| Reconstructability | A stored decision re-evaluates to the same outcome from its record (test) |
| Failure safety | Every dependency failure has a tested, owner-approved behavior |
| Integrity | Duplicate, concurrency, and audit-atomicity tests pass |
| Release safety | Canary distribution checks defined; rollback rehearsed |

## Exit conditions

- `NEW_FEATURE.md` exit conditions plus every gate above; **or** stopped at a gate with the owner's decision pending, recorded in `tasks/STATUS.md`.

## Human approval required

- Every policy interpretation: thresholds, inclusivity, precedence, fallbacks, reason codes.
- Version activation (by someone other than the proposer), canary thresholds, and go/no-go after the canary.
- Accepting parity differences or golden-set outcome changes.
- Any correction of historical financial records.
