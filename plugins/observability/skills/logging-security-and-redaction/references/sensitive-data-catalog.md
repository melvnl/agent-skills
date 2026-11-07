# Sensitive data catalog

Default classification when the project has no policy. A project's own policy overrides this. Key-name matching is a **hint**, not a verdict: `password_reset_requested=true` is operational; `token_count` is a count. Classify by what the value *is*.

## Key names (case-insensitive substrings, after normalizing `-` and camelCase to `_`)

| Tier | Key name signals |
|---|---|
| 1 Secrets | `password`, `passwd`, `pwd`, `secret`, `token`, `api_key`, `apikey`, `access_key`, `private_key`, `client_secret`, `authorization`, `auth_header`, `cookie`, `set_cookie`, `session`, `sessionid`, `csrf`, `otp`, `pin`, `cvv`, `cvc`, `signature`, `signing_key`, `dsn` (with credentials), `connection_string` |
| 2 Personal identity | `ssn`, `nik`, `ktp`, `npwp`, `passport`, `national_id`, `identity_number`, `id_number`, `tax_id`, `driver_license`, `dob`, `date_of_birth`, `birth`, `full_name`, `first_name`, `last_name`, `mother_maiden` |
| 2 Contact / location | `email`, `phone`, `msisdn`, `mobile`, `address`, `street`, `postal`, `zip`, `lat`, `lng`, `latitude`, `longitude`, `ip_address` (personal data in many regimes) |
| 2 Financial | `account_number`, `bank_account`, `iban`, `card_number`, `pan`, `card`, `salary`, `income`, `balance`, `credit_score`, `bureau`, `credit_report`, `transaction_detail` |
| 2 Documents / biometrics | `selfie`, `photo`, `document_image`, `face`, `fingerprint`, `biometric` |
| 2 Free text | `notes`, `comment`, `description`, `message` (user-entered text routinely contains PII) |

## Value patterns (secret or PII regardless of key)

| Pattern | Regex (indicative) | Tier |
|---|---|---|
| Bearer / basic auth | `(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}` | 1 |
| JWT | `\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}` | 1 |
| AWS access key id | `\b(AKIA|ASIA)[0-9A-Z]{16}\b` | 1 |
| Private key block | `-----BEGIN [A-Z ]*PRIVATE KEY-----` | 1 |
| URL with credentials | `[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@` | 1 |
| Token-like query parameter | `(?i)[?&](token|access_token|api_key|signature|sig|code)=[^&\s]+` | 1 |
| Email | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | 2 |
| Card number | 13–19 digits (optionally spaced or dashed) **passing a Luhn check** | 2 |
| 16-digit national id (e.g. NIK) | `\b\d{16}\b` (high false-positive rate: confirm by key or context) | 2 |
| Phone (E.164-like) | `\+?\d[\d\s-]{8,14}\d` (high false-positive rate) | 2 |

Numeric patterns collide with order numbers and timestamps. Use them to **flag for review**, never as the only control.

## Places sensitive data hides

- `Authorization`, `Cookie`, `Set-Cookie`, `X-Api-Key`, and custom auth headers in logged request objects
- Query strings in logged URLs (`?token=...`, signed URLs)
- `repr()` / `__str__` of models and dataclasses (every field)
- Exception messages: database constraint errors (values), validation errors (input), HTTP client errors (URLs)
- Framework error reports: Django's debug page and error emails include request data unless filtered
- Third-party SDK debug logging (HTTP client wire logs at DEBUG print headers and bodies)
- Celery/queue task arguments logged by the worker framework on failure

## Framework facilities worth reusing

- Django: `@sensitive_variables(...)` and `@sensitive_post_parameters(...)` (exclude values from error reports); `SafeExceptionReporterFilter` hides settings whose names match a pattern including `API`, `KEY`, `PASS`, `SECRET`, `SIGNATURE`, `TOKEN`. Neither scrubs your own log calls.
- HTTP client wire logging (`http.client` debuglevel, `urllib3`/`httpx` DEBUG loggers): keep these loggers at WARNING or above in production.
