---
name: financial-authorization
description: Designs and enforces who may view, decide, override, and configure financially sensitive data and operations: least-privilege roles and attributes, object and tenant scoping, maker-checker segregation of duties, amount-based approval authority, scoped service-to-service credentials, audited break-glass access, and a tested permission matrix. Use when adding admin or back-office functions, decision overrides, limit or policy changes, or service access to credit data.
---

# Financial Authorization

## Overview

In financial systems the dangerous operations are often legitimate ones performed by the wrong person: an agent overriding their own customer's rejection, an engineer activating a rule change they wrote, a service with read access to every bureau report. Authentication says who someone is; financial authorization decides what they may do with *this* record, *this* amount, and *this* policy, and makes sure nobody can both propose and approve a sensitive change.

## When to use

- Back-office or admin features: manual review, decision overrides, limit changes, customer data views.
- Policy and configuration changes: thresholds, rule versions, feature flags affecting decisions.
- New service-to-service access to credit, decision, or customer financial data.
- Reviewing Django admin, internal tools, or API permissions for financial operations.

**When not to use:** general authentication, IDOR, and injection → `backend-security`. Recording what happened → `financial-auditability`.

## Inputs and context

1. The organization's roles and responsibilities, and any written policy on approvals, limits, and segregation of duties. Authority rules are business policy: get them from the owner.
2. The existing permission system: Django groups and permissions, DRF permission classes, FastAPI dependencies, an external policy service, or IAM for services.
3. The operations and data in scope, classified by sensitivity and financial impact.
4. Existing admin surfaces (Django admin is often granted broadly and bypasses API-level checks).

## Process

1. **List operations and data**, each with its impact: view credit data, decide manual reviews, override a decision, change a limit (by amount), edit or activate policy versions, export data, manage users and roles.
2. **Build the permission matrix** (roles × operations, with conditions). Start from deny; grant the minimum each role needs. Prefer permissions named after operations (`decision.override`) over broad flags (`is_staff`).
3. **Scope to objects and tenants.** A permission is evaluated against the specific record: the reviewer's assigned queue, the agent's portfolio, the merchant's own customers. Enforce scoping in queries, not only in the UI (`backend-security`).
4. **Apply segregation of duties (maker-checker)** for high-impact changes: the person who proposes (a policy change, an override above a threshold, a limit increase) can't approve it. Store proposer and approver as different identities, enforce `approver != proposer` in code, and require approval before the change takes effect.
5. **Apply amount-based authority**: approval caps per role (e.g. up to X by a reviewer, above X by a senior reviewer plus a second approver). The caps come from policy, live in versioned configuration, and are enforced server-side.
6. **Constrain overrides**: an override requires a reason code (and free text if policy asks), keeps the original decision intact, creates a new decision record that supersedes it, and is reported in override-rate metrics.
7. **Scope service credentials**: each service gets its own identity with the minimum access (read decisions but not raw bureau data; publish to one topic). No shared superuser database accounts or shared API keys across services.
8. **Plan break-glass access**: emergency elevated access that is time-limited, requires a reason, alerts on use, and is fully audited.
9. **Lock down admin surfaces**: Django admin `ModelAdmin` permissions (`has_change_permission`, `has_delete_permission`, read-only fields for decision data), no delete on financial records, and the same scoping as the API.
10. **Audit authorization events**: privileged actions and approvals as durable audit records (`financial-auditability`); denials logged at WARNING with actor and operation, without sensitive values (`structured-logging-and-instrumentation`).
11. **Test the matrix**: for each operation, at least one allowed and one denied role; cross-object access attempts; maker-checker with the same user as proposer and approver (must fail); amounts at, below, and above each cap.

## Output

The permission matrix (in `engineering/SECURITY_AND_PRIVACY.md` or equivalent), enforcement code, and tests:

```markdown
| Operation | Reviewer | Senior reviewer | Risk policy admin | Engineer | Service: notifier |
|---|---|---|---|---|---|
| View decision + reasons | own queue | all | all | no (break-glass only) | outcome only |
| Override decision | ≤ IDR 5,000,000, reason required | ≤ IDR 50,000,000 | no | no | no |
| Propose policy version | no | no | yes | yes | no |
| Approve/activate policy version | no | no | yes (not own proposal) | no | no |
```

## Verification

- [ ] Every financial operation appears in the matrix, defaulting to deny.
- [ ] Enforcement is server-side and object-scoped; admin surfaces follow the same rules.
- [ ] Maker-checker is enforced in code; a same-user approval test fails as expected.
- [ ] Amount caps come from versioned configuration and are boundary-tested.
- [ ] Overrides keep the original decision, require a reason, and create a superseding record.
- [ ] Service credentials are per service and least privilege.
- [ ] Privileged actions and approvals produce audit records; a test asserts it.

## Escalation

The owner decides: roles, approval caps, which operations need maker-checker, override policy, and break-glass rules. Escalate immediately if existing access is found to be broader than policy (e.g. every staff user can edit decisions in admin): that is a finding to report, not a quiet fix.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Only staff can reach the admin." | Staff is many people. Per-operation permissions, scoped, audited. |
| "The engineer who wrote the rule can activate it; they know it best." | That is exactly what segregation of duties prevents. A second person approves. |
| "One service account is simpler." | Then one compromised service reads everything. Scope per service. |
