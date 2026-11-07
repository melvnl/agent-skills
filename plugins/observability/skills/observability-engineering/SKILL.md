---
name: observability-engineering
description: Designs observability for backend systems across logs, metrics and traces: what to observe, service health and dependency signals, cardinality and cost, dashboards and alerting. Use when designing a feature or service, writing a design's observability plan, defining SLOs or alerts, or when production behavior can't be explained.
---

# Observability Engineering

## Overview

Observability is the ability to answer new questions about production from the signals the system already emits. Logs explain individual events, metrics show rates and distributions cheaply, and traces show where time and failures go across services. This skill decides which pillar carries which question, so each feature ships with the signals needed to run it, without paying for noise.

## When to use

- Designing a feature or service (the Software Factory `DESIGN.md` *Observability plan* section).
- Defining service health, SLIs/SLOs, dashboards, or alerts.
- An incident was hard to diagnose, or a system's behavior can't be explained from current signals.

**When not to use:** writing the actual log calls → `structured-logging-and-instrumentation`. Propagating ids → `distributed-tracing-and-correlation`. Field sensitivity → `logging-security-and-redaction`. Reviewing a diff → `observability-code-review`.

## Inputs and context

1. The spec: critical operations, NFRs (latency, availability, freshness), business-critical outcomes.
2. The existing observability stack: log platform, metrics system (Prometheus, StatsD/Datadog, CloudWatch), tracing (OpenTelemetry, vendor APM, X-Ray), alert routing. Reuse it; don't add a pillar's tooling without a decision.
3. Existing dashboards, alerts, and naming conventions for metrics.
4. Dependencies the feature calls (databases, caches, queues, external APIs) and their failure modes.
5. Traffic expectations: requests per second, message rates, batch sizes. Needed for volume and cost estimates.

## Process

1. **List the questions on-call must answer** for this feature: "Is it working?", "For whom is it failing?", "Which dependency is slow?", "Did the decision logic change outcomes?". Derive signals from questions, not from code structure.
2. **Identify critical operations** (the few whose failure hurts users or money) and their failure scenarios, from the design's error-handling section.
3. **Assign each question to a pillar** with the table below.
4. **Define service health**: for request-driven code, RED (Rate, Errors, Duration) per important endpoint; for consumers and jobs, throughput, failure rate, lag/age of oldest message, processing duration; for resources, USE (Utilization, Saturation, Errors).
5. **Cover dependencies**: per dependency, call rate, error rate, latency distribution, timeouts, and circuit/fallback state. These are the first things checked in an incident.
6. **Control cardinality**: metric labels take bounded values only (endpoint *template*, status class, dependency name, outcome enum). Never user ids, request ids, raw URLs, or error messages as labels. Those belong in logs and traces.
7. **Correlate the pillars**: logs carry `trace_id`/`request_id`; metrics may carry exemplars (trace ids on samples) if the stack supports them; traces carry the same service and operation names as metrics.
8. **Design alerts on symptoms**: user-visible error rate and latency against SLOs, consumer lag, absence of expected activity (job didn't run). Avoid alerting on causes (CPU) unless they reliably predict user impact. Every alert has an owner and a runbook link.
9. **Estimate volume and cost** for new logs, metric series (labels multiply), and trace sampling.
10. **Write the observability plan** using [references/observability-plan-template.md](references/observability-plan-template.md), and get it reviewed with the design.

### Which pillar answers what

| Question | Pillar | Why |
|---|---|---|
| How many, how fast, how often failing (aggregate) | **Metrics** | Cheap at any traffic; good for alerts and dashboards |
| What happened to *this* request, user, or message | **Logs** (+ trace) | High detail, searchable by id |
| Where did the time go across services | **Traces** | Causal, cross-service timing |
| Did a business decision change distribution (approval rate, rule hits) | **Metrics** by outcome enum, with **logs** for individual cases | Aggregate trend + drill-down |
| Is the system alive / did the job run | **Metrics** (heartbeat, last-success timestamp) + absence alert | Logs can't alert on silence well |

Metric design and alerting details: [references/metrics-and-alerting.md](references/metrics-and-alerting.md).

## Output

The **Observability plan** section of `DESIGN.md` (or the design doc in use), filled from the template: important operations; required identifiers; events to log; error scenarios and how each is detected; sensitive fields and their handling; metrics (name, type, labels, unit); traces (spans, propagation); dashboards and alerts (condition, threshold, owner, runbook); volume and cost estimate; decisions and deferrals.

## Verification

- [ ] Every critical operation has a success/failure signal and a latency signal.
- [ ] Every external dependency has rate, error and latency coverage.
- [ ] Each failure scenario in the design names how it is detected (metric, log event, alert) or is explicitly accepted as undetected.
- [ ] All metric labels are bounded; the series count estimate is written down.
- [ ] Alerts are symptom-based, have thresholds tied to an SLO or a stated rationale, an owner, and a runbook.
- [ ] Sensitive fields are listed and handled per `logging-security-and-redaction`.
- [ ] After implementation: signals were observed in a real run (local, staging, or test capture), not assumed.

## Escalation

Ask when: SLO targets aren't defined (they are a product decision); the plan requires a new observability tool, agent, or paid tier; alert routing or on-call ownership is unknown; or retention and cost limits are unclear.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "We'll add monitoring after launch." | The first incident is when you need it most. |
| "Log it and we can count from logs." | Counting from logs is slow, costly, and breaks when sampling or retention changes. Use a metric. |
| "Add `user_id` as a label so we can filter." | Unbounded labels explode series count and cost. Filter in logs and traces. |
| "Alert on everything to be safe." | Noisy alerts get ignored; then the real one is too. |

## References

- [references/observability-plan-template.md](references/observability-plan-template.md): the section to add to a design.
- [references/metrics-and-alerting.md](references/metrics-and-alerting.md): read when defining metrics, SLOs, dashboards, or alerts.
