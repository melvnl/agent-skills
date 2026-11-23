# Broker notes

Check the installed client and server versions, and current provider limits, before relying on any number here.

## AWS SQS / SNS

- **Standard** queues: at-least-once, best-effort ordering, high throughput. **FIFO**: ordered within a `MessageGroupId` (use the entity id), deduplicated within a 5-minute window by `MessageDeduplicationId` or content, lower throughput. FIFO only when per-entity ordering is required.
- Long-poll (`WaitTimeSeconds` up to 20); request the attributes you need (`MessageAttributeNames`, `ApproximateReceiveCount`).
- **Visibility timeout** is the redelivery timeout; extend with `ChangeMessageVisibility` for long work. Delete with the receipt handle only after success.
- Dead letters: a redrive policy with `maxReceiveCount` (3–5) per queue; alarm on DLQ `ApproximateNumberOfMessagesVisible > 0`.
- Fan-out: SNS topic → one SQS queue per consumer; subscription filter policies; know whether **raw message delivery** is on (it changes the body and attribute shape).
- Batches up to 10; on Lambda use partial batch responses (`ReportBatchItemFailures`).

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

## RabbitMQ

- Manual acks (`autoAck=false`); `ack` after success, `nack`/`reject` with `requeue=false` for permanent failures so they go to the dead-letter exchange (`x-dead-letter-exchange`).
- Unacked messages redeliver when the channel closes; there is no visibility timeout, but there is a consumer ack timeout on recent versions.
- `prefetch` (QoS) bounds in-flight messages per consumer; set it.
- Publisher confirms for reliable publishing; quorum queues for durability.

## Kafka

- Ordering per partition; the message key picks the partition (use the entity id).
- Commit offsets after processing (disable auto-commit or commit manually); a crash before commit replays from the last committed offset, so consumers are idempotent.
- Long processing must stay under `max.poll.interval.ms` or the consumer is evicted and its partitions rebalance (duplicate processing).
- No built-in DLQ: route failures to a retry or dead-letter topic yourself.
- Schema evolution through a schema registry with compatibility rules where the team runs one.

## BullMQ (Redis-backed jobs, Node)

- A job's lock is the redelivery timeout: a job whose processor blocks the event loop past `lockDuration` is marked stalled and re-run by another worker. Keep CPU work off the loop or raise the lock duration deliberately.
- `attempts` with `backoff: { type: 'exponential', delay }`; failed jobs stay in the failed set (the dead-letter equivalent): alert on it and keep `removeOnFail` retention long enough to inspect.
- Use `jobId` for deduplication of enqueues.
- Durability depends on Redis persistence and `maxmemory-policy noeviction`; an evicting Redis silently loses jobs.

## Framework event buses (Medusa, NestJS, others)

- Find the configured backend: Medusa v2 uses an in-memory event bus by default (lost on restart; for development only) and a Redis-backed module in production; check `medusa-config` before assuming durability.
- Events are usually emitted after the surrounding workflow or transaction completes; subscribers still must be idempotent, because retries and replays happen.
- Subscribers run in the same deployment as the API unless workers are split out (Medusa `workerMode`); slow subscribers compete with request handling.
