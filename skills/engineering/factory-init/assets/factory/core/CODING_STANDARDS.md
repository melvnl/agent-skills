# Coding Standards

> **Scope:** Project-agnostic and language-agnostic. Language-specific tooling (formatter, linter config) is declared per project in its development guide.

---

## 1. Readability and maintainability

Operational definition of "readable code":

- A reviewer can state what a function does from its **name and signature** alone.
- Functions do one thing. Guideline: ≤ ~40 lines; > 3 levels of nesting is a signal to extract or use early returns.
- Files have one primary responsibility. Guideline: ≤ ~300 lines; larger files need a reason.
- No "clever" code where plain code works (nested ternaries, dense one-liners, implicit coercions).
- Magic numbers and strings become named constants with units in the name (`MAX_UPLOAD_BYTES`, `SESSION_TTL_MS`).
- Formatting is automated (formatter + linter). Never hand-argue formatting in review.

## 2. Naming conventions

| Element | Convention | Example |
|---|---|---|
| Variables / functions | Descriptive, intention-revealing; functions start with a verb | `calculateRemainingBudget`, `isOverLimit` |
| Booleans | `is/has/can/should` prefix | `hasTarget`, `isLoading` |
| Collections | Plural nouns | `entries`, `profilesById` |
| Types / classes / components | `PascalCase` nouns | `OrderSummary`, `UserCard` |
| Constants | `UPPER_SNAKE_CASE` for true module-level constants | `DEFAULT_PAGE_SIZE` |
| Quantities | Include the unit | `weightG`, `timeoutMs`, `priceCents` |
| Files | Follow the project's declared convention consistently (e.g. `kebab-case.ts`) | `order-summary.tsx` |

- Use **domain language** from the project's product docs. One concept = one name across code, docs, database, and UI copy.
- Avoid abbreviations except universally known ones (`id`, `url`, `api`).
- Avoid meaningless names: `data`, `info`, `item`, `handle`, `manager`, `util`, `temp` — unless qualified.

## 3. Modularity

- Organize code by **feature/domain module**; inside a module, separate domain logic, application services, UI, and infrastructure adapters.
- A module's public API is explicit (e.g. `index.ts` exports). Cross-module imports go through it.
- No circular dependencies between modules.
- Shared code must be used by ≥ 2 modules; otherwise keep it local.

## 4. Type safety

- Strict type checking enabled; zero type errors is a merge requirement.
- No `any` (or language equivalent) in committed code except at a validated boundary, with a comment explaining why. Prefer `unknown` + validation.
- Model domain states with precise types: unions/enums for finite states, branded/nominal types for IDs where mix-ups are costly.
- Make illegal states unrepresentable (e.g. discriminated unions instead of several optional booleans).
- Runtime-validate data crossing trust boundaries (user input, network, storage); derive static types from the schema to avoid drift.
- Avoid non-null assertions/force-unwraps; handle the null case or prove it impossible via types.

## 5. Avoiding unnecessary abstractions

Before introducing an interface, base class, generic helper, factory, or wrapper, it must satisfy at least one:

1. There are ≥ 2 concrete implementations or call sites **today**, or
2. A second implementation is **documented and scheduled** (e.g. in the roadmap), or
3. It isolates an external dependency that is expected to change.

Otherwise, write the direct code. Duplication of two small similar blocks is acceptable; extract on the third occurrence ("rule of three").

## 6. Documentation requirements

| What | Required documentation |
|---|---|
| Public module API / exported functions with non-obvious behavior | Doc comment: purpose, parameters with units, return, errors thrown |
| Business rules | Comment linking to the spec/requirement ID it implements (e.g. `// FR-03`) |
| Non-obvious decisions / workarounds | Comment explaining **why**, not what. Link the issue/ADR. |
| `TODO` | Must include an owner or task reference: `TODO(TASK-12): ...`. No anonymous TODOs. |
| Architecture-level changes | Update project engineering docs and/or add an ADR in the same change |

Do not write comments that restate the code.

## 7. Error handling (code level)

- Use the language's idiomatic mechanism consistently (exceptions or result types — pick one per layer and document it).
- Throw/return **typed, domain-meaningful errors** (`ProfileNotFoundError`), not generic strings.
- Add context when rethrowing; preserve the original cause.
- No empty `catch` blocks. No `catch` that only logs and continues unless continuing is correct and commented.
- Validate preconditions at function entry for public APIs; use assertions for internal invariants.
- See `ENGINEERING_STANDARDS.md` § Error handling for classification and user-facing rules.

## 8. Refactoring guidelines

- Refactor in **separate commits/changes** from behavior changes. A diff is either a refactor or a feature/fix, not both.
- Tests must be green before and after; do not edit test expectations during a pure refactor (if you must, it is not a pure refactor).
- "Boy Scout rule" is allowed only within files already touched by the task and only for low-risk cleanups (renames, dead code removal, extracting a function). Larger refactors follow `.factory/workflows/REFACTORING.md`.
- Delete dead code instead of commenting it out; version control remembers.

## 9. Code hygiene checklist (pre-commit)

- [ ] Formatter and linter pass with zero warnings in changed files.
- [ ] Type checker passes.
- [ ] No debug output (`console.log`, `print`) left in non-debug code.
- [ ] No commented-out code.
- [ ] No secrets, tokens, or personal data in code, fixtures, or logs.
- [ ] New/changed behavior has tests.
