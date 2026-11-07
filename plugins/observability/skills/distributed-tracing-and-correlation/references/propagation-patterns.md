# Propagation patterns

Adapt names to the project's existing identifiers. These patterns assume stdlib Python; check the runtime version before using `contextvars` (3.7+) or `asyncio.to_thread` (3.9+).

## Find what exists

```bash
grep -rniE "request_id|correlation_id|trace_id|x-request-id|x-correlation-id|traceparent|AWSTraceHeader|MessageAttributes" --include=*.py . | head -60
grep -rniE "opentelemetry|ddtrace|aws_xray_sdk|sentry_sdk" --include=*.py --include=*.txt --include=*.toml --include=*.cfg . | head
```

## Context holder + logging filter

```python
import contextvars
import logging
import re
import uuid

correlation_id_var = contextvars.ContextVar("correlation_id", default=None)
_VALID_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

def accept_or_generate(inbound):
    """Use a well-formed inbound id; replace anything else (prevents log injection)."""
    if inbound and _VALID_ID.match(inbound):
        return inbound
    return uuid.uuid4().hex

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        return True
```

Attach the filter to the handler in the logging config so every record carries the field.

## Ingress middleware

Django (new-style middleware):

```python
def correlation_middleware(get_response):
    def middleware(request):
        cid = accept_or_generate(request.headers.get("X-Correlation-ID"))
        token = correlation_id_var.set(cid)
        try:
            response = get_response(request)
            response["X-Correlation-ID"] = cid
            return response
        finally:
            correlation_id_var.reset(token)
    return middleware
```

`request.headers` exists from Django 2.2; older versions use `request.META["HTTP_X_CORRELATION_ID"]`.

FastAPI / Starlette:

```python
@app.middleware("http")
async def correlation_middleware(request, call_next):
    cid = accept_or_generate(request.headers.get("x-correlation-id"))
    token = correlation_id_var.set(cid)
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response
    finally:
        correlation_id_var.reset(token)
```

## HTTP egress

```python
def outbound_headers():
    cid = correlation_id_var.get()
    return {"X-Correlation-ID": cid} if cid else {}

resp = session.get(url, headers={**outbound_headers(), **other_headers}, timeout=5)
```

With OpenTelemetry, prefer the propagator, which writes `traceparent`/`tracestate`:

```python
from opentelemetry.propagate import inject
headers = {}
inject(headers)
```

Instrumentation packages for `requests`/`httpx` can do this automatically; check whether they are already enabled before adding manual injection, or the headers are written twice.

## SQS publish

```python
def correlation_attributes():
    attrs = {}
    cid = correlation_id_var.get()
    if cid:
        attrs["correlation_id"] = {"DataType": "String", "StringValue": cid}
    return attrs

sqs.send_message(QueueUrl=queue_url, MessageBody=body, MessageAttributes=correlation_attributes())
```

OpenTelemetry carrier for SQS attributes:

```python
carrier = {}
inject(carrier)
attrs = {k: {"DataType": "String", "StringValue": v} for k, v in carrier.items()}
```

Remember the 10-attribute limit per message.

## SQS consume

```python
def handle_sqs_message(msg):
    attrs = msg.get("MessageAttributes", {})
    inbound = attrs.get("correlation_id", {}).get("StringValue")
    token = correlation_id_var.set(accept_or_generate(inbound))
    try:
        logger.info("message_processing_started", extra={"message_id": msg["MessageId"]})
        process(msg)
    finally:
        correlation_id_var.reset(token)
```

Request `MessageAttributeNames=["All"]` (or the specific names) in `receive_message`, or attributes are not returned. Many consumers miss this.

## SNS -> SQS envelope

```python
import json

def extract_sns(msg):
    body = json.loads(msg["Body"])
    if body.get("Type") == "Notification":                 # raw delivery off: envelope
        attrs = {k: v.get("Value") for k, v in body.get("MessageAttributes", {}).items()}
        return body["Message"], attrs
    attrs = {k: v.get("StringValue") for k, v in msg.get("MessageAttributes", {}).items()}
    return msg["Body"], attrs                              # raw delivery on
```

Note the different shapes: the envelope uses `{"Type": ..., "Value": ...}`; SQS attributes use `{"DataType": ..., "StringValue": ...}`.

## Thread pools and executors

```python
import contextvars
from concurrent.futures import ThreadPoolExecutor

ctx = contextvars.copy_context()
executor.submit(ctx.run, do_work, item)

# asyncio
await loop.run_in_executor(None, contextvars.copy_context().run, do_work, item)
await asyncio.to_thread(do_work, item)   # 3.9+: copies context itself
```

Use one copied context per submitted task when tasks may set variables, so they don't interfere.

## Celery

```python
score_refresh.apply_async(args=[applicant_ref], headers={"correlation_id": correlation_id_var.get()})
```

On the worker side, read the header in a `task_prerun` signal handler (or a base task class) and set the contextvar; reset it in `task_postrun`. Where the header lands on the task request varies across Celery versions, so check `task.request` in the project's installed version (or pass the id as an explicit kwarg if headers are unreliable). OpenTelemetry's Celery instrumentation propagates trace context when enabled.

## Testing propagation

```python
def test_publish_injects_correlation(monkeypatch):
    sent = {}
    monkeypatch.setattr(sqs, "send_message", lambda **kw: sent.update(kw))
    token = correlation_id_var.set("cid-123")
    try:
        publish_score_refresh("ref-1")
    finally:
        correlation_id_var.reset(token)
    assert sent["MessageAttributes"]["correlation_id"]["StringValue"] == "cid-123"
```

Write the mirror test for the consumer: feed a message with the attribute and assert the log record (or the contextvar inside `process`) carries it.
