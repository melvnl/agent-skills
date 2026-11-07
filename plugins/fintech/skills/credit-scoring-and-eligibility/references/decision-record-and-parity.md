# Decision record and parity testing

## Decision record (minimum fields)

| Field | Notes |
|---|---|
| `decision_id` | immutable id |
| `application_ref` | internal reference, not personal data |
| `decided_at` | UTC, from the injected clock |
| `rule_set_version`, `config_version`, `model_version` | exact versions used |
| `input_snapshot_ref` or `inputs` | immutable snapshot of the inputs used (or a reference to a write-once store); minimized to what the policy uses |
| `input_hash` | hash of the canonicalized inputs, for integrity and dedup |
| `features` | derived values actually used |
| `score` | with model or scorecard version |
| `rule_results` | ordered list: rule id, version, result, values compared |
| `outcome` | approve / reject / manual_review / ... |
| `limit_amount`, `currency` | if applicable, exact decimal |
| `reason_codes` | ordered, stable codes |
| `fallback_applied`, `fallback_reason` | e.g. `BUREAU_TIMEOUT` |
| `correlation_id`, `request_id` | for joining logs and traces |
| `decided_by` | service and version (and human actor for manual decisions) |
| `supersedes_decision_id` | for re-decisions; records are never updated in place |

Store sensitive inputs according to the project's retention and access policy; the record itself is an audit artifact (`financial-auditability`).

## Reproducibility test

```python
def test_stored_decision_reproduces(decision_fixture):
    rec = decision_fixture
    outcome = evaluate(load_snapshot(rec.input_snapshot_ref), versions=rec.versions, now=rec.decided_at)
    assert (outcome.outcome, outcome.limit_amount, outcome.reason_codes) == (rec.outcome, rec.limit_amount, rec.reason_codes)
```

## Golden dataset

- Cases: representative profiles per outcome, every threshold boundary, missing and malformed inputs, fallback scenarios, and every past production incident's input pattern.
- Each case: id, inputs (synthetic or de-identified), versions, expected outcome, limit, reason codes, and the approver of the expectation.
- Stored with the code; changes to expected values require the policy owner's approval (they are policy changes).

## Parity procedure (migration or engine rewrite)

1. **Replay**: run N historical inputs (with their original versions) through the old and new implementations offline.
2. **Shadow**: deploy the new implementation to evaluate live requests without affecting outcomes; log both results with the correlation id.
3. **Compare** on outcome, limit, reason codes, and rule results. Categorize each difference:
   - *expected* (an intended policy change, approved),
   - *data* (input differences between environments),
   - *defect* (the new implementation is wrong),
   - *legacy defect* (the old one was wrong: needs an owner decision).
4. **Report** counts per category, examples by id, and the parity rate.
5. **Cut over** behind a flag once the owner accepts the report; keep the old path runnable for rollback until a post-cutover window passes with stable decision metrics.
