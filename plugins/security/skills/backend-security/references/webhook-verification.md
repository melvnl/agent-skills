# Webhook and callback verification

Follow the provider's documented scheme exactly (header names, signed string, encoding). The generic HMAC pattern:

```python
import hashlib
import hmac
import time

TOLERANCE_S = 300

def verify_callback(raw_body: bytes, signature_header: str, timestamp_header: str, secret: bytes) -> None:
    try:
        ts = int(timestamp_header)
    except (TypeError, ValueError):
        raise InvalidSignature("missing or malformed timestamp")
    if abs(time.time() - ts) > TOLERANCE_S:
        raise InvalidSignature("timestamp outside tolerance")          # replay protection
    signed = f"{ts}.".encode() + raw_body                               # sign the RAW bytes, not re-serialized JSON
    expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header or ""):       # constant-time
        raise InvalidSignature("signature mismatch")
```

Rules:
- Read the **raw** request body before any JSON parsing; re-serializing changes bytes and breaks the signature.
- One secret per provider (and per environment), from the secret manager; support rotation (accept current and previous secret during a rollover).
- Reject before doing any work; respond with a generic 401/400 and log the rejection without the signature or secret.
- **Idempotency**: store the provider's event id with a unique constraint in the same transaction as the effect; duplicates are acknowledged and skipped.
- **Don't trust the payload for critical state** when the provider offers an API: use the callback as a trigger, then fetch the authoritative status (e.g. the transaction or verification result) by id.
- Acknowledge quickly (2xx) and process asynchronously when processing is slow; providers retry on timeouts, which creates duplicates anyway.
- IP allowlists are defense in depth only: provider IP ranges change and can be spoofed through intermediaries.

## SSRF guard for outbound fetches

```python
import ipaddress
import socket
from urllib.parse import urlsplit

ALLOWED_SCHEMES = {"https"}

def assert_public_url(url: str, allowed_hosts=None) -> None:
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES or not parts.hostname:
        raise UnsafeURL("scheme or host not allowed")
    if allowed_hosts is not None and parts.hostname not in allowed_hosts:
        raise UnsafeURL("host not in allowlist")
    for info in socket.getaddrinfo(parts.hostname, parts.port or 443):
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise UnsafeURL("resolves to a non-public address")
```

Then fetch with redirects disabled (or re-check each redirect target), a short timeout, and a response size limit. DNS can change between the check and the connection (DNS rebinding); for high-risk features, connect to the resolved, validated IP with the original Host header, or route through an egress proxy that enforces the policy.
