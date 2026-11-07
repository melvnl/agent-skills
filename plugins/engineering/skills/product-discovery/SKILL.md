---
name: product-discovery
description: Turns an idea or an undocumented request into an owner-approved product brief, PRD and roadmap through a one-question-at-a-time interview, with every requirement traced to the interview and labeled confirmed or proposed, then self-checked with prd-analysis. Use when starting a project from an idea, when there is no PRD, or when a request is too vague to specify.
---

# Product Discovery

## Overview

Most bad specifications aren't wrong, they're unasked: nobody established the problem, the user, what "done" means, or what is out of scope, so the gaps get filled by assumptions during implementation. This skill runs the conversation a good product lead would, one question at a time, and writes the answers into the Software Factory's product documents. It never invents requirements: everything it writes is either confirmed by the owner or clearly labeled as a proposal.

## When to use

- **Mode A, idea to product:** a new project from an idea, personal or business: "I want to build…", an empty repository, `NEW_PROJECT` stages A–B.
- **Mode B, request without a PRD:** a capability for an existing project that nobody has written down: "we need X but there's no spec", or a request too vague to write acceptance criteria for.
- A brief exists but is thin (a few paragraphs, a chat summary): use it as the starting point and interview only for gaps.

**When not to use:** a real PRD exists → `prd-analysis`. Requirements are clear and approved → `specification-decomposition` or `acceptance-criteria-engineering`. Market research, competitors, pricing, positioning → marketing or research skills, not this one.

## Inputs and context

1. **What already exists:** README, notes, chat summaries, sketches, an existing `product/` folder, and in Mode B the code and current specs for the affected area. Read them first and never ask what is already written.
2. **The owner:** who decides scope and priorities. If it is a team or business project, who else must approve.
3. **Depth calibration** (ask early, once): personal side project, business or team project, or regulated / financial domain. It sets how far the interview goes (references below).
4. Whether the repository uses the Software Factory (`.factory/`). Without it, write the same documents under `docs/product/` or propose `/factory-init`.

## Process

1. **Detect the mode** (A or B) from the repository and the request; say which one you are running and why.
2. **Calibrate depth** with one question: what kind of project, and how much time the owner wants to spend now. Personal projects get a short interview; business, team, or regulated work gets the full set.
3. **Interview one question per turn.** Pick the question with the highest information value from [references/interview-guide.md](references/interview-guide.md), in roughly this order: problem and user → current alternative → outcome and success measure → core journey → scope and non-goals → rules and constraints → non-functional needs → risks. Make questions specific to what the owner said, offer 2–3 options with a recommendation when the owner may not have an answer, accept "skip" or "you decide" (then record a **Proposed** answer), and follow up when an answer is vague. Never ask several unrelated questions at once.
4. **Reflect back** after each topic cluster in two or three sentences ("So the first version is for X, to do Y, and Z is out of scope. Right?"). Corrections are cheaper now than in the PRD.
5. **Stop at enough.** The interview ends when the done-test below passes, typically 8–15 questions in Mode A and 4–8 in Mode B, or when the owner says stop (remaining unknowns become **Open questions**). Don't run a questionnaire.
6. **Save the interview record** to `product/sources/discovery-<YYYY-MM-DD>-<slug>.md` using [references/discovery-record.md](references/discovery-record.md): every question, the owner's answer in their words, and the decisions. It is the source document that the PRD traces to.
7. **Draft the documents** from the record (mapping in the reference):
   - Mode A: `product/PRODUCT_BRIEF.md`, `product/PERSONAS.md`, `product/PRD.md`, `product/ROADMAP.md` from the factory templates, with phase 1 the smallest independently useful version.
   - Mode B: new `FR`/`NFR`/`BR` rows in `product/PRD.md` (continuing existing ids) with a change-log entry and a `product/FEATURES.md` entry, or a draft `specs/<F-ID>-<slug>/SPEC.md` when the request is a single feature.
   Every statement carries a label: **Confirmed** (the owner said it), **Proposed** (your recommendation, accepted or not yet reviewed), **Open question** (unknown; name what it blocks), or **Future consideration**. Every requirement cites its source (`discovery 2026-11-08 Q5`).
8. **Self-check with `prd-analysis`** on the drafts: contradictions, vague terms, missing NFR categories, untestable statements. Fix what you can from the record and turn the rest into owner questions.
9. ⏸ **Gate:** present the brief, PRD, and roadmap (or the PRD rows or spec) with the open questions. Proposed items become Confirmed only when the owner accepts them.
10. **Hand off.** Mode A → `NEW_PROJECT` stage C (architecture, stack, ADR-0001). Mode B → `specification-decomposition` or `NEW_FEATURE` step 3.

### Done-test

Another engineer reading the drafts can state: who the user is and what problem they have; what the first version does and explicitly doesn't; how success is measured; the business rules with exact values (or that they are open questions); the non-functional needs that matter for this kind of project; and what remains undecided.

## Output

- `product/sources/discovery-<date>-<slug>.md`: the interview record.
- Mode A: product brief, personas, PRD (status Draft), roadmap. Mode B: PRD rows and feature entry, or a draft spec.
- A short summary for the gate:

```markdown
## Discovery: <name> (mode A, business project)
Record: product/sources/discovery-2026-11-08-merchant-credit.md (12 questions)
Drafted: PRODUCT_BRIEF, PERSONAS, PRD (FR-1..FR-9, NFR-1..NFR-5, BR-1..BR-3), ROADMAP (phase 1: 3 features)
Confirmed 14 · Proposed 6 (need your review) · Open questions 4 (Q-1 blocks phase 1 scope)
Self-check (prd-analysis): 1 contradiction resolved, 2 vague terms turned into questions
Next: approve or adjust, then NEW_PROJECT stage C (architecture)
```

## Verification

- [ ] Every requirement and rule traces to the interview record or an existing document.
- [ ] Nothing is presented as Confirmed that the owner didn't say or accept.
- [ ] No invented numbers: targets, limits, and thresholds the owner didn't give are Proposed or Open questions.
- [ ] Goals, non-goals, and a phase 1 that is usable without later phases are explicit (Mode A).
- [ ] The NFR categories relevant to the depth calibration are present, proposed, or open (financial and personal-data projects always cover security, privacy, auditability, observability).
- [ ] The `prd-analysis` self-check ran and its findings are resolved or listed.
- [ ] The owner approved at the gate before any design or code.

## Escalation

Stop and ask when: the owner's answers contradict each other on scope or rules; a requirement implies regulated, credit, or financial policy the owner can't state (that needs whoever owns the policy); the project needs another decision-maker's approval (business partner, client, product team); or the owner wants to start coding before the gate (say what risk that carries, then follow their call).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The idea is clear; let's pick the stack." | Stack choice depends on users, scale, and constraints you haven't asked about yet. |
| "I'll ask everything up front so it's quick." | A wall of questions gets skimmed answers. One at a time, built on the last answer. |
| "I'll fill in sensible defaults for limits and SLAs." | Proposals are welcome; presenting them as requirements is invention. Label them. |
| "It's just a side project; it doesn't need a PRD." | It needs a short one: a problem, a first version, and non-goals save weeks of drift. |

## References

- [references/interview-guide.md](references/interview-guide.md): question bank by topic, follow-ups, depth calibration, Mode B questions.
- [references/discovery-record.md](references/discovery-record.md): interview record template and the record-to-document mapping.
