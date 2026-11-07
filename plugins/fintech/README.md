# melvin-fintech

Fintech backend engineering, scoped to **credit scoring, eligibility, and risk decisioning** in backend services and APIs: data integrity, exact money, decision engineering, authorization, auditability, and reliability.

Depends on `melvin-backend`, `melvin-observability`, and `melvin-security` (installed automatically).

## Skills

- **[financial-data-integrity](skills/financial-data-integrity/SKILL.md)**: Invariants enforced and checked, immutable history, duplicate prevention, cross-service reconciliation, evidence-validated migrations.
- **[credit-scoring-and-eligibility](skills/credit-scoring-and-eligibility/SKILL.md)**: Consistent, versioned, explainable decisions: one policy source, deterministic evaluation, immutable decision records, owner-defined fallbacks, golden and parity tests.
- **[risk-decision-engineering](skills/risk-decision-engineering/SKILL.md)**: Rule engines and decision tables: explicit precedence, exact thresholds and missing values, gap/overlap validation, immutable versions, traced deterministic evaluation.
- **[financial-authorization](skills/financial-authorization/SKILL.md)**: Who may view, decide, override and configure: least privilege, object scoping, maker-checker, amount-based authority, scoped service credentials, tested matrix.
- **[financial-auditability](skills/financial-auditability/SKILL.md)**: Reconstructable actions and decisions: append-only audit records separate from logs, written atomically, integrity-protected, retained, as-of reconstruction.
- **[financial-system-reliability](skills/financial-system-reliability/SKILL.md)**: Correctness-first reliability: owner-defined fail-closed or degraded modes, single effects, safe replay, rerunnable jobs, decision-distribution canaries, peak capacity.

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

Before adding one: confirm the need with a real requirement, check overlap with existing skills (especially `financial-data-integrity` and `money-and-decimal-arithmetic`), and follow `docs/skill-anatomy.md`.
