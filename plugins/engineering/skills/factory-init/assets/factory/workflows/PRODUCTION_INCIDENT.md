# Workflow: Production Incident

> **Scope:** Project-agnostic. Applies when production behavior is broken, degraded, incorrect, or exposing data.

## Purpose

Help humans restore service and correctness quickly and safely, then find the root cause and prevent recurrence. The agent's role is **evidence and analysis**; production actions stay with the authorized humans.

## Entry conditions

- A human reports or confirms a production problem (alert, customer report, data anomaly).

## Inputs

- Symptoms: what is wrong, since when, who is affected, how it was detected.
- Access the humans grant: logs, metrics, traces, dashboards, recent deploys and configuration changes. The agent never assumes production access.

## Outputs

- A running incident log: timeline, evidence, hypotheses (confirmed or refuted), actions taken by humans.
- Mitigation recommendations with their risks.
- After resolution: root cause, fix through `BUG_FIX.md`, follow-up tasks, and a short review.

## Execution steps

1. **Establish facts**: impact (who, how many, since when), severity, and whether data is being corrupted or exposed. Data exposure or corruption is escalated to the owner immediately.
2. **Correlate with changes**: recent deploys, configuration and feature-flag changes, dependency incidents, traffic changes.
3. **Gather evidence read-only**: logs by correlation id, error rates, latency, queue depth, dead-letter queues, database health. Never run writes, migrations, or data fixes against production.
4. **Recommend mitigation** that reduces impact fastest with the least risk: roll back the deploy, disable a flag, scale out, pause a consumer, switch to a documented degraded mode. State each option's risk. **Humans decide and execute.**
5. **Verify mitigation** with the same signals that showed the problem.
6. **Diagnose the root cause** once stable: reproduce outside production, hypothesis by hypothesis.
7. **Fix** through `BUG_FIX.md` (regression test first); data corrections through `DATABASE_MIGRATION.md` with approval, as new records rather than silent overwrites where history matters.
8. **Close**: timeline, root cause, contributing factors, what detected it and how fast, follow-ups (tests, alerts, runbooks) with owners.

If the `debugging-and-error-recovery`, `distributed-tracing-and-correlation`, and `financial-system-reliability` skills are available, use them.

## Quality gates

| Gate | Passes when |
|---|---|
| Mitigated | The signals that showed the problem are back to normal |
| Explained | Root cause stated with evidence, not inferred from the fix working |
| Prevented | A regression test and any missing alert or runbook exist as tasks or changes |

## Exit conditions

- Service and data correct, root cause recorded, follow-ups owned; **or** handed over to the humans with the incident log current.

## Human approval required

- **Every production action**: rollbacks, flag changes, scaling, consumer pauses, data corrections, re-processing.
- Communication to customers or regulators.
- Closing the incident.
