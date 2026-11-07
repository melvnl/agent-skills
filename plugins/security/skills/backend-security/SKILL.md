---
name: backend-security
description: Secures backend services against the failures that recur in reviews and incidents: broken authentication and object-level authorization (IDOR), injection, SSRF, unverified webhooks and callbacks, secrets in code or logs, unsafe deserialization, mass assignment, and missing rate limits. Use when building or reviewing endpoints, integrations, callbacks, file or URL handling, auth logic, or configuration.
---

# Backend Security

## Overview

Most backend vulnerabilities are not exotic: an endpoint that checks *that* a user is logged in but not *whose* record they are reading, a callback that trusts any caller, a URL fetched on a user's behalf into the internal network, a secret committed to the repo. This skill checks for those classes systematically while code is written and reviewed, and requires tests that attempt the attack.

## When to use

- New or changed endpoints, especially ones taking ids, URLs, files, or callback payloads.
- Integrations with external providers (bureaus, payment or messaging providers), webhooks and callbacks.
- Authentication, session, permission, or configuration changes.
- Security review of a diff (the factory `SECURITY_REVIEW` workflow, the `security-auditor` agent).

**When not to use:** keeping sensitive data out of logs → `logging-security-and-redaction`. Financial permission models (limits, maker-checker) → `financial-authorization`.

## Inputs and context

1. The auth model: identity provider or session system, token types, roles and permissions, tenancy, and where checks are enforced (middleware, decorators, DRF permissions, FastAPI dependencies).
2. `engineering/SECURITY_AND_PRIVACY.md` and the threat assumptions it records.
3. The data the code touches and its classification.
4. Every external input: path and query params, bodies, headers, files, callback payloads, and data read back from third parties.
5. Secret handling: where secrets come from (secret manager, environment) and how they reach the process.

## Process

1. **Map trust boundaries** for the change: who can call it, with what credentials, and what data crosses into the system.
2. **Authentication**: every non-public route requires it, enforced by the framework mechanism (not by convention in each handler). Token validation checks signature, expiry, audience, and issuer with the provider's library. Never hand-roll crypto or session schemes.
3. **Authorization at the object level.** For every id from the request, check the caller may access *that* record: scope queries by owner or tenant (`.filter(owner=request.user)`), not "fetch by id, then maybe check". Return 404 for records the caller may not know exist. Deny by default. **Write a test where user B requests user A's object.**
4. **Prevent mass assignment**: accept only explicit fields in serializers and schemas; never bind request bodies onto models wholesale (`**request.data`), especially for `role`, `status`, `limit`, `owner`.
5. **Injection**: parameterized queries only (ORM or bound parameters); no shell commands built from input (`subprocess` with an argument list and no `shell=True`); safe template rendering; validate and canonicalize file paths against a base directory (path traversal).
6. **SSRF**: when the server fetches a URL influenced by input (webhook registration, document import, image fetch), allowlist schemes and hosts; resolve DNS and reject private, loopback, link-local and cloud-metadata addresses (`169.254.169.254`); disable redirects or re-validate each hop; set timeouts and size limits.
7. **Verify webhooks and callbacks** ([references/webhook-verification.md](references/webhook-verification.md)): HMAC or asymmetric signature over the **raw** body with a per-provider secret, constant-time comparison, a timestamp tolerance against replay, idempotent processing by event id, and optionally an IP allowlist as defense in depth (never as the only check). Re-fetch critical state from the provider's API instead of trusting the callback body when the provider supports it.
8. **Secrets**: never in code, fixtures, logs, error messages, or client responses; loaded from the secret manager or environment; `.env*` with real values git-ignored. A secret that reached git history is compromised: rotate it.
9. **Deserialization and parsing**: no `pickle`, `yaml.load` without a safe loader, or `eval` on untrusted input; limit request body and file sizes; validate file types by content, not only extension.
10. **Abuse controls**: rate limits on authentication, OTP, and expensive or enumeration-prone endpoints; lockouts or backoff on repeated failures; generic error messages that don't reveal whether an account exists.
11. **Security headers and transport** where the service serves browsers: HTTPS only, HSTS, appropriate CORS (no `*` with credentials), CSRF protection for cookie-authenticated state changes.
12. **Dependencies**: no new dependency with known high or critical vulnerabilities; run the project's scanner if one is configured.
13. **Record findings** with severity and a concrete exploit scenario; fixes come with a test that reproduces the attack.

## Output

For implementation: the secured code plus attack tests (cross-user access, unsigned or replayed callback, SSRF target, injection payload). For review: findings in the factory `CODE_REVIEW` format, with severity, `file:line`, exploit scenario, and fix:

```markdown
| # | Severity | Location | Finding | Exploit scenario | Fix |
|---|---|---|---|---|---|
| 1 | Blocker | api/applications.py:31 | Fetches application by id without owner scope | Any user reads any application by iterating ids | Scope the query to request.user; add cross-user test |
```

## Verification

- [ ] Every new route has authentication and object-level authorization, with a cross-user test.
- [ ] Request bodies bind only allowlisted fields.
- [ ] No string-built SQL or shell commands; file paths are canonicalized.
- [ ] Outbound fetches of input-influenced URLs block internal and metadata addresses (tested).
- [ ] Callbacks verify signature, timestamp, and idempotency (tested with bad signature, stale timestamp, replay).
- [ ] No secrets in the diff, logs, or responses; scanner or hook output reviewed.
- [ ] Rate limits on sensitive endpoints.

## Escalation

Escalate immediately when: a vulnerability may already be exploited or a secret is exposed (incident: rotate, assess, notify, per the project's process); a fix changes authentication or permission semantics for existing users; or a provider's verification mechanism is undocumented (ask, don't guess).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The id is a UUID, so it can't be guessed." | IDs leak through logs, URLs, and referrers. Authorize every access. |
| "The callback URL is secret." | URLs leak. Verify signatures. |
| "It's an internal endpoint." | Internal networks get reached through SSRF and compromised services. Authenticate. |

## References

- [references/webhook-verification.md](references/webhook-verification.md): signature verification, replay protection, idempotent processing, SSRF guard.
