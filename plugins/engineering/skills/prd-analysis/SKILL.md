---
name: prd-analysis
description: Analyzes a large or AI-generated PRD before anything is built: inventories it, extracts requirements, business rules, entities and actors with source references, and surfaces contradictions, ambiguities, duplicates and missing NFRs. Use when given a PRD, spec, or requirements document to plan from, or asked to review or break down requirements.
---

# PRD Analysis

## Overview

Large PRDs, especially ones drafted or expanded with AI, read as complete while hiding contradictions, vague terms, duplicated or invented requirements, and missing non-functional needs. Building from them directly turns each defect into rework. This skill reads the document systematically, extracts what it actually says with traceable source references, and produces an analysis that a human resolves **before** specification and design. It never invents requirements.

## When to use

- A PRD, spec, product brief, or requirements export arrives and work will be planned from it.
- Asked to "review", "analyze", "break down", or "find gaps in" requirements.
- Phase 1 of the Software Factory `PRD_TO_IMPLEMENTATION` workflow.

**When not to use:** turning an *approved* analysis into feature specs with ids → `specification-decomposition`. Writing acceptance criteria → `acceptance-criteria-engineering`.

## Inputs and context

1. **The source document(s)**, in full. Convert formats to text first (Markdown, `pdftotext`, docx export); note anything lost (tables, images, diagrams).
2. **Existing product context**: in a Software Factory repo, `product/PRD.md`, `product/FEATURES.md`, the glossary, and existing `specs/`, so new requirements are compared against what is already specified or built.
3. **The domain**: regulated or financial domains need explicit auditability, data retention, and authorization requirements; their absence is itself a finding.
4. **Who can answer questions**: the owner of the document.

## Process

1. **Preserve the source.** Store it unmodified (Software Factory: `product/sources/<name>-v<version or date>.<ext>`). Record version, date, author if known. The analysis cites this copy.
2. **Inventory the structure.** List sections with a stable reference scheme (`S1 §3.2`, or file + heading anchor), size, and anything non-textual. For documents too large to hold at once, analyze section by section and keep a running index in the analysis file (see `context-engineering`).
3. **Extract atomic statements.** One requirement per row, quoted or closely paraphrased, each with its source reference. Classify each: functional requirement, non-functional requirement, business rule (formula, threshold, eligibility condition), constraint, assumption, out of scope, or question.
4. **Extract the domain model.** Actors and roles (with permissions implied), entities and their lifecycle states, external systems and integrations, and a glossary. Flag synonyms (one concept, several names) and homonyms (one name, several concepts).
5. **Run the quality checks** in [references/quality-checks.md](references/quality-checks.md): contradictions, ambiguities, duplicates, missing NFR categories, untestable statements, missing actors or boundaries, numeric inconsistencies, and AI-generation artifacts (generic filler, integrations nobody mentioned, invented numbers).
6. **Rate each issue**: **Blocking** (two reasonable readings lead to different builds, or a contradiction), **Major** (gap that will cause rework if unaddressed), **Minor** (wording, consistency).
7. **Compare with what exists** (factory repos): mark each extracted requirement *new*, *already specified* (cite `FR-x` / spec), *already implemented*, or *conflicts with existing* (cite).
8. **Write the analysis** from [references/analysis-template.md](references/analysis-template.md) and batch questions for the owner: most important first, each with options and a recommendation.
9. ⏸ **Gate:** the owner resolves Blocking issues (or explicitly accepts them as open) before `specification-decomposition`. Record each decision with date and who decided.

## Output

`product/analysis/<source-name>-analysis.md` (Software Factory) or an equivalent file, containing: source metadata and inventory; extracted requirements with source refs and classification; domain model (actors, entities, states, integrations, glossary); issues table (id, type, severity, source refs, description, question, recommendation); comparison with existing specs; and the owner decision log. The PRD itself is not edited.

## Verification

- [ ] Every extracted row has a source reference that leads back to the preserved source.
- [ ] No row states something the source doesn't (spot-check at least 10 rows, or all for short documents).
- [ ] Every section of the inventory was read; skipped content (images, tables lost in conversion) is listed.
- [ ] Every NFR category in the checklist is marked present, missing, or not applicable.
- [ ] Every Blocking issue has a question for the owner.
- [ ] Contradictions cite both sides.

## Escalation

Stop and ask when: the source is incomplete, truncated, or several versions disagree on which is current; requirements involve legal, regulatory, credit-decision, or financial policy the document only implies; or the document contradicts already-implemented behavior (that decision belongs to the owner). Never resolve an ambiguous business or financial rule by choosing the reading that seems sensible.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The intent is obvious." | Then the owner can confirm it in one line. Unconfirmed intent becomes a bug report later. |
| "I'll fill in the missing NFRs with standard values." | Proposed values are fine; presenting them as requirements is invention. Mark them *Proposed*. |
| "It's too long to read fully; the summary section is enough." | Contradictions live in the details. Chunk it, but read it. |
| "AI wrote it, so it's consistent." | Generated documents are fluent, not consistent. Check the numbers. |

## References

- [references/quality-checks.md](references/quality-checks.md): checks, vague-term list, NFR checklist, AI-artifact signals.
- [references/analysis-template.md](references/analysis-template.md): the analysis document skeleton.
