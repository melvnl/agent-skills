---
name: financial-auditability
description: Makes financially relevant actions and decisions reconstructable with append-only audit records, separate from diagnostic logs, written atomically with the change and capturing actor, action, object, reason, versions and before/after state, with integrity protection, retention, restricted access and as-of reconstruction. Use for decisions, overrides, limit or policy changes, and privileged access.
---

# Financial Auditability

## Overview

"Why was this applicant rejected last March, by which rules, and who changed the threshold since?" must have a factual answer, years later. Operational logs can't provide it: they are sampled, rotated, mutable in practice, and designed for debugging, not evidence. This skill builds a separate audit trail: durable records, written in the same transaction as the change they describe, append-only, integrity-protected, retained per policy, and queryable to reconstruct what was true at any point in time.

## When to use

- Recording credit or eligibility decisions, manual reviews, and overrides.
- Changes to limits, policy and rule versions, configuration that affects decisions, roles and permissions.
- Privileged or break-glass access to sensitive data, and exports.
- Designing how to answer "what happened and who did it" for a feature.

**When not to use:** debugging and operational visibility → `structured-logging-and-instrumentation` (operational logs are not a substitute for audit records). Who is allowed to act → `financial-authorization`.

## Inputs and context

1. Audit requirements from policy, regulation, or the owner: which actions, what detail, retention period, who may read the trail.
2. Existing audit mechanisms (audit tables, history libraries such as django-simple-history, an audit service, WORM storage) and their guarantees.
3. Identity sources for actors (users, services) and the trusted clock.
4. Sensitive data involved, and its retention and access rules.

## Process

1. **Separate audit from diagnostics.**

   | | Diagnostic log | Audit record |
   |---|---|---|
   | Purpose | debug, operate | evidence, reconstruction |
   | Completeness | sampled, best effort | every in-scope event, guaranteed |
   | Mutability | rotated, deleted by retention tooling | append-only, protected |
   | Write path | async, may drop | same transaction as the change (or outbox) |
   | Access | engineers | restricted; access itself audited |
   | Retention | days to weeks | per policy, often years |

   A log line may also be emitted, but it never replaces the record.
2. **Define the in-scope events** with the owner, and the record for each: `event_id`, `occurred_at` (UTC, server clock), `actor` (user id or service identity, plus the on-behalf-of user for service actions), `action`, `object_type` and `object_id`, `reason` (required for overrides and manual actions), relevant **versions** (rule set, config, model), **before and after** state (or references to immutable snapshots), `correlation_id`, and the result.
3. **Write atomically with the change**: insert the audit record in the same database transaction as the state change, so no change exists without its audit record (or both go through the transactional outbox to an audit service: `distributed-systems`). If the audit write fails, the change fails.
4. **Make the trail append-only**: no update or delete paths in code; database grants that allow only `INSERT` and `SELECT` for the application's audit writer where feasible; or ship to write-once storage (e.g. S3 Object Lock) for long retention. Corrections are new records referencing the original.
5. **Protect integrity** where the threat model needs it: per-record hashes and hash chaining (each record includes the previous record's hash) so tampering is detectable; periodic verification of the chain.
6. **Protect sensitive content**: store the minimum needed to reconstruct (references to snapshots instead of copying raw bureau data), encrypt sensitive fields where policy requires, restrict read access, and audit reads of the audit trail itself.
7. **Support reconstruction**: from a decision id, retrieve its inputs snapshot, versions, rule trace, and actor; from a date, determine which policy version, configuration, and permissions were active (effective-dated versions, `credit-scoring-and-eligibility`, `risk-decision-engineering`). Build and test these queries; reconstruction that only exists in theory fails during an audit.
8. **Apply retention deliberately**: per policy and per data type; archive before purge; never purge audit data silently or ad hoc.
9. **Test it**: every in-scope action produces exactly one audit record with the required fields; a failed audit write rolls back the change; update and delete of audit records are impossible through the application; reconstruction queries return the expected history.

## Output

The audit event catalog (event, trigger, fields, retention, readers), the audit write path, protection measures, reconstruction queries, and tests:

```markdown
| Event | Trigger | Key fields | Retention | Readers |
|---|---|---|---|---|
| decision.made | eligibility evaluation | decision_id, versions, outcome, reasons, input_snapshot_ref | per policy (e.g. 5y) | risk, compliance |
| decision.overridden | manual override | original_decision_id, new_decision_id, actor, reason_code, free_text | per policy | risk, compliance |
| policy.activated | version activation | version, proposer, approver, effective_at, diff_ref | per policy | risk, compliance, engineering leads |
```

## Verification

- [ ] Every in-scope action writes an audit record in the same transaction (test: force the audit insert to fail and assert the change rolled back).
- [ ] Records include actor, service, action, object, reason where required, versions, before/after or snapshot references, correlation id, UTC time.
- [ ] No application code path updates or deletes audit records; grants or storage enforce it where possible.
- [ ] Reconstruction queries for "explain decision X" and "what was active at time T" exist and are tested.
- [ ] Sensitive content is minimized, access-restricted, and access is audited.
- [ ] Retention is defined per event type.

## Escalation

The owner and compliance decide: the in-scope events, retention, readers, and integrity requirements. Escalate immediately if an in-scope action is found to happen without an audit record in production, or if audit data must be corrected or purged.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "We log every decision at INFO; that's our audit trail." | Logs get sampled, dropped under load, rotated, and are editable by whoever runs the log platform. |
| "Write the audit record asynchronously for speed." | Then a crash leaves changes without evidence. Same transaction or outbox. |
| "Store the full bureau response in the audit record." | Copying sensitive data widens exposure. Reference an immutable snapshot under the same controls. |
