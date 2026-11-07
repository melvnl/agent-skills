# Resilience patterns

## Transactional outbox

```sql
CREATE TABLE outbox_event (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  event_id CHAR(36) NOT NULL UNIQUE,          -- consumers dedupe on this
  topic VARCHAR(128) NOT NULL,
  payload JSON NOT NULL,                       -- no secrets; minimal personal data
  headers JSON NOT NULL,                       -- correlation_id, traceparent
  created_at DATETIME(6) NOT NULL,
  published_at DATETIME(6) NULL,
  attempts INT NOT NULL DEFAULT 0,
  KEY idx_unpublished (published_at, id)
);
```

Write path, in one transaction:

```python
with transaction.atomic():
    decision = record_decision(application)
    OutboxEvent.objects.create(event_id=new_uuid(), topic="decision.made",
                               payload=decision_event(decision), headers=current_trace_headers(),
                               created_at=now_utc())
```

Relay (separate worker): claim unpublished rows (`FOR UPDATE SKIP LOCKED` on MySQL 8.0.1+), publish, mark `published_at`, increment `attempts` on failure with backoff, alert on age of the oldest unpublished row. Publishing is at least once, so consumers dedupe on `event_id`. Purge published rows after a retention period.

## Consumer deduplication

```sql
CREATE TABLE processed_message (
  consumer VARCHAR(64) NOT NULL,
  message_key VARCHAR(128) NOT NULL,          -- event_id or business key
  processed_at DATETIME(6) NOT NULL,
  PRIMARY KEY (consumer, message_key)
);
```

In the **same transaction** as the consumer's state change, insert the key; a duplicate-key error means already processed: acknowledge and skip. Inserting the key in a separate transaction reintroduces the race.

## Retry policy

| Error | Retry? |
|---|---|
| Connect timeout, connection reset | yes (request likely not processed) |
| Read timeout on a write | only with an idempotency key, or after querying state |
| 429 | yes, honoring `Retry-After` |
| 502 / 503 / 504 | yes |
| 500 | maybe, if the operation is idempotent |
| 400 / 401 / 403 / 404 / 409 / 422 | no |

Delay: `base * 2^attempt`, capped, plus full jitter (`random.uniform(0, delay)`). Attempts: 2–3 for synchronous paths (the user is waiting); more for background work, bounded by a deadline.

## Circuit breaker

Starting parameters to tune with real data: open after ≥ 50% failures over a window of ≥ 20 calls; stay open 30 s; half-open with a few probe calls. While open: fail fast with the fallback, log state changes at WARNING, emit a breaker-state metric.

## Saga state

```text
application_decision_saga: STARTED -> SCORE_FETCHED -> DECISION_RECORDED -> NOTIFIED -> DONE
                                  \-> FAILED_SCORE -> COMPENSATED (release reservation)
```

Persist the state and step outputs; each step and compensation is idempotent and keyed by the saga id; a sweeper resumes or compensates stuck sagas.
