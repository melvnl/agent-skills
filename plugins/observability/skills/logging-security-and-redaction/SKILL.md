---
name: logging-security-and-redaction
description: Classifies data before it reaches logs and keeps secrets, credentials, PII and customer financial data out of them, using allowlisted fields, masking or keyed pseudonyms. Use when adding or reviewing log statements, error handling, exception messages, or request/response logging.
---

# Logging Security and Redaction

## Overview

Logs are copied, retained, indexed, exported, and read by more people than any database. A single token or identity number in a log is a breach with a long tail. This skill decides, field by field, what may enter a log and in what form. It enforces the rule that redaction happens **at the source, before data reaches the logging backend**, through allowlisted fields rather than after-the-fact masking of arbitrary payloads.

## When to use

- Adding or changing log statements, error handlers, exception messages, or middleware that logs requests or responses.
- Choosing an identifier to put in logs (`user_id`, `customer_ref`, phone, email).
- Reviewing code or logs for PII and secret exposure, or responding to "we found X in the logs".

**When not to use:** what deserves logging at all → `structured-logging-and-instrumentation`. Formal audit trails → `financial-auditability`. Broader application security → `backend-security`.

## Inputs and context

1. The project's data classification or privacy policy (`engineering/SECURITY_AND_PRIVACY.md`, `CLAUDE.md`), and which identifiers it approves for logs. If none exists, use the default tiers below and flag the gap.
2. Existing redaction utilities: filters, serializers, `sensitive_variables`/`sensitive_post_parameters` decorators (Django), masking helpers. Reuse them.
3. The data flowing through the code: model fields, request schemas, headers, external API responses.
4. Where logs go and who can read them (platform, retention, exports), when documented.

## Process

1. **Inventory every value** the change could log: explicit fields, interpolated variables, exception messages, `repr()` of objects, request/response bodies, headers, URLs.
2. **Classify each value** with the tiers below and [references/sensitive-data-catalog.md](references/sensitive-data-catalog.md).
3. **Assess identifiers individually.** A field named `user_id` is not automatically safe. Ask: is it an internal surrogate key or an external identifier (account number, phone, national id)? Is it exposed to customers or partners? Can it be linked to a person by people who read logs? Is it needed to diagnose anything? Log it only if it is an **approved internal identifier** *and* diagnostically needed.
4. **Choose the safe form** for anything not tier 4 (table below). Default to *omit*.
5. **Build log payloads from an allowlist.** Pass explicit, named fields. Never pass whole dicts, request objects, ORM instances, Pydantic models, or `__dict__`/`vars()`.
6. **Sanitize exceptions** before logging their text: database errors often echo values; validation errors (e.g. Pydantic, which includes the offending `input` in its error details) echo user input; HTTP client errors echo URLs and query strings. Log `error_code` and exception class; include text only when known safe.
7. **Add defense in depth** where the project lacks it: a logging filter that redacts known sensitive keys and value patterns ([references/redaction-implementation.md](references/redaction-implementation.md)). It is a safety net, not the primary control.
8. **Prove absence with a test** that feeds sentinel sensitive values through the code path and asserts they appear in no captured log record.

### Classification tiers

| Tier | Examples | In logs |
|---|---|---|
| **1. Secrets** | passwords, API keys, tokens (bearer, refresh, session, OTP), private keys, signing secrets, `Authorization`/`Cookie`/`Set-Cookie` headers, DB URLs with credentials | **Never**, in any form (no masking, no hashing) |
| **2. Sensitive personal or financial** | national identity numbers (SSN, NIK, passport, tax id), full name + DOB, phone, email, address, precise location, bank account / card numbers, salary, credit score, bureau data, document images | **Never raw.** Only a pseudonymous reference or a masked fragment when there is a documented diagnostic need |
| **3. Internal identifiers** | surrogate keys, application ids, order ids, internal customer refs | Allowed when approved and needed; assess linkability (step 3) |
| **4. Operational** | event, status, durations, counts, error codes, rule versions, enum states, service names | Allowed |

### Safe alternatives

| Need | Instead of | Use |
|---|---|---|
| Find the customer's records | phone, email, national id | approved internal customer reference |
| Join events about the same person without identifying them | raw identifier | keyed pseudonym: `HMAC-SHA256(secret_key, value)`, truncated. **Never** a plain unsalted hash: phone numbers and ids are low-entropy and brute-forceable |
| Show a human which account | full account number | masked fragment, e.g. last 4 digits, only if policy allows |
| Know a value was present | the value | `has_email=true`, `phone_country=ID`, `items_count=3` |
| Debug a payload shape | the payload | field names, sizes, schema version, validation error **codes** |
| Exception diagnostics | `str(exc)` with data | `error_code`, exception class, sanitized message |

Pseudonymous is not anonymous: a keyed pseudonym is still personal data under most privacy regimes, so it still needs a purpose and limited retention.

## Output

1. The code change: allowlisted fields, safe forms, sanitized exceptions, filter where needed.
2. A **data-handling note** in the implementation report:

```markdown
### Log data classification
| Field | Tier | Form logged | Justification |
|---|---|---|---|
| applicant_ref | 3 | as is (approved internal ref) | locate application records |
| phone | 2 | not logged; `has_phone` flag | presence only needed |
| bureau_response | 2 | not logged; `bureau_status`, `error_code` | outcome only |
Sentinel test: test_no_pii_in_logs (passes).
```

## Verification

- [ ] Every logged field is classified; no tier-1 value appears in any form.
- [ ] Tier-2 values appear only as approved pseudonyms or masks, with a written justification.
- [ ] No whole objects, bodies, headers, querystrings, or unsanitized exception text are logged.
- [ ] A sentinel test (fake token, fake id number, fake email) runs through the path and asserts absence in captured logs. It was actually run.
- [ ] The guardrails `detect-sensitive-logging` hook (if installed) reports nothing, **and** you still reviewed manually: patterns miss things.

## Escalation

Ask when: the policy doesn't say whether a field may be logged; a diagnostic need seems to require tier-2 data (decide with the data owner, don't decide alone); sensitive data is found **already** in logs (that is an incident: report it, don't just patch the code; retention and purge need a human); or a keyed-pseudonym key needs provisioning.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's only DEBUG." | DEBUG gets enabled in production during incidents, which is exactly when the data flows. |
| "The log platform masks it." | Downstream masking misses formats, and the raw value already crossed the network and agents. |
| "It's hashed." | An unsalted hash of a phone number reverses in minutes. |
| "Only engineers can read logs." | Engineers, vendors, exports, backups, and anyone with a leaked credential. |
| "`user_id` is obviously fine." | Not if it is an external account number or appears in customer-facing URLs. |

## References

- [references/sensitive-data-catalog.md](references/sensitive-data-catalog.md): read when classifying fields; key names and value patterns by tier.
- [references/redaction-implementation.md](references/redaction-implementation.md): read when implementing allowlists, a redaction filter, keyed pseudonyms, masking, or sentinel tests.
