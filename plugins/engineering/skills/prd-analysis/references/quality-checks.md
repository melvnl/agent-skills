# PRD quality checks

## Contradictions

Look for pairs of statements that can't both hold:

| Kind | Example |
|---|---|
| Numeric | "limit is 5 per day" (§2) vs "up to 10 attempts daily" (§7) |
| State / lifecycle | "rejected applications can be resubmitted" vs "rejected is a terminal state" |
| Permission | "only admins approve" vs "reviewers can approve below X" with no threshold for X |
| Temporal | "real-time" vs "processed in nightly batch" |
| Scope | a feature listed in scope and in out-of-scope |
| Inclusivity | "above 600" vs "600 or more" for the same threshold |

Cite both sides with source references.

## Ambiguity signals

- Vague qualifiers: *fast, quickly, real-time, scalable, secure, robust, user-friendly, intuitive, seamless, efficient, flexible, appropriate, reasonable, as needed, etc., and so on, TBD, may, should (when intent is "must")*.
- Undefined terms or acronyms; a term used before it is defined; one concept with several names.
- Missing actor ("the system notifies": who? by which channel?).
- Missing boundary or inclusivity (thresholds, date ranges, "within 24 hours" from what event?).
- Missing failure behavior ("calls the bureau" but nothing on timeout or error).
- Missing units or currency; missing time zone for date-based rules.
- Passive voice hiding responsibility ("records are reviewed").

## Duplicates

Same requirement stated twice, possibly with drift. Keep the most precise phrasing, cite all sources, and flag any differences as a contradiction.

## NFR checklist

Mark each present (cite), missing, or not applicable (say why):

| Category | Typical questions |
|---|---|
| Performance | latency targets (p95/p99), throughput, batch windows |
| Availability / reliability | uptime target, degradation behavior, RPO/RTO |
| Scalability | expected volumes now and at horizon |
| Security | authentication, authorization model, secrets, threat considerations |
| Privacy / data protection | personal data collected, purpose, retention, deletion, consent |
| Auditability | which actions and decisions must be reconstructable, by whom, for how long |
| Observability | what operators must see; alerting expectations |
| Data integrity | consistency guarantees, idempotency, duplicate handling |
| Compliance / regulatory | applicable regulations and internal policies |
| Compatibility / migration | existing clients, data, APIs that must keep working |
| Internationalization | time zones, currency, locale, language |
| Accessibility | when there is a UI |

## Testability

A requirement is testable when an observable outcome can be checked. Flag statements with no observable outcome, or with outcomes that depend on undefined terms.

## AI-generation artifacts

- Generic, symmetric sections with no project-specific detail ("The system shall be secure, scalable and maintainable").
- Integrations, vendors, or regulations nobody else in the document mentions.
- Suspiciously round or inconsistent numbers repeated with variations.
- Requirements that contradict the domain (e.g. "store the full card number for convenience").
- Feature lists that repeat with renamed items.
- Confident statements of current-system behavior that the codebase doesn't support. Check them.

Treat these as questions, not as errors to correct silently.
