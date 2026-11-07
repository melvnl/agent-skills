# Metrics and alerting

## Metric types

| Type | Use for | Notes |
|---|---|---|
| Counter | Events and outcomes (`requests_total`, `decisions_total{outcome}`) | Monotonic; compute rates at query time |
| Gauge | Current values (queue depth, in-flight jobs, last-success timestamp) | Sampled; can miss spikes between scrapes |
| Histogram | Latency and size distributions | Enables percentiles and SLO math across instances; choose buckets around the SLO threshold |
| Summary | Client-side quantiles | Quantiles can't be aggregated across instances; prefer histograms for services |

Averages hide tail latency. Track p95/p99 from histograms, plus error rate.

## Naming and labels

- Use the existing convention. If none: `<domain>_<thing>_<unit>`, with base units in the name (`_seconds`, `_bytes`, or `_ms` if the stack standardizes on ms), and `_total` for counters (Prometheus convention).
- Labels must be **bounded and low-cardinality**: route templates (`/v1/applications/{id}`, not the raw path), status class, outcome enum, dependency name, rule version.
- Series count ≈ product of each label's distinct values, per metric, per instance (where instance labels apply). Estimate it before adding a label.
- Never as labels: user/customer/request/trace ids, emails, raw URLs, exception messages, free text.

## Health models

- **RED** for request-driven services: Rate, Errors, Duration per important operation.
- **USE** for resources: Utilization, Saturation, Errors (connection pools, worker pools, queues).
- **Queues and consumers**: message age / oldest-message age (SQS `ApproximateAgeOfOldestMessage`), visible depth, processing rate, failure and dead-letter counts, redelivery counts.
- **Jobs**: last-success timestamp gauge, duration, items processed, failures. Alert on "no success in N hours".

## SLIs and SLOs

- SLI: a ratio of good events to valid events (e.g. requests answered successfully within 500 ms / all valid requests).
- SLO: the target for that ratio over a window (e.g. 99.5% over 30 days). The error budget is the remainder.
- Targets are product decisions; propose, don't impose.

## Alert design

- Page on **symptoms users feel** (error rate, latency SLO burn, consumer lag) and on **silence** (job didn't run, no traffic where traffic is expected).
- Burn-rate alerting (from the Google SRE Workbook) pairs a fast and a slow window to catch both sharp and slow budget burn. A common starting point for a 30-day SLO is a page when the 1-hour burn rate exceeds 14.4 (2% of the budget in one hour), confirmed by a 5-minute window, plus a ticket-level alert on a slower multi-hour burn.
- Every alert: owner, severity, runbook link, and a threshold rationale. Delete alerts nobody acts on.
- Use `for:` durations or equivalent to avoid flapping on single samples.

## Dashboards

One overview per service: RED for top operations, dependency health, saturation, recent deploys and flag changes. Drill-down dashboards per critical operation. Panels show units and thresholds. Link panels to log and trace queries filtered by the same service and operation.

## Platform notes

- Prometheus: pull model; histograms with `le` buckets; avoid high-cardinality labels.
- StatsD / DogStatsD: push; tags multiply cost the same way labels do.
- CloudWatch: custom metrics are billed per metric and dimension combination; Embedded Metric Format (EMF) emits metrics from structured log lines, which is useful in Lambda and containers without a metrics agent.
- OpenTelemetry metrics: exporters to any of the above; keep instrument names stable across services.
