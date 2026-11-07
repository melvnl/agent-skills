---
name: financial-system-reliability
description: Keeps financial decision systems correct and available under failure: owner-defined fail-closed or degraded modes, end-to-end idempotency, safe replay and recovery from durable inputs, rerunnable checkpointed batch jobs, deploy safety with decision-distribution canaries and fast rollback, peak capacity, third-party quotas, and tested failure paths. Use when designing or changing critical financial services, jobs, deployments, or recovery procedures.
---

# Financial System Reliability

## Overview

For a financial decision service, "up but wrong" is worse than "down": a bug or degraded dependency that keeps answering produces decisions that are hard to find and harder to reverse. Reliability here means correctness first, then availability: every failure mode has a defined, owner-approved behavior, every effect happens once, recovery replays durable inputs safely, and deploys are watched for changes in *outcomes*, not just errors.

## When to use

- Designing or changing critical services: decisioning, scoring, limit management, financial data pipelines.
- Scheduled and batch jobs that compute or change financial data.
- Deployment, rollout, and rollback planning for such services.
- Defining recovery procedures, RPO/RTO, or degraded modes.

**When not to use:** general timeout, retry, outbox, and saga mechanics → `distributed-systems` (used from here). Live incident handling → the factory `PRODUCTION_INCIDENT` workflow.

## Inputs and context

1. The service's criticality and its SLOs; RPO/RTO targets if defined.
2. Failure modes and their business impact, from the design and past incidents.
3. Deployment mechanics: feature flags, canary or blue/green support, rollback time.
4. Load patterns: peaks (paydays, campaigns, month end), batch windows, third-party quotas and contracts.
5. Existing runbooks and on-call arrangements.

## Process

1. **Classify each failure mode and choose its behavior with the owner**: *fail closed* (reject or defer the operation: usual for approvals, limit increases, anything granting credit), *degraded* (a defined reduced mode such as manual review or deferred evaluation), or *fail open* (only where the owner explicitly accepts the risk). Record the choice per dependency and per operation; implement and test it.
2. **Guarantee single effects end to end**: idempotency keys at the API, dedup in consumers, unique constraints on decisions and financial facts, conditional state transitions (`distributed-systems`, `financial-data-integrity`). Test duplicate requests, redelivered messages, and retried jobs.
3. **Design for replay**: keep durable, immutable inputs (requests, events, snapshots) so a period can be reprocessed after a bug fix. Reprocessing must be idempotent and produce **new** superseding records, never silent overwrites, and its scope and results are reviewed before effects such as notifications are re-sent.
4. **Make batch and scheduled jobs rerunnable**: process in checkpointed chunks; record progress; make each chunk idempotent; define behavior for partial failure (resume from the checkpoint); use explicit business dates and time zones instead of "now"; alert when a job didn't run or didn't finish in its window.
5. **Deploy safely**:
   - ship decision-logic changes behind flags or versioned activation (`risk-decision-engineering`);
   - canary with **decision-distribution monitoring**: compare approval and rejection rates, limit distribution, fallback rate, and reason codes between canary and baseline, not only error rates and latency;
   - keep rollback fast and rehearsed; schema changes follow expand-contract so rollback stays possible (`database-migrations`).
6. **Plan capacity for peaks**: load-test at expected peak plus headroom (`performance-engineering`); protect dependencies with concurrency limits; respect third-party quotas with rate limiting and queueing rather than failing randomly at the limit.
7. **Define recovery**: backups and point-in-time recovery meeting RPO; a tested restore procedure; runbooks for the top failure modes (dependency down, queue backlog, bad deploy, bad policy version) with owners.
8. **Test failure paths**, not only happy paths: dependency timeouts and errors (stubbed), duplicate and out-of-order messages, a job crash midway and resume, a rollback of a decision-logic deploy in staging.
9. **Observe correctness signals** alongside health: decision distribution by version, fallback rate, reconciliation mismatches, job completion and lag, DLQ depth (`observability-engineering`), with alerts that route to the owner of the decision, not only to infrastructure on-call.

## Output

A reliability note for the service or change:

```markdown
| Failure | Behavior (owner-approved) | Implementation | Test |
|---|---|---|---|
| Bureau unavailable | degraded: manual review queue, reason BUREAU_UNAVAILABLE | breaker + fallback in evaluator | test_bureau_down_routes_to_manual_review |
| Duplicate submission | single decision returned | idempotency key + unique constraint | test_duplicate_submission |
| Bad policy version deployed | rollback: reactivate previous version (< 5 min) | versioned activation | staging rehearsal 2026-11-05 |
Canary checks: approval rate within ±2 pp of baseline over 30 min; fallback rate < 1%.
Peak: 3x normal at month end, load-tested 4x on staging.
```

## Verification

- [ ] Every identified failure mode has an owner-approved behavior, implemented and tested.
- [ ] Duplicate, redelivery, and retry tests show single effects.
- [ ] Replay of a period is possible from durable inputs and produces superseding records (tested on a fixture period).
- [ ] Batch jobs resume from checkpoints after a simulated crash.
- [ ] Canary criteria include decision-distribution checks; rollback was rehearsed.
- [ ] Peak load test results recorded; third-party quotas protected.
- [ ] Runbooks exist for the top failure modes.

## Escalation

The owner decides fail-closed vs degraded vs fail-open behavior, canary thresholds, and any reprocessing that changes customer-visible outcomes. Escalate immediately when a deploy shifts decision distributions beyond thresholds, or when replay would change past outcomes.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Availability first: keep approving during the outage." | Unrecoverable credit decisions are worse than a delay. Fail closed unless the owner accepts the risk. |
| "The canary had no errors." | Wrong decisions don't throw errors. Compare outcome distributions. |
| "We'll fix the data after the incident by updating rows." | Then the trail is gone. Replay into superseding records. |
