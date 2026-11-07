# Observability plan (design section template)

Add this as a section of `specs/<F-ID>-<slug>/DESIGN.md` in Software Factory projects, or of the design doc in use. Keep it short; a small feature may need a few lines per heading. Write "None" rather than deleting a heading, so reviewers see it was considered.

```markdown
## Observability plan

### Questions on-call must answer
- {{e.g. Is eligibility evaluation succeeding? Which rule version produced a decision? Is the bureau slow?}}

### Important operations
| Operation | Entry point | Success signal | Failure signal | Latency signal |
|---|---|---|---|---|
| {{evaluate_eligibility}} | {{POST /v1/eligibility}} | {{metric outcome=success}} | {{metric outcome=failed + ERROR log}} | {{histogram duration_ms}} |

### Identifiers
| Id | Source | Propagated across | Notes |
|---|---|---|---|
| {{request_id}} | {{ingress middleware}} | {{API logs}} | {{existing}} |
| {{correlation_id / trace_id}} | {{...}} | {{API -> SQS -> worker}} | {{see distributed-tracing-and-correlation}} |

### Log events
| Event | Level | Fields | Why |
|---|---|---|---|
| {{eligibility_evaluation_completed}} | {{INFO}} | {{request_id, status, rule_version, duration_ms}} | {{outcome + latency per request}} |
Deliberately not logged: {{e.g. per-rule steps (volume), applicant attributes (PII)}}

### Error scenarios and detection
| Scenario | Detection | Response |
|---|---|---|
| {{bureau timeout}} | {{dependency error-rate metric; WARNING log with error_code}} | {{fallback decision; alert if > X% for 10m}} |

### Sensitive fields
| Field | Tier | Handling |
|---|---|---|
| {{national_id}} | {{2}} | {{never logged}} |

### Metrics
| Name | Type | Labels (bounded) | Unit |
|---|---|---|---|
| {{eligibility_evaluations_total}} | {{counter}} | {{outcome, rule_version}} | {{1}} |
| {{eligibility_evaluation_duration}} | {{histogram}} | {{outcome}} | {{ms}} |
Estimated new series: {{n}}

### Traces
{{spans added, propagation boundaries, sampling notes, or "relies on existing auto-instrumentation"}}

### Dashboards and alerts
| Alert | Condition | Threshold / SLO | Owner | Runbook |
|---|---|---|---|---|
| {{high failure rate}} | {{failed / total}} | {{> 2% for 10 min}} | {{team}} | {{link}} |

### Volume and cost
{{new log lines/day at expected traffic, new metric series, trace sampling}}

### Instrumentation decisions
- {{decision and rationale, including what was deferred and why}}
```
