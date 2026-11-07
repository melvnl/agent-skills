# Invariant checks

## Catalog format

| ID | Invariant | Enforcement | Check | Schedule |
|---|---|---|---|---|
| INV-1 | A decided application has exactly one final decision | unique key (application_id) WHERE is_final; domain code (MySQL: generated column + unique) | Q1 | hourly |
| INV-2 | Credit limit is never negative | CHECK (limit_amount >= 0) (MySQL ≥ 8.0.16) | Q2 | daily |
| INV-3 | Every decision references an existing rule version | FK | Q3 | daily |
| INV-4 | Approved amount ≤ product maximum at decision time | domain code | Q4 | daily |

## Example check queries (MySQL)

```sql
-- Q1: applications with != 1 final decision
SELECT a.id, COUNT(d.id) AS finals
FROM application a LEFT JOIN decision d ON d.application_id = a.id AND d.is_final = 1
WHERE a.status IN ('approved', 'rejected')
GROUP BY a.id HAVING finals <> 1;

-- Q2: negative limits (catches pre-constraint data and engines that don't enforce CHECK)
SELECT id, limit_amount FROM credit_limit WHERE limit_amount < 0;

-- Q4: approved amount above the product max snapshotted at decision time
SELECT d.id FROM decision d WHERE d.outcome = 'approved' AND d.approved_amount > d.product_max_snapshot;
```

"One final decision per application" in MySQL (no partial unique indexes): a generated column such as `final_application_id = IF(is_final, application_id, NULL)` with a `UNIQUE` index on it (NULLs don't collide).

## Near-duplicate detection

```sql
SELECT customer_ref, product_code, DATE(created_at) AS day, COUNT(*) AS n
FROM application
GROUP BY customer_ref, product_code, DATE(created_at)
HAVING n > 1;
```

Report, review with the owner, then decide on prevention (a constraint or idempotency key) and correction (new records, never silent deletes).

## Reconciliation between services

Per period (e.g. day):
1. Counts by category in both systems (decisions by outcome).
2. Sums of monetary columns (approved amounts by product).
3. Per-entity comparison on the join key: present in A not B, present in B not A, field mismatch (compare a hash of normalized key fields to keep the comparison cheap).

Output a mismatch report with categories and examples by id (no personal data), and a metric per category.

## Migration validation

```sql
-- before and after, stored in the migration report
SELECT status, COUNT(*), SUM(approved_amount) FROM decision GROUP BY status;
-- per-row sample comparison between old and new tables
SELECT o.id FROM decision_old o JOIN decision_new n ON n.id = o.id
WHERE NOT (o.outcome <=> n.outcome AND o.approved_amount <=> n.approved_amount AND o.rule_version <=> n.rule_version)
LIMIT 100;
```

`<=>` is MySQL's NULL-safe equality. Run all invariant checks after the migration as well.
