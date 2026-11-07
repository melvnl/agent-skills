---
name: async-messaging
description: Designs and implements reliable asynchronous messaging on AWS SQS and SNS: standard vs FIFO choice, versioned message envelopes, idempotent consumers, visibility timeouts, delete-after-success, dead-letter queues and redrive, retries with backoff, fan-out and filtering, poison messages, and graceful shutdown. Use when publishing or consuming queue or topic messages, or designing event contracts between services.
---

# Async Messaging (SQS / SNS)

## Overview

Queues decouple services and absorb load, but they deliver at least once, may reorder, and keep redelivering what a consumer fails to finish. Most messaging incidents are duplicate processing, messages reprocessed in a loop because the visibility timeout was too short, poison messages blocking progress, or events whose schema changed under their consumers. This skill makes publishing, consuming, and evolving messages correct under those conditions.

## When to use

- Adding or changing an SQS queue, SNS topic, subscription, publisher, or consumer.
- Designing or changing an event or command message contract.
- Diagnosing duplicates, stuck or looping messages, growing queues, or DLQ arrivals.

**When not to use:** cross-service consistency patterns (outbox, sagas) → `distributed-systems`. Propagating correlation ids in attributes → `distributed-tracing-and-correlation` (applied here, not repeated).

## Inputs and context

1. The flow: producer, topic or queue, subscribers, and what each consumer does with a message.
2. Requirements: ordering (global, per entity, none), latency, throughput, tolerance for duplicates and loss, retention.
3. Existing infrastructure: queue type, visibility timeout, `maxReceiveCount`, DLQs, encryption, IAM, consumer runtime (worker process, Celery, Lambda).
4. Existing message envelope and naming conventions.
5. **Current AWS quotas** (message size, FIFO throughput): check the documentation or console for the account rather than relying on remembered numbers.

## Process

1. **Choose the queue type.** *Standard*: at-least-once, best-effort ordering, high throughput; consumers must tolerate duplicates and reordering. *FIFO*: ordered within a `MessageGroupId`, deduplicated within a 5-minute window (by `MessageDeduplicationId` or content-based), with lower throughput limits. Use FIFO only when per-entity ordering is a requirement, with the entity id as the group id. FIFO deduplication doesn't replace idempotent consumers (duplicates outside the window, or from the producer's own retries with new ids).
2. **Define the envelope** for every message: `event_id` (unique), `event_type`, `schema_version`, `occurred_at` (UTC), `producer`, the payload, and correlation in message attributes. Commands name intent (`ScoreRefreshRequested`); events state facts (`DecisionMade`).
3. **Keep payloads small and safe.** Send identifiers and the minimal data consumers need, not full records with personal data. Large payloads go to S3 with a reference in the message. Messages are encrypted at rest when SSE is enabled, but they are still copied, logged and redriven: apply `logging-security-and-redaction` tiers.
4. **Publish reliably.** When the message must not be lost relative to a database change, publish through the transactional outbox (`distributed-systems`); otherwise publish after commit. Include correlation attributes on every publish.
5. **Consume correctly** ([consumer pattern below](#consumer-pattern)):
   - Long-poll (`WaitTimeSeconds` up to 20) and request the attributes you need (`MessageAttributeNames`).
   - **Idempotent processing**: deduplicate on `event_id` or a business key in the same transaction as the state change.
   - **Delete only after successful processing.** A message deleted before processing is lost on crash.
   - **Visibility timeout > worst-case processing time**, with headroom. For long jobs, extend it (`ChangeMessageVisibility`) as work progresses. Too short means another consumer receives and processes the same message concurrently.
6. **Retry through redelivery, with backoff.** On a transient failure, don't delete; optionally set a longer visibility timeout (backoff) for that message. Classify errors: transient → retry; permanent (schema invalid, business precondition impossible) → don't loop: send to the DLQ or record and delete, with an ERROR log.
7. **Configure a DLQ** with a redrive policy (`maxReceiveCount`, e.g. 3–5) for every consumer queue. Alert on DLQ depth > 0, document how to inspect and redrive, and make sure redriven messages are still processed idempotently.
8. **Fan out with SNS → SQS** when several consumers need the same event: one queue per consumer, so each has its own retries and DLQ. Use subscription filter policies instead of consumers discarding most messages. Know whether **raw message delivery** is on (it changes the body and attribute shape).
9. **Evolve schemas compatibly.** Add optional fields; consumers ignore unknown fields; never change a field's meaning or type in place. Breaking changes get a new `schema_version` (or event type) consumed in parallel until producers stop sending the old one.
10. **Handle batches and partial failures.** With batch receive (up to 10), track per-message outcomes and delete only successes. On Lambda, use partial batch responses (`ReportBatchItemFailures`) rather than failing the whole batch.
11. **Shut down gracefully**: stop receiving, finish or abandon in-flight messages (abandoned ones reappear after the visibility timeout), then exit.
12. **Observe**: age of oldest message, visible and in-flight counts, DLQ depth, processing duration and failures, receive count per message (`observability-engineering`).

### Consumer pattern

```python
def poll(queue_url):
    resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=20,
                               MessageAttributeNames=["All"], AttributeNames=["ApproximateReceiveCount"])
    for msg in resp.get("Messages", []):
        try:
            with correlation_from(msg):                      # distributed-tracing-and-correlation
                handle(parse_envelope(msg["Body"]))          # idempotent; dedupes on event_id in its transaction
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
        except PermanentMessageError:
            logger.error("message_rejected", extra={"message_id": msg["MessageId"], "error_code": "SCHEMA_INVALID"})
            send_to_dlq_or_park(msg)
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])
        except Exception:
            logger.exception("message_processing_failed", extra={"message_id": msg["MessageId"]})
            # not deleted: redelivered after the visibility timeout; DLQ after maxReceiveCount
```

## Output

Producer and consumer code plus a messaging design note: queue type and why, envelope and schema version, visibility timeout vs measured processing time, DLQ and `maxReceiveCount`, idempotency key, error classification, filter policies, and alerts.

## Verification

- [ ] Duplicate delivery test: the same message processed twice yields one effect.
- [ ] Failure test: a transient failure leaves the message undeleted; a permanent failure doesn't loop.
- [ ] Visibility timeout exceeds measured worst-case processing time (or is extended during processing).
- [ ] Every consumer queue has a DLQ, an alarm, and a documented redrive procedure.
- [ ] Message contains no unnecessary personal data; large payloads use references.
- [ ] Schema change is additive, or versioned with parallel consumption.
- [ ] Correlation attributes are published and extracted (tested).

## Escalation

Ask when: ordering or exactly-once effects are business requirements (they shape the design and cost); a breaking schema change affects consumers owned by other teams; messages must carry personal or financial data; or queue infrastructure (FIFO, DLQ, IAM, encryption) needs changes outside the repository.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "FIFO means no duplicates." | Only within a 5-minute dedup window and for identical dedup ids. Consumers still dedupe. |
| "Delete first so it doesn't get redelivered." | Then a crash loses it. Delete after success. |
| "30 seconds is plenty." | The day processing takes 31 s, two consumers do the same work at once. Measure and add headroom. |
