# Workflow: Security Review

> **Scope:** Project-agnostic. Applies to changes touching endpoints, authentication or authorization, external integrations and callbacks, file or URL handling, secrets, configuration, or personal and financial data.

## Purpose

Find exploitable weaknesses before merge, with an independent reviewer, concrete exploit scenarios, and tests that prove each fix.

## Entry conditions

- The change is implemented; the diff range is known.
- The reviewer is not the implementer.
- The project's security and privacy document exists (or its absence is recorded as a finding).

## Inputs

- The diff and base; the spec and design (§ 9 Security and privacy).
- The project's security and privacy document: auth model, data classification, threat assumptions.
- Provider documentation for any webhook or callback verification.

## Outputs

- Findings: severity, `file:line`, weakness, exploit scenario, fix, and the test that would prove it.
- A list of what was checked and found sound, and what was out of scope.

## Execution steps

1. **Map trust boundaries**: callers, credentials, inputs, and data crossing in or out.
2. **Authentication**: every non-public route is protected by the framework mechanism.
3. **Object-level authorization**: every id from input is checked against the caller (queries scoped by owner or tenant); a cross-user access test exists.
4. **Input handling**: only allowlisted fields bind to models (mass assignment); parameterized queries; no shell commands from input; canonicalized file paths; no unsafe deserialization.
5. **Outbound requests** influenced by input: scheme and host allowlists; private, loopback, link-local, and metadata addresses blocked; redirects handled; timeouts and size limits.
6. **Callbacks and webhooks**: signature over the raw body, constant-time comparison, timestamp tolerance, idempotent processing, critical state re-fetched from the provider where possible.
7. **Secrets**: none in code, fixtures, logs, errors, or responses; loaded from the approved source.
8. **Abuse controls**: rate limits and lockouts on authentication, OTP, enumeration-prone, and expensive endpoints; generic errors.
9. **Data exposure**: responses and logs carry only the fields the use case needs.
10. **Dependencies**: no new high or critical known vulnerabilities (run the project's scanner if configured).
11. **Decide** and record the verdict.

If the `backend-security` skill or the `security-auditor` agent is available, use it for steps 1–10.

## Quality gates

| Gate | Passes when |
|---|---|
| Authorization | Every new route has authentication, object-level authorization, and a cross-user test |
| Callbacks | Signature, replay, and duplicate tests pass for each new callback handler |
| Secrets | No secrets in the diff, history of the branch, logs, or responses |
| Findings | No open Blocker; Majors fixed or explicitly accepted |

## Exit conditions

- Verdict recorded; Blockers fixed with proving tests and re-reviewed, or escalated.

## Human approval required

- Accepting any Blocker or Major as a known risk.
- Changes to authentication, authorization semantics, or secret handling.
- **Immediate escalation** (incident handling, not a review comment) when a secret is exposed or a weakness may already be exploited.
