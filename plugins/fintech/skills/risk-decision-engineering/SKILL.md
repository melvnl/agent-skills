---
name: risk-decision-engineering
description: Implements rule engines and decision tables for risk decisions: explicit precedence, exact threshold and missing-value semantics, rule-set validation for gaps, overlaps and unreachable rules, immutable versioned policies with audited activation, deterministic evaluation with an explanation trace, table-driven regression tests, and rule-hit instrumentation. Use when building or changing rules, decision tables, policy configuration or a decision engine.
---

# Risk Decision Engineering

## Overview

Risk policies are usually expressed as rules and tables: "if score ≥ 600 and debt ratio < 40%, approve; if the bureau has a default in 12 months, reject". The engineering risk is in the semantics nobody wrote down: which rule wins when two match, what "< 40%" means at exactly 40, what happens when an input is missing, and which version decided last March's case. This skill makes those semantics explicit, validates rule sets before they can go live, and keeps every evaluation explainable.

## When to use

- Building or changing a rule engine, decision table, scorecard bands, or policy configuration.
- Adding, editing, or retiring rules; changing precedence or thresholds.
- Explaining or debugging why a rule fired.

**When not to use:** the end-to-end credit pipeline (inputs, fallbacks, parity, decision records) → `credit-scoring-and-eligibility`. Who may change and activate policies → `financial-authorization`.

## Inputs and context

1. The policy as approved: rules, tables, thresholds, units, and intended precedence, with its owner.
2. The current engine: rules in code vs rules as data (tables, configuration, a DSL), how they are loaded, versioned, and activated.
3. Input definitions: types, units, ranges, and what "missing" means for each.
4. Existing tests and decision records.

## Process

1. **Choose the representation deliberately.** Rules in code are type-checked and reviewed with the code, but every change is a deploy. Rules as data (tables, configuration) change without deploys but need their own validation, versioning, review, and activation controls. Either way, the policy has **one** source of truth.
2. **Define precedence explicitly**: first-match in a declared order; highest priority wins; or all matching rules apply with a defined aggregation (most restrictive outcome wins, sum of points). Write it in the policy and in the engine. Never rely on file order, dict order, or database row order implicitly.
3. **Define comparison semantics exactly**: inclusive or exclusive bounds for every threshold (half-open intervals `[lo, hi)` for bands avoid both gaps and overlaps); units and scaling (percent as `0.40` or `40`?); decimal comparison (`money-and-decimal-arithmetic`); time zone for date rules.
4. **Define missing-value behavior per input**: reject, route to manual review, treat as worst case, or skip the rule. Never let `None` compare as false and fall through to approval.
5. **Validate rule sets before activation** ([references/decision-table-checks.md](references/decision-table-checks.md)): **gaps** (input combinations no rule covers), **overlaps** (several rules match where precedence isn't meant to resolve it), **unreachable** rules (shadowed by an earlier rule), type and unit errors, and references to unknown inputs. A rule set that fails validation can't be activated.
6. **Version policies immutably.** A version, once used in a decision, never changes. Edits create a new version; activation is a separate, approved, audited step with an effective time (`financial-auditability`, `financial-authorization`). Keep old versions loadable so past decisions can be re-evaluated.
7. **Evaluate deterministically and explain**: the evaluator takes inputs, version, and evaluation time, and returns the outcome plus a **trace** (each rule considered, its inputs and thresholds, matched or not, in order). The trace feeds reason codes and the decision record.
8. **Test table-driven**: one test per rule row at, below, and above each threshold; precedence tests where rules overlap by design; missing-value tests per input; a validation test that fails on known-bad rule sets; and the regression golden dataset from `credit-scoring-and-eligibility`.
9. **Instrument**: rule hit counts by rule id and version, outcome distribution by version, evaluation latency; alert on hit-rate shifts after activation (a rule suddenly matching 0% or 100%) (`observability-engineering`).
10. **Review changes as policy diffs**: show the before/after table and the golden-dataset outcome differences to the policy owner, not just the code diff.

## Output

The rules or tables, the evaluator with precedence and missing-value semantics, validation that runs before activation, table-driven tests, and a policy change summary:

```markdown
### Policy change: eligibility rules v14 -> v15
| Rule | v14 | v15 |
|---|---|---|
| R3 debt ratio | < 0.40 approve | < 0.35 approve; [0.35, 0.40) manual_review |
Validation: no gaps, no unintended overlaps, no unreachable rules
Golden dataset: 412 cases; 9 outcome changes (all R3 band), listed in the PR
Activation: pending owner approval; effective time to be set at activation
```

## Verification

- [ ] Precedence is declared and tested.
- [ ] Every threshold has explicit inclusivity, units, and boundary tests.
- [ ] Every input has defined missing-value behavior, tested.
- [ ] Rule-set validation (gaps, overlaps, unreachable, types) passes and blocks activation on failure.
- [ ] Used versions are immutable; old versions remain loadable; activation is separate and audited.
- [ ] Evaluation returns a trace; determinism test passes.
- [ ] Rule-hit metrics exist per version.

## Escalation

Always ask the policy owner when: precedence, inclusivity, or missing-value behavior isn't specified; validation finds gaps or overlaps in an approved policy; a change alters golden-dataset outcomes; or a version needs activation.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Rules are evaluated in the order they're listed; that's obvious." | Until someone sorts the config file. Declare precedence and test it. |
| "Missing income just fails the rule." | Failing an exclusion rule can mean approval. Define missing behavior per input. |
| "Fix the typo in the active version." | Then past decisions point at a version that no longer says what they used. New version. |

## References

- [references/decision-table-checks.md](references/decision-table-checks.md): band and table validation (gaps, overlaps, unreachable), evaluator trace shape.
