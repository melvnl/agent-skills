---
name: api-design
description: Designs and evolves HTTP API contracts: resources, status codes, a stable error model, pagination, idempotency keys for retried writes, money and time formats, versioning and backward compatibility, and contract documentation and tests. Use when adding or changing an endpoint, request or response schema, or an internal service interface.
---

# API Design

## Overview

An API contract outlives its implementation: clients, partners, and other services build on its exact shapes and behaviors. Most API incidents come from contract mistakes: an error clients can't distinguish, a retried POST that creates duplicates, a removed field, a float amount that rounds. This skill designs contracts that are unambiguous, safe to retry, and possible to evolve without breaking consumers.

## When to use

- New endpoints, or changes to request/response schemas, status codes, error codes, or semantics.
- Internal service-to-service interfaces with the same compatibility concerns.
- Reviewing an API change for compatibility.

**When not to use:** framework mechanics → `django-engineering`, `fastapi-engineering`. Message and event contracts → `async-messaging`. Webhook signature verification and authz → `backend-security`.

## Inputs and context

1. The spec's requirements and acceptance criteria for the interface.
2. **Existing API conventions**: URL style, casing (`snake_case` vs `camelCase`), error shape, pagination style, auth, versioning scheme. Consistency with the existing API beats any default here. The factory keeps them in `engineering/API_CONTRACTS.md`.
3. Who consumes it: public or partner clients, mobile apps (slow upgrade cycles), internal services.
4. Non-functional needs: latency, payload size, rate limits.

## Process

1. **Model resources and operations** from the domain: nouns for resources, standard methods for operations. Actions that aren't CRUD (`approve`, `recalculate`) become explicit sub-resources or action endpoints (`POST /v1/applications/{id}/approval`), not overloaded `PATCH` flags.
2. **Pick status codes by meaning** ([references/http-semantics.md](references/http-semantics.md)): 400 malformed, 422 semantically invalid, 401 unauthenticated, 403 forbidden, 404 not found (also for objects the caller may not know exist), 409 state conflict, 429 rate limited, 5xx only for server faults.
3. **Define one error model** for the whole API: a stable machine-readable `code`, a human message free of internals, optional `details` (field errors), and a correlation id. Error codes are part of the contract: never repurpose one. RFC 9457 (Problem Details) is a good default when no convention exists.
4. **Make retried writes safe.** Any non-idempotent operation that clients may retry (creating applications, triggering decisions, anything with money) accepts an **idempotency key** (pattern in the reference): same key + same payload returns the original result; same key + different payload is rejected; concurrent duplicates don't both execute.
5. **Paginate every unbounded collection.** Prefer cursor pagination for large or changing datasets (offset pages get slow and skip or duplicate rows as data changes); keep a maximum page size.
6. **Format values unambiguously**: money as a decimal **string** plus an ISO 4217 currency code (`{"amount": "150000.00", "currency": "IDR"}`), never a float; timestamps in ISO 8601 with offset (UTC preferred); durations with units; ids opaque strings; enums documented as closed or open sets.
7. **Minimize data exposure.** Return only fields the client needs; never internal flags, raw bureau data, or personal data beyond the use case (`logging-security-and-redaction` tiers apply to responses too).
8. **Plan evolution.** Additive changes (new optional request fields, new response fields, new endpoints) are compatible, *if* clients ignore unknown fields. Breaking changes (removing or renaming fields, changing types or meaning, tightening validation, new required inputs, changing error codes) need a new version or a deprecation path with dates, an ADR or spec note, and owner approval.
9. **Document before implementing**: update `engineering/API_CONTRACTS.md` or the OpenAPI spec, including errors and examples.
10. **Test the contract**: schema-level tests for request validation and response shape, error-code tests for each failure case, idempotency tests (same key twice, same key different body, concurrent).

## Output

A contract entry (OpenAPI fragment or `API_CONTRACTS.md` section) with method, path, auth, request and response schemas, every error code with its status, idempotency behavior, pagination, rate limits, examples, and a compatibility statement ("additive; no client change required").

## Verification

- [ ] Every failure case in the spec maps to a status code and a stable error code, and has a test.
- [ ] Retryable non-idempotent writes accept idempotency keys; duplicate and conflicting-key tests pass.
- [ ] Collections are paginated with a maximum page size.
- [ ] Money is a decimal string with currency; timestamps carry offsets.
- [ ] Responses contain no internal or unnecessary personal fields (asserted in a test).
- [ ] The change is classified additive or breaking; breaking changes have approval and a migration path.
- [ ] The contract document was updated in the same change.

## Escalation

Ask when: a change is breaking for existing consumers; consumers are unknown (public or partner APIs); a new error code or status changes client behavior; or the API exposes personal or financial data not covered by the spec.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Clients won't retry POST." | Mobile networks, load balancers and SDKs retry. Without idempotency, they create duplicates. |
| "A float is fine for amounts." | `0.1 + 0.2 != 0.3`. Rounding errors in money become disputes. |
| "Renaming the field is a small cleanup." | It is a breaking change for every consumer. |

## References

- [references/http-semantics.md](references/http-semantics.md): status code guide, error model, idempotency-key pattern, pagination.
