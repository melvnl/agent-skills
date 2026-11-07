# Workflow: New Project

> **Scope:** Project-agnostic. Use when bootstrapping a new project (or adopting the Software Factory in an existing repository).

## Purpose

Establish a project's product and engineering foundation so that feature work can start with clear requirements, a documented architecture, and a verified development environment.

## Inputs

| Input | Source | Required |
|---|---|---|
| Project idea / vision, target users, constraints | Human owner | Yes |
| Technology preferences or mandates | Human owner | If any |
| Existing repository contents | Repository inspection | If adopting into an existing repo |
| `.factory/` (core, workflows, templates) | This factory | Yes |

## Outputs (standard project layout)

```text
CLAUDE.md                     # Agent entry point: identity, stack, reading order, commands, phase
README.md                     # Human entry point (short; links to CLAUDE.md and docs)
product/
  PRODUCT_BRIEF.md            # from templates/PROJECT_BRIEF.md
  PRD.md                      # from templates/PRD.md
  PERSONAS.md
  ROADMAP.md                  # phases with deliverables and acceptance criteria
  FEATURES.md                 # feature catalog with IDs, phase, status
engineering/
  ARCHITECTURE.md
  TECH_STACK.md
  DATA_MODEL.md
  API_CONTRACTS.md
  SECURITY_AND_PRIVACY.md
  DEVELOPMENT_GUIDE.md        # setup, commands, conventions, quality gates
  adr/0001-*.md               # from templates/ARCHITECTURE_DECISION_RECORD.md
specs/                        # one folder per feature: SPEC.md, DESIGN.md
tasks/                        # STATUS.md, task breakdowns, implementation reports
```

A project may adapt names, but must document the mapping in `CLAUDE.md`.

## Execution steps

### Stage A — Discover (no code)

1. **Inspect the repository** (if any): structure, existing docs, configs, source, conventions. Record what exists and what will be preserved.
2. **Interview / read the brief**: problem, users, goals, non-goals, constraints (budget, timeline, platform, compliance, data sensitivity). Ask one question at a time, starting with whatever the existing notes don't answer; calibrate depth to the project (personal, business, regulated). Save the interview, with the owner's answers in their words, as `product/sources/discovery-<date>-<slug>.md`: it is the source the PRD traces to. If the `product-discovery` skill is available, use it for this stage and stage B.
3. **List open questions** and classify each as blocking or non-blocking.

### Stage B — Define the product

4. Write `product/PRODUCT_BRIEF.md` from `templates/PROJECT_BRIEF.md`.
5. Write `product/PERSONAS.md` (who, context, goals, pain points, accessibility needs).
6. Write `product/PRD.md` from `templates/PRD.md`: functional and non-functional requirements with stable IDs.
7. Write `product/FEATURES.md`: a catalog mapping feature IDs → requirements → phase → status.
8. Write `product/ROADMAP.md`: phases, each with deliverables, explicit acceptance criteria, and exit criteria. The first phase must be independently useful.
9. **Self-check the drafts** before approval: contradictions, vague terms, untestable statements, and missing non-functional categories (the `prd-analysis` skill does this if available). Label every statement Confirmed, Proposed, Open question, or Future consideration; never present a proposal as confirmed.

### Stage C — Define the engineering foundation

10. Select the stack; write `engineering/TECH_STACK.md` with rationale, alternatives, and phase applicability.
11. Write `engineering/ARCHITECTURE.md`: system context, module boundaries, data flow, trade-offs (Mermaid diagrams encouraged).
12. Write `engineering/DATA_MODEL.md`: entities, ownership, invariants, units, history stability, migration strategy.
13. Write `engineering/API_CONTRACTS.md`: service/API boundaries and schemas.
14. Write `engineering/SECURITY_AND_PRIVACY.md`: data classification, auth, isolation, secrets, retention/deletion.
15. Record the foundational decisions in `engineering/adr/0001-*.md`.
16. Write `engineering/DEVELOPMENT_GUIDE.md`: prerequisites, setup, commands (mark planned vs. existing), directory conventions, quality gates mapped to commands.

### Stage D — Agent entry point

17. Write `CLAUDE.md`: concise identity, stack, structure, reading order per task type, reference to `.factory/core/AGENT_BEHAVIOR.md` and workflows, commands, current phase, architectural constraints. **Do not copy factory content into it — link.**
18. Create `tasks/STATUS.md` with the current phase, next actions, and blockers.

### Stage E — Initialize the stack *(separate, approved step)*

19. Scaffold the application using the chosen stack's official generator.
20. Configure: strict typing, formatter, linter, test runner(s), E2E runner, environment validation, `.env.example`, `.gitignore`.
21. Add one trivial passing test per test level to prove the pipeline.
22. **Verify the environment:** install, lint, type-check, test, build, run locally. Record the actual outputs.
23. Update `DEVELOPMENT_GUIDE.md` and `CLAUDE.md` so documented commands match real ones.

## Quality gates

| Gate | Check |
|---|---|
| G1 — Product clarity | Every PRD requirement has an ID and is testable; goals and non-goals are explicit. |
| G2 — Phase independence | Phase 1 is usable without later-phase infrastructure. |
| G3 — Consistency | Product, architecture, data model, and security docs agree (entities, user model, phase boundaries). |
| G4 — Factory hygiene | No project-specific content was added to `.factory/`. |
| G5 — Decision status | Every significant decision is labeled Confirmed / Proposed / Open / Future. |
| G6 — Environment (Stage E) | Install, lint, type-check, tests, and build all succeed on a clean checkout. |

## Human approval required

- Product brief, PRD, and roadmap (before Stage C is treated as final).
- Technology stack and ADR-0001.
- Starting Stage E (scaffolding code).
- Any decision marked **Proposed** that is expensive to reverse.
