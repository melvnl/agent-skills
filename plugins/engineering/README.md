# melvin-engineering

Spec-driven engineering core: the Software Factory and the skills for turning requirements into verified, incremental changes.

## Skills

### Software Factory

- **[factory-init](skills/factory-init/SKILL.md)**: Bootstrap (or `--verify`) the `.factory/` software factory in a repository.
- **[factory-router](skills/factory-router/SKILL.md)**: Classify, size, and route each request in a factory repo to its workflow.

`skills/factory-init/assets/factory-router.SKILL.md` is a bundled copy of `skills/factory-router/SKILL.md`, installed into target repos. Edit the source and copy it over; `scripts/validate.py` fails on drift.

### Specification and planning

- **[prd-analysis](skills/prd-analysis/SKILL.md)**: Analyze a large or AI-generated PRD: extract requirements with source references, surface contradictions, ambiguities, duplicates, and missing NFRs.
- **[specification-decomposition](skills/specification-decomposition/SKILL.md)**: Turns analyzed requirements into stable ids, domain groups, a feature catalog, and atomic feature specs with traceability.
- **[acceptance-criteria-engineering](skills/acceptance-criteria-engineering/SKILL.md)**: Writes and reviews atomic, testable Given/When/Then criteria covering boundaries, permissions, state, failures, idempotency, time, money, observability and audit.
