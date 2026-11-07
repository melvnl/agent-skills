# melvin-observability

Meaningful backend observability: logs that are structured, concise, correlated across services, and safe from PII and secrets. Useful observability, not maximum log volume.

## Skills

- **[structured-logging-and-instrumentation](skills/structured-logging-and-instrumentation/SKILL.md)**: Decides what deserves a log entry and adds structured, correlated, PII-safe logs using the project's existing logger. Applied to every backend change.
- **[distributed-tracing-and-correlation](skills/distributed-tracing-and-correlation/SKILL.md)**: Preserves request, correlation and trace context across HTTP, SQS/SNS, workers and async code with the fewest identifiers possible.
- **[logging-security-and-redaction](skills/logging-security-and-redaction/SKILL.md)**: Classifies data before it reaches logs; keeps secrets, PII and customer financial data out through allowlisted fields, masking or keyed pseudonyms.
- **[observability-engineering](skills/observability-engineering/SKILL.md)**: Designs logs, metrics and traces for a feature or service: health and dependency signals, cardinality and cost, SLO-based alerting, and the design's observability plan.
