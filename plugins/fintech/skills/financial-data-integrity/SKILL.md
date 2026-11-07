---
name: financial-data-integrity
description: Keeps financially relevant data correct: invariants enforced by constraints and checked by queries, immutable history, duplicate and lost-update prevention, cross-service reconciliation, exact money, and evidence-validated migrations. Use when writing or reviewing code that reads and updates limits, balances, decisions or other financial records (races, retries, duplicates), migrating such data, or investigating inconsistent records.
---

# Financial Data Integrity

## Overview

In financial systems, a wrong number that looks plausible is worse than a crash: it propagates into decisions, reports, and customer outcomes before anyone notices. Integrity means the data obeys its invariants now, still says what it said about the past, has no silent duplicates, agrees across services, and survives migrations unchanged. This skill makes those properties explicit, enforced where possible, and continuously checkable.

## When to use

- Changing schemas, write paths, or jobs for data used in credit scoring, eligibility, limits, pricing, or other financial decisions.
- Migrating or backfilling such data, or moving it between services.
- Investigating inconsistent, duplicated, or unexplained records.

**When not to use:** schema mechanics in general → `database-design`, `database-migrations`. Decision logic itself → `credit-scoring-and-eligibility`, `risk-decision-engineering`. Arithmetic → `money-and-decimal-arithmetic`.

## Inputs and context

1. The entities and their invariants, from the spec, business rules (`BR-n`), and existing code. Ask for invariants that only exist in people's heads.
2. Which services own and which consume each entity, and how data flows between them (APIs, events, batch exports).
3. Volumes and change rates; existing reconciliation or data quality jobs.
4. Regulatory or policy retention requirements for historical data.

## Process

1. **Write the invariant catalog** for the entities touched ([references/invariant-checks.md](references/invariant-checks.md)): what must always hold ("every decided application has exactly one final decision", "a limit is never negative", "a decision's rule version exists"). Each invariant gets an id, an owner, and a check query.
2. **Enforce what the database can**: `NOT NULL`, foreign keys, unique keys (including "one active" rules), `CHECK` constraints where the engine enforces them. Enforce the rest in one domain function that every write path calls, and check it with the catalog queries.
3. **Keep history immutable.** Decisions and other financially relevant facts are inserted, never updated in place. Corrections are new records referencing the original, with a reason and an actor. Inputs a decision depended on are snapshotted with it (`financial-auditability`).
4. **Prevent duplicates at write time** with natural-key unique constraints and idempotency keys (`api-design`, `async-messaging`); then **detect** what slipped through with periodic queries on near-duplicate keys (same customer, product, and window).
5. **Make concurrent writes safe** for read-modify-write paths (limits, counters, status transitions) with conditional updates or row locks (`mysql-engineering`). Lost updates in financial data are integrity failures.
6. **Reconcile across services.** Where two services hold views of the same facts, run a reconciliation job: counts and sums per period, per-entity comparison of key fields or hashes, and a report of mismatches by category. Alert on mismatch thresholds. Never "fix" mismatches automatically without a rule the owner approved.
7. **Validate migrations with evidence**: before and after row counts per category, sums of monetary columns, invariant queries, checksums or sampled per-row comparisons between old and new. Keep the results in the migration's report.
8. **Represent money exactly** (`DECIMAL` plus currency; `money-and-decimal-arithmetic`); never derive stored financial values from floats.
9. **Make integrity observable**: invariant-check results as metrics, reconciliation mismatch counts, duplicate-detection counts, with alerts (`observability-engineering`).

## Output

- The invariant catalog (in `engineering/DATA_MODEL.md` or a dedicated section): id, statement, enforcement (constraint / domain code / check only), check query, schedule.
- Constraints and domain checks in code; reconciliation or check jobs where needed.
- For migrations: a validation report with before/after evidence.

## Verification

- [ ] Every invariant touched by the change is enforced or checked, and its check query returns zero violations on realistic data.
- [ ] Financial facts are append-only; corrections reference the original with reason and actor.
- [ ] Duplicate-prevention constraints exist; a duplicate-submission test passes.
- [ ] Concurrent-update tests pass on the production engine.
- [ ] Migrations have before/after counts, sums, and invariant results recorded.
- [ ] Reconciliation mismatches (if applicable) are measured, alerted, and routed to a human-approved fix process.

## Escalation

Always ask before: correcting or deleting historical financial records; auto-repairing reconciliation mismatches; changing an invariant's definition; or proceeding with a migration whose before/after evidence doesn't match. Report discovered integrity violations in production as incidents, with counts and scope, not as quiet fixes.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Just update the record to the right value." | Then nobody can explain the past. Insert a correction with reason and actor. |
| "The migration ran without errors." | Errors aren't the risk; silently changed values are. Compare counts, sums and samples. |
| "The two services are always in sync." | Prove it with a reconciliation job; otherwise you'll find out from a customer. |

## References

- [references/invariant-checks.md](references/invariant-checks.md): invariant catalog format, check query examples, reconciliation and migration validation queries.
