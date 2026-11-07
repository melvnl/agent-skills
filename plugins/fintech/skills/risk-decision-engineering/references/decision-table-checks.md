# Decision table checks

## Bands as half-open intervals

Represent numeric bands as `[lower, upper)` with `None` for unbounded ends. This makes gaps and overlaps checkable mechanically.

```python
from decimal import Decimal

def validate_bands(bands):
    """bands: list of (lower: Decimal|None, upper: Decimal|None, outcome). Returns problems."""
    problems = []
    ordered = sorted(bands, key=lambda b: (Decimal("-Infinity") if b[0] is None else b[0]))
    if ordered[0][0] is not None:
        problems.append(f"gap below {ordered[0][0]}")
    for prev, cur in zip(ordered, ordered[1:]):
        prev_upper, cur_lower = prev[1], cur[0]
        if prev_upper is None:
            problems.append(f"band {prev} is unbounded above but another band follows")
        elif cur_lower is None or cur_lower < prev_upper:
            problems.append(f"overlap between {prev} and {cur}")
        elif cur_lower > prev_upper:
            problems.append(f"gap [{prev_upper}, {cur_lower})")
    if ordered[-1][1] is not None:
        problems.append(f"gap at and above {ordered[-1][1]}")
    return problems

# Example: score bands
assert validate_bands([(None, Decimal(550), "reject"), (Decimal(550), Decimal(600), "manual_review"),
                       (Decimal(600), None, "approve")]) == []
```

## Multi-condition tables

For tables over several inputs (score band × debt-ratio band × bureau flag):

- **Gaps**: enumerate the cross product of each input's bands and categories (plus "missing" per input) and check that every cell matches at least one rule.
- **Overlaps**: for each cell, list matching rules; more than one match is an error unless the table declares precedence or aggregation.
- **Unreachable rules**: under first-match precedence, a rule that matches no cell before an earlier rule does is dead and should be removed or reordered.

The cross product grows quickly; enumerate band representatives (one value per band plus each boundary), not raw values.

## Evaluator trace

```json
{
  "rule_set_version": "eligibility-v15",
  "evaluated_at": "2026-11-07T09:14:03Z",
  "precedence": "first_match",
  "trace": [
    {"rule": "R1", "condition": "bureau_default_12m == true", "inputs": {"bureau_default_12m": false}, "matched": false},
    {"rule": "R2", "condition": "score < 550", "inputs": {"score": 612}, "matched": false},
    {"rule": "R3", "condition": "score >= 600 and debt_ratio < 0.35", "inputs": {"score": 612, "debt_ratio": "0.31"}, "matched": true}
  ],
  "outcome": "approve",
  "reason_codes": ["SCORE_ABOVE_THRESHOLD", "DEBT_RATIO_OK"]
}
```

Store the trace (or enough of it to reproduce) in the decision record. Keep input values in the trace minimal and policy-relevant: it is sensitive data.
