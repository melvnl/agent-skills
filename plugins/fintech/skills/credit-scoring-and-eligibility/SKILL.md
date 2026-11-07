---
name: credit-scoring-and-eligibility
description: Builds and changes credit scoring and eligibility pipelines that are consistent, versioned, explainable and reconstructable: one source of truth for rules, deterministic evaluation, immutable decision records, owner-defined fallbacks, golden-dataset regression tests, and parity-proven service migrations. Use when implementing, changing or reviewing scoring, eligibility rules, thresholds, limits or decision services, or migrating decision logic between services.
---

# Credit Scoring and Eligibility

## Overview

A credit or eligibility decision must be the same for the same inputs, explainable to the applicant and to auditors, and reconstructable years later, even after rules, models, and services have changed. Defects here are business and regulatory problems: inconsistent decisions between channels, thresholds drifting between copies of the rules, an outage silently approving applicants, a migration that quietly changes approval rates. This skill structures decision pipelines so those properties hold and stay proven.

## When to use

- Implementing or changing scoring, eligibility rules, thresholds, limit assignment, or decision APIs.
- Adding or changing inputs (bureau data, internal history, features).
- Migrating decision logic between services or rewriting a decision engine.
- Investigating inconsistent or unexplainable decisions.

**When not to use:** generic rule-engine mechanics (tables, precedence, policy versions) → `risk-decision-engineering`. Data invariants and reconciliation → `financial-data-integrity`. The audit record's integrity and access → `financial-auditability`.

## Inputs and context

1. **The decision policy** as approved by its owner: inputs, scores, thresholds with inclusivity, outcomes (approve, reject, manual review, limit), reason codes, and the fallback policy. Never infer policy from code alone when it is ambiguous: ask.
2. The pipeline as built: where inputs come from, where features are computed, which service owns the rules, how decisions are stored and published.
3. Versioning in place for rules, configuration, and models.
4. Volumes, latency budget per stage, and dependency SLOs (bureau, internal services).
5. Historical decisions available for regression and parity datasets (synthetic or properly de-identified for development use).

## Process

1. **Map the pipeline** in stages: collect inputs → validate → derive features → score → apply eligibility rules → determine outcome and limit → record decision → publish and notify. Name the owner of each stage and its failure modes.
2. **Keep one source of truth for the policy.** One service or module owns rule evaluation; other services call it or consume its decisions. Never copy thresholds or rules into a second codebase (frontends, other services, SQL reports): copies drift. If a copy exists, plan its removal.
3. **Version everything a decision depends on**: rule set version, configuration version, model version, feature definitions. Versions are immutable once used; changes create new versions with an effective date. Activation is a deliberate, audited change (`financial-auditability`).
4. **Evaluate deterministically**: the same inputs and versions always produce the same outcome. Inject the evaluation time; no hidden reads of mutable state mid-evaluation; a defined rule order; no reliance on dict or set iteration order where it matters; exact decimal arithmetic (`money-and-decimal-arithmetic`).
5. **Record every decision immutably** ([references/decision-record-and-parity.md](references/decision-record-and-parity.md)): the input snapshot (or a reference to an immutable snapshot), derived feature values, score, versions, rules evaluated with results, outcome, limit, reason codes, timestamps, correlation id, the deciding service, and whether a fallback applied.
6. **Make decisions explainable**: stable reason codes mapped to rules, ordered by significance, suitable for customer-facing explanation and adverse-action notices where policy requires them, without exposing internal model details beyond policy.
7. **Define failure behavior with the owner.** For each dependency failure (bureau timeout, missing data, internal service down): retry within budget, then the **owner-approved fallback** (manual review, defer and re-evaluate, reject with a specific reason). Never default to approval silently. Record `fallback=true` and the reason in the decision.
8. **Budget latency per stage** and set timeouts accordingly (`distributed-systems`). Cache external data only within consent, policy, and freshness rules.
9. **Test as a regression suite**:
   - boundary tests at every threshold (below, at, above);
   - a **golden dataset** of representative and edge-case inputs with approved expected outcomes and reasons, run on every change;
   - property checks the policy actually guarantees (e.g. "a higher score never produces a worse outcome, all else equal", only if stated);
   - determinism tests (evaluate twice, compare records).
10. **Prove parity when migrating** logic between services or engines: replay historical inputs through old and new; run the new one in shadow on live traffic; compare outcomes, limits and reasons; categorize every difference; agree the acceptance threshold with the owner (often zero unexplained differences); cut over behind a flag with rollback ready.
11. **Observe decision execution**: decisions by outcome, version and reason code; fallback rate; latency per stage; input-missing rates; alerts on distribution shifts after deploys or version activations (approval rate change beyond a set band) (`observability-engineering`).
12. **Protect inputs**: credit data is tier-2 sensitive; minimize it in logs, events, and responses (`logging-security-and-redaction`).

## Output

Decision code with versioned, deterministic evaluation; the decision record; regression and parity suites; and a decision design note covering stage ownership, versions, fallback policy (with owner approval reference), latency budget, and decision metrics.

## Verification

- [ ] Rules and thresholds exist in exactly one place; any other copy is listed for removal.
- [ ] Every decision record contains inputs (or snapshot reference), versions, rule results, outcome, reasons, fallback flag, correlation id.
- [ ] Re-evaluating a stored decision's inputs with its versions reproduces its outcome (test).
- [ ] Boundary tests at every threshold and the golden dataset pass; the run output is recorded.
- [ ] Each dependency failure has an owner-approved fallback that is tested and recorded on the decision.
- [ ] For migrations: parity report with categorized differences and owner sign-off.
- [ ] Decision metrics and distribution-shift alerts exist.

## Escalation

Always ask the owner before: changing thresholds, rules, outcomes, reason codes, or fallback behavior; activating a new rule or model version; accepting parity differences; or using real customer data outside production. Ambiguous policy is never resolved by the engineer's judgment.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The frontend needs the threshold too; I'll copy it." | Now there are two policies. Expose the decision or a pre-check endpoint instead. |
| "If the bureau is down, approve small amounts." | That is a credit policy decision, not an engineering default. Ask. |
| "Store the outcome; we can recompute the rest." | Not after the rules change. Snapshot what the decision used. |
| "The new engine matches on the tests." | Tests cover the cases you thought of. Shadow on real traffic and compare. |

## References

- [references/decision-record-and-parity.md](references/decision-record-and-parity.md): decision record schema, golden dataset structure, parity comparison procedure.
