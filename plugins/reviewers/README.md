# reviewers

Independent, read-only specialist reviewers. Each one gives a verdict on a change it did not write; the implementer never approves its own work. The Software Factory's `code-review`, `observability-review`, `security-review` and `fintech-feature` workflows use them when installed.

## Agents

- **[observability-engineer](agents/observability-engineer.md)**: Instrumentation value, correlation coverage, sensitive logging, severity, volume and cardinality.
- **[security-auditor](agents/security-auditor.md)**: Authz and IDOR, injection, SSRF, webhook verification, secrets and data exposure, with exploit scenarios.
- **[fintech-domain-reviewer](agents/fintech-domain-reviewer.md)**: Decision logic against the approved credit and risk policy: thresholds, precedence, fallbacks, reasons, versions, authority.
- **[financial-invariant-reviewer](agents/financial-invariant-reviewer.md)**: Exact arithmetic, duplicates, concurrency, immutable history, atomic audit records, migration evidence and cross-service consistency.
