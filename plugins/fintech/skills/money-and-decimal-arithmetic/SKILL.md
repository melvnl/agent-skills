---
name: money-and-decimal-arithmetic
description: Handles monetary and precision-sensitive values exactly: Decimal built from strings, amount-plus-currency values, explicit rounding modes applied only at policy-defined points, currency minor units, allocation that preserves totals, DECIMAL storage, and string serialization in APIs and events. Use whenever code computes, stores, compares, rounds, splits, converts or serializes money, rates, scores or percentages.
---

# Money and Decimal Arithmetic

## Overview

Binary floating point can't represent most decimal fractions (`0.1 + 0.2 == 0.30000000000000004`), and rounding decisions made casually turn into cents that disappear, totals that don't add up, and disputes. This skill makes every monetary value exact, every rounding step explicit and policy-backed, and every split preserve its total.

## When to use

- Any computation, comparison, storage, or serialization of money, interest or fee rates, percentages, ratios used in decisions (debt-to-income), or scores with decimal thresholds.
- Splitting or allocating amounts; converting currencies.

**When not to use:** interest accrual conventions and fee schedules belong to a domain spec (see the fintech extension catalog); this skill covers the arithmetic they rely on.

## Inputs and context

1. The rounding policy: mode (half-up, half-even, down), precision, and *where* rounding happens (per line item, per total, at display only). It is a business rule: get it from the spec or the owner.
2. Currencies in scope and their minor units (ISO 4217 exponent; some currencies are commonly handled without minor units in practice regardless of the ISO exponent; follow the project's rule).
3. Existing money types, helpers, and database column definitions.
4. Consumers of serialized values (mobile and JavaScript clients parse JSON numbers as floats).

## Process

1. **Use `decimal.Decimal`** (or the project's money type), never `float`, for money and decision-relevant ratios.
2. **Construct from strings or integers**, never from floats: `Decimal("0.1")`, not `Decimal(0.1)` (which is `0.1000000000000000055511151231257827...`). Parse inputs as strings; reject float inputs at the boundary.
3. **Carry currency with the amount.** Represent money as `(amount: Decimal, currency: str)`; arithmetic and comparison across currencies raise an error instead of silently mixing.
4. **Round only where the policy says**, with an explicit mode: `amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`. Python's default context rounding is `ROUND_HALF_EVEN` (banker's rounding); never rely on a default when the policy names a mode. Keep intermediate results unrounded unless the policy rounds per step.
5. **Mind the context precision** (28 significant digits by default) for long chains of multiplication and division; set a local context (`decimal.localcontext()`) when a calculation needs more, and document it.
6. **Allocate without losing cents**: when splitting an amount (installments, shares), compute the rounded parts and assign the remainder deterministically (for example, to the last part or by the largest-remainder method) so the parts sum exactly to the total (example below).
7. **Compare exactly**: thresholds compared as `Decimal` with defined inclusivity; never compare a float score to a `Decimal` threshold.
8. **Store exactly**: `DECIMAL(p, s)` columns sized for the maximum value and needed scale (Django `DecimalField(max_digits=..., decimal_places=...)`), with the currency in a column or fixed by the schema. Integer minor units (cents) are a valid alternative when the codebase already uses them consistently. Don't mix both styles.
9. **Serialize as strings** in APIs and events (`"150000.00"`) with the currency (`api-design`). DRF's `DecimalField` returns strings by default (`COERCE_DECIMAL_TO_STRING`); Pydantic v2 serializes `Decimal` as a string in JSON mode. Check the project's serializers instead of assuming.
10. **Convert currencies with explicit rates**: the rate as a `Decimal` with its source and timestamp recorded, and rounding applied once to the target currency's minor unit.
11. **Test the arithmetic**: rounding at `.5` boundaries for the policy's mode, allocation sums equal the total for many inputs, currency mismatch raises, serialization round-trips.

### Examples

```python
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP

assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
assert Decimal("10.005").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("10.01")
assert Decimal("10.005").quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN) == Decimal("10.00")

def allocate(total: Decimal, parts: int, unit: Decimal = Decimal("0.01")):
    """Split `total` into `parts` amounts that sum exactly to `total`; remainder goes to the first parts."""
    base = (total / parts).quantize(unit, rounding="ROUND_DOWN")
    remainder = total - base * parts
    extra = int(remainder / unit)
    return [base + unit if i < extra else base for i in range(parts)]

shares = allocate(Decimal("100.00"), 3)
assert shares == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")] and sum(shares) == Decimal("100.00")
```

## Output

Arithmetic using exact types, explicit rounding at policy points, total-preserving allocation, and a short note of the rounding policy applied (mode, precision, where) with its source.

## Verification

- [ ] No `float` in monetary or decision-threshold code paths (search the diff for `float(` and float literals in money code).
- [ ] Every `quantize` names its rounding mode, and the mode matches the policy.
- [ ] Allocation tests assert parts sum to the total across many inputs.
- [ ] Money values carry currency; mixed-currency operations raise.
- [ ] Storage columns have sufficient precision and scale; APIs and events serialize decimals as strings.
- [ ] Boundary tests at `.5` cases for the policy's rounding mode pass.

## Escalation

Ask the owner when: the rounding mode, precision, or rounding point isn't specified; a currency's minor-unit handling is unclear; or changing rounding would alter amounts already shown to customers or stored.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Floats are fine; we round at the end." | Errors accumulate before the end, and comparisons at thresholds flip. |
| "Python rounds the normal way." | Its default is half-even. Name the mode the policy wants. |
| "A cent off in a split doesn't matter." | Multiplied by volume, it is a reconciliation break. Preserve totals. |
