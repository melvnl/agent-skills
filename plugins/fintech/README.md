# fintech-engineering

Fintech reviewer agents, scoped to **credit scoring, eligibility, and risk decisioning** in backend services and APIs.

Depends on `backend-engineering`, `observability`, and `application-security` (installed automatically).

## Agents

- **[fintech-domain-reviewer](agents/fintech-domain-reviewer.md)**: Read-only check that decision logic implements the approved credit and risk policy: thresholds, precedence, fallbacks, reasons, versions, authority.
- **[financial-invariant-reviewer](agents/financial-invariant-reviewer.md)**: Read-only check of exact arithmetic, duplicates, concurrency, immutable history, atomic audit records, migration evidence and cross-service consistency.

## Extension catalog (not implemented)

These domains are deliberately out of scope until a real project needs them. They are listed so additions follow the same structure:

| Domain | Would cover |
|---|---|
| Payment processing | provider integration, authorization/capture, refunds, idempotent payment intents |
| Checkout and payment gateway integration | redirects, callbacks, status polling, timeouts |
| Double-entry ledger and accounting | journals, balanced postings, immutability, period close |
| Loan lifecycle management | origination to closure state machines |
| Loan disbursement and repayment | payout flows, schedules, allocation of payments |
| Interest and fee calculation | day-count conventions, accrual, rounding policy |
| Payment settlement | settlement files, timing, fees |
| Financial reconciliation | statement matching, break management |
| Fraud detection and transaction monitoring | rules and models, alert queues, feedback loops |

Before adding one: confirm the need with a real requirement, check that it encodes a workflow rather than knowledge the model already has, and follow `docs/skill-anatomy.md`.
