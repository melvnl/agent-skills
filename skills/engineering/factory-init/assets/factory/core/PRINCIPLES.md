# Engineering Principles

> **Scope:** Project-agnostic. These principles apply to every project built with this Software Factory.
> Project-specific rules live in the project's own documentation (e.g. `CLAUDE.md`, `engineering/`), never here.

These principles are the tie-breakers. When a standard, workflow, or template is silent or ambiguous, decide by applying these principles in order of listed priority where they conflict.

---

## 1. Correctness over implementation speed

Shipping the wrong thing quickly is slower than shipping the right thing once.

- Prefer a smaller, correct change over a larger, partially correct one.
- A change that is "done except for edge cases" is not done.
- **In practice:** if a deadline forces a trade-off, cut scope, not correctness. Record cut scope as a follow-up task.

## 2. Specification before implementation

Code is written to satisfy a written specification, not an impression of one.

- Every non-trivial change starts from a spec: a feature spec, a bug report with expected behavior, or a refactoring brief with invariants (see `.factory/workflows/`).
- The spec is the contract. If implementation reveals the spec is wrong, update the spec first (with approval), then the code.
- **Trivial change threshold:** a change that touches ≤ 1 module, adds no new behavior, and has no data/contract impact (typo fix, copy change, dependency patch) may skip a formal spec but still needs a clear description of intent.

## 3. Explicit requirements and acceptance criteria

Every requirement must be testable. If you cannot describe how to verify it, it is not a requirement yet.

- Acceptance criteria use observable outcomes: *"Given X, when Y, then Z"*.
- Vague words ("fast", "intuitive", "secure") must be replaced by measurable criteria ("p95 < 200 ms", "completable in ≤ 3 taps", "inaccessible without a valid session").
- Acceptance criteria are never silently changed. Changes are proposed, approved, and recorded.

## 4. Small, incremental changes

- Each change should be reviewable in one sitting (guideline: ≤ ~400 lines of meaningful diff).
- Each increment leaves the system working: builds, tests pass, no half-migrated states on the main branch.
- Prefer a sequence of safe steps (add → migrate → remove) over one big-bang change.

## 5. Separation of concerns

- Business/domain rules do not know about UI frameworks, HTTP, databases, or vendors.
- Infrastructure (storage, network, third-party APIs) is reached through narrow, explicit boundaries.
- A module has one reason to change. If describing a module requires "and", consider splitting it.

## 6. Simplicity over unnecessary abstraction

- Build for today's known requirements plus clearly documented near-term ones — not for hypothetical futures.
- Introduce an abstraction only when there are **at least two concrete uses** or a **documented, planned** second implementation (e.g. a storage adapter that will be swapped in a scheduled phase).
- Prefer simple architectures (e.g. a modular monolith) until there is evidence that more complexity is needed.
- Do not introduce dependencies without justification (see `ENGINEERING_STANDARDS.md` § Dependency management).

## 7. Maintainability

Code is read far more often than it is written.

- Optimize for the next engineer (human or AI) who has no context.
- Consistency with existing conventions beats personal preference.
- Never silently change existing behavior; behavior changes are explicit, specified, and tested.

## 8. Security and privacy by design

Security and data privacy are mandatory, not features.

- Collect the minimum data needed. Store it for the minimum time needed.
- Treat all external input as untrusted.
- Design data isolation before writing the first query, not after.
- Secrets never live in source control or client-side bundles.

## 9. Evidence-based engineering decisions

- Significant decisions (architecture, data model, major dependency, security model) are recorded in an Architecture Decision Record (`.factory/templates/ARCHITECTURE_DECISION_RECORD.md`).
- Claims are backed by evidence: benchmarks, documentation, reproductions, test results — not assertions.
- When evidence is missing, state the assumption explicitly and mark the decision as *proposed*.

## 10. Human accountability

AI agents accelerate work; humans own outcomes.

- A named human approves specifications, architecture decisions, destructive operations, and merges to the main branch.
- Agents report what they did, what they did not do, and what they are unsure about (see `AGENT_BEHAVIOR.md`).
- Every business requirement must trace to a human-approved source.

---

## Decision status vocabulary

Use these labels consistently across all project documentation:

| Label | Meaning |
|---|---|
| **Confirmed** | Approved by the accountable human. Safe to build on. |
| **Proposed** | Recommended with rationale; awaiting approval. Build on it only if reversible. |
| **Open question** | Unresolved; blocks or materially affects some work. Must name what it blocks. |
| **Future consideration** | Deliberately out of current scope. Do not build. |
