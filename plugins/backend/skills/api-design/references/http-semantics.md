# HTTP semantics, errors, idempotency, pagination

## Status codes

| Code | Use | Common mistake |
|---|---|---|
| 200 / 201 / 204 | success; 201 with `Location` for creation; 204 no body | 200 with `{"error": ...}` |
| 400 | malformed request (unparseable, wrong types) | used for business rule rejections |
| 401 | missing or invalid credentials | used when the user is authenticated but not allowed |
| 403 | authenticated but not permitted | revealing that a resource exists to a caller who shouldn't know |
| 404 | not found, **or** exists but caller must not learn it does | |
| 409 | conflicts with current state (invalid transition, duplicate natural key, concurrent modification) | 400 |
| 412 | precondition failed (`If-Match` ETag mismatch, optimistic concurrency) | |
| 422 | well-formed but semantically invalid (business validation) | 500 for a validation bug |
| 429 | rate limited; include `Retry-After` | |
| 500 / 502 / 503 / 504 | server fault, bad upstream, unavailable, upstream timeout | 500 for a client error |

A business "no" (applicant not eligible) is usually a **successful** response describing the decision, not an error.

## Error body

```json
{
  "type": "https://errors.example.com/invalid-income",
  "title": "Income is invalid",
  "status": 422,
  "code": "INVALID_INCOME",
  "detail": "Monthly income must be a positive amount.",
  "errors": [{"field": "monthly_income", "code": "MUST_BE_POSITIVE"}],
  "request_id": "req-8f2c..."
}
```

Shape follows RFC 9457 (Problem Details) plus a stable `code`. Messages contain no stack traces, SQL, internal hostnames, or echoed sensitive input.

## Idempotency keys

```text
POST /v1/applications
Idempotency-Key: 6f1d2c0e-...        (client-generated, unique per logical operation)
```

Server behavior:

1. Look up `(client_id, key)`. If absent, insert a record `{key, request_hash, status: in_progress}` **atomically** (unique constraint), then execute.
2. On completion, store the response status and body; keep for a documented TTL (e.g. 24 h).
3. Same key, same `request_hash`, completed → return the stored response (same status and body).
4. Same key, same hash, still `in_progress` → 409 (or wait briefly), never execute twice.
5. Same key, **different** hash → 422 (`IDEMPOTENCY_KEY_REUSED`).
6. Failed with a server error → policy decision: allow retry with the same key (delete the record) or return the stored failure. Document it.

Scope keys per client or tenant. Hash the canonicalized request body, not raw bytes that vary in field order.

## Pagination

- **Cursor**: `?limit=50&cursor=<opaque>`; response `{"data": [...], "next_cursor": "..."}`. Cursor encodes the last sort key (e.g. `(created_at, id)`), giving stable results under inserts.
- **Offset**: `?limit=50&offset=100`; simple, fine for small, stable datasets and admin UIs; slow at deep offsets (the database still scans skipped rows).
- Always cap `limit`; always define a deterministic sort including a unique tiebreaker.

## Optimistic concurrency

Return an `ETag` (or `version` field); require `If-Match` (or the version) on updates; reject stale writes with 412 (or 409). This prevents lost updates between two editors.
