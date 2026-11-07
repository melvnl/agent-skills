---
description: SQS consumer neither requests nor binds correlation attributes
tags: [observability]
runs: 1
max_turns: 8
allowed_tools: [Skill, Read, Grep, Glob]
---

Review this backend change for observability (logging, correlation, sensitive data). Report concrete findings with fixes.

```python
def poll():
    resp = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=20)
    for msg in resp.get("Messages", []):
        logger.info("score_refresh_started", extra={"message_id": msg["MessageId"]})
        refresh(json.loads(msg["Body"]))
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
```
