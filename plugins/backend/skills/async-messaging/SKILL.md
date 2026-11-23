---
name: async-messaging
description: Designs and implements reliable asynchronous messaging on any broker or job queue (SQS/SNS, RabbitMQ, Kafka, BullMQ, framework event buses): delivery guarantees and ordering, versioned envelopes, idempotent consumers, ack-after-success, visibility and lock timeouts, retries with backoff, dead-letter handling, fan-out, poison messages, and graceful shutdown. Use when publishing or consuming messages, events or background jobs.
---

# Async Messaging

## Overview

Queues and event buses decouple services and absorb load, but they deliver at least once, may reorder, and keep redelivering what a consumer fails to finish. Most messaging incidents are duplicate processing, messages reprocessed in a loop because a timeout was shorter than the work, poison messages blocking progress, or events whose schema changed under their consumers. This skill makes publishing, consuming and evolving messages correct under those conditions, whatever the broker.

## When to use

- Adding or changing a queue, topic, subscription, event subscriber, background job, publisher, or consumer.
- Designing or changing an event or command message contract.
- Diagnosing duplicates, stuck or looping messages, growing queues, or dead-letter arrivals.

**When not to use:** cross-service consistency patterns (outbox, sagas) → `distributed-systems`. Propagating correlation ids in message metadata → `distributed-tracing-and-correlation` (applied here, not repeated).

## Inputs and context

1. The flow: producer, broker resource, subscribers, and what each consumer does with a message.
2. Requirements: ordering (global, per entity, none), latency, throughput, tolerance for duplicates and loss, retention.
3. **The broker or job system and its configuration**: then read its section in [references/broker-notes.md](references/broker-notes.md). Delivery semantics, acknowledgement, redelivery timeouts and dead-letter mechanics differ per broker.
4. Existing message envelope and naming conventions.
5. Current quotas and limits (message size, throughput) from the provider's documentation, not memory.

## Process

1. **Know the delivery guarantee** you actually have. Almost every broker is at-least-once; some framework event buses are at-most-once in development (in-memory) and only durable with a production backend. "Exactly once" features are scoped (a dedup window, a single partition, a transactional producer) and don't replace idempotent consumers.
2. **Choose ordering deliberately.** Order only where a requirement needs it, scoped per entity (FIFO message group, Kafka partition key, single-concurrency job queue per key). Global ordering costs throughput.
3. **Define the envelope** for every message: `event_id` (unique), `event_type`, `schema_version`, `occurred_at` (UTC), `producer`, payload, and correlation metadata. Commands name intent (`ScoreRefreshRequested`); events state facts (`OrderPlaced`).
4. **Keep payloads small and safe.** Send identifiers and the minimal data consumers need, not full records with personal data; large payloads go to object storage with a reference. Messages are copied, logged and redriven: apply `logging-security-and-redaction` tiers.
5. **Publish reliably.** When the message must not be lost relative to a database change, publish through the transactional outbox (`distributed-systems`); otherwise publish **after commit**, never inside the transaction (consumers would read uncommitted or rolled-back state).
6. **Consume correctly**:
   - **Idempotent processing**: deduplicate on `event_id` or a business key, in the same transaction as the state change.
   - **Acknowledge only after successful processing.** Acknowledging first loses the message on crash.
   - **Redelivery timeout > worst-case processing time** (visibility timeout, job lock duration, consumer session timeout), with headroom, or extended as work progresses. Too short means two consumers process the same message at once.
7. **Retry with backoff and classify errors.** Transient → retry with increasing delay; permanent (invalid schema, impossible precondition) → don't loop: dead-letter or record and acknowledge, with an ERROR log.
8. **Dead-letter every consumer.** A bounded attempt count, a dead-letter destination, an alert on depth > 0, and a documented inspect-and-redrive procedure. Redriven messages are still processed idempotently.
9. **Fan out with one queue or consumer group per consumer**, so each has its own retries and dead letters. Filter at the broker (subscription filters, routing keys) instead of consumers discarding most messages.
10. **Evolve schemas compatibly.** Add optional fields; consumers ignore unknown fields; never change a field's meaning or type in place. Breaking changes get a new `schema_version` or event type consumed in parallel until producers stop sending the old one.
11. **Handle batches and partial failures**: track per-message outcomes and acknowledge only successes.
12. **Shut down gracefully**: stop receiving, finish or release in-flight messages, then exit.
13. **Observe**: oldest message age or consumer lag, queue depth, dead-letter depth, processing duration and failures, attempts per message (`observability-engineering`).

## Output

Producer and consumer code plus a messaging design note: broker and delivery guarantee, ordering scope, envelope and schema version, redelivery timeout vs measured processing time, attempts and dead-letter destination, idempotency key, error classification, filters, and alerts.

## Verification

- [ ] Duplicate delivery test: the same message processed twice yields one effect.
- [ ] Failure test: a transient failure leads to redelivery; a permanent failure doesn't loop.
- [ ] Redelivery timeout exceeds measured worst-case processing time, or is extended during processing.
- [ ] Every consumer has dead-letter handling, an alert, and a documented redrive procedure.
- [ ] Publishing happens after commit or through an outbox, never inside the transaction.
- [ ] Message contains no unnecessary personal data; large payloads use references.
- [ ] Schema change is additive, or versioned with parallel consumption.
- [ ] Correlation metadata is published and extracted (tested).

## Escalation

Ask when: ordering or exactly-once effects are business requirements; a breaking schema change affects consumers owned by other teams; messages must carry personal or financial data; or broker infrastructure (queues, dead letters, permissions, encryption, a production event-bus backend) needs changes outside the repository.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The broker deduplicates." | Within a window, for identical ids, on one path. Consumers still dedupe. |
| "Ack first so it doesn't get redelivered." | Then a crash loses it. Ack after success. |
| "30 seconds is plenty." | The day processing takes 31 s, two consumers do the same work at once. Measure and add headroom. |
| "It works locally." | The local event bus is in-memory and drops everything on restart. Check the production backend. |

## References

- [references/broker-notes.md](references/broker-notes.md): read for the broker in use: SQS/SNS (with a consumer pattern), RabbitMQ, Kafka, BullMQ, framework event buses.
