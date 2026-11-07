# Redaction implementation

Primary control: **build log payloads from explicit, allowlisted fields.** Everything below is defense in depth.

## Allowlisted event payloads

```python
def application_log_fields(application):
    """The only application fields that may appear in logs. Extend deliberately."""
    return {
        "application_ref": application.reference,      # tier 3, approved
        "product_code": application.product_code,      # tier 4
        "status": application.status,                  # tier 4
        "has_phone": bool(application.phone),          # presence, not value
    }

logger.info("application_submitted", extra=application_log_fields(app))
```

Never: `extra=vars(app)`, `extra=request.data`, `logger.info("app=%s", app)` (calls `__str__`), `extra={"payload": body}`.

## Defense-in-depth filter (stdlib)

```python
import logging
import re

_SENSITIVE_KEY = re.compile(
    r"(password|passwd|secret|token|api_?key|authorization|cookie|session|otp|cvv|"
    r"private_?key|signature|national_?id|nik|ssn|passport|card_?number|account_?number|email|phone)",
    re.IGNORECASE,
)
_VALUE_PATTERNS = [
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}"),
    re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
]
_RECORD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}
REDACTED = "[REDACTED]"

def _scrub(text):
    for pattern in _VALUE_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text

class RedactingFilter(logging.Filter):
    def filter(self, record):
        for key in list(vars(record)):
            if key not in _RECORD_ATTRS and _SENSITIVE_KEY.search(key):
                setattr(record, key, REDACTED)
        if record.args:
            record.msg = record.getMessage()   # format once, then scrub the result
            record.args = None
        if isinstance(record.msg, str):
            record.msg = _scrub(record.msg)
        return True
```

Notes:
- Attach it to **handlers** (it then applies to every logger that propagates there), and add a test that it runs.
- Exempt keys that are clearly operational (`token_count`, `has_email`) with an explicit allowlist rather than weakening the pattern.
- Tracebacks (`exc_info`) are rendered later by the formatter, so this filter does not scrub them. Prefer not logging sensitive exception text in the first place, or add a formatter subclass that scrubs `formatException` output.
- structlog: implement the same logic as a processor placed before the renderer.

## Keyed pseudonyms

```python
import hashlib
import hmac

def pseudonym(value, key):
    """Stable, non-reversible reference for joining logs about the same subject.
    `key` comes from the secret manager, never from code. Rotating it breaks linkability, by design."""
    return hmac.new(key, value.strip().lower().encode("utf-8"), hashlib.sha256).hexdigest()[:16]
```

Never use `hashlib.sha256(phone)` alone: the input space is small enough to enumerate.

## Masking

```python
def mask_tail(value, visible=4):
    digits = "".join(ch for ch in value if ch.isalnum())
    return "*" * max(len(digits) - visible, 0) + digits[-visible:]
```

Use only where policy permits showing a fragment, and never for tier-1 secrets.

## Sentinel test

```python
SENTINELS = {
    "token": "tok_SENTINEL_9f8e7d",
    "national_id": "3201999999999999",
    "email": "sentinel.person@example.com",
}

def test_no_sensitive_values_in_logs(caplog, client):
    caplog.set_level(logging.DEBUG)
    client.post("/applications", json={"email": SENTINELS["email"], "national_id": SENTINELS["national_id"]},
                headers={"Authorization": f"Bearer {SENTINELS['token']}"})
    rendered = "\n".join(
        f"{r.getMessage()} {vars(r)}" for r in caplog.records
    )
    for value in SENTINELS.values():
        assert value not in rendered
```

Run at DEBUG so verbose paths are covered too, and use clearly fake values (`example.com`, impossible ids).
