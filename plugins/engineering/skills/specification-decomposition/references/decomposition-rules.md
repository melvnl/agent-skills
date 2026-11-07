# Decomposition rules

## Splitting heuristics

Split a candidate feature when any of these is true:

| Signal | Split along |
|---|---|
| Several primary actors with different goals | one feature per actor goal |
| Several lifecycle stages (submit, evaluate, notify) | one feature per stage, ordered by the lifecycle |
| Several external integrations | one per integration, if each is independently testable |
| CRUD + workflow + reporting mixed together | separate the operational flow from reporting |
| Happy path + many exception policies | core flow first; exception policies as follow-on features if independently valuable |
| Phase boundary crosses the feature | the part needed now vs later |
| More than ~10 FRs, or design needs more than one review | by sub-capability |

Don't split when the parts can't be verified independently, or when a split only produces technical layers (an "API feature" and a "database feature"). Slices are vertical.

## Ids

| Id | Scope | Rule |
|---|---|---|
| `FR-n`, `NFR-n`, `BR-n` | project-wide, in `product/PRD.md` | sequential; never renumbered or reused; deprecated ids stay with status *Deprecated* |
| `Q-n` | project-wide open questions | closed with a recorded decision |
| `F-nn` | features in `product/FEATURES.md` | two digits minimum; sequential |
| `<F-ID>-FR-n` | inside a spec | feature-scoped refinement; must cite the PRD id it refines |
| `AC-n` | inside a spec | see `acceptance-criteria-engineering` |
| `T-n` | inside a task breakdown | see `planning-and-task-breakdown` |

## Worked example

Analysis statements (abridged):

- E-4 "Applicants submit an application with identity and income details" (S1 §2.1)
- E-9 "Eligibility is decided automatically using score thresholds" (S1 §4)
- E-10 "Score >= 600 is eligible; 550–599 goes to manual review" (S1 §4.1)
- E-15 "Applicants are notified of the decision by SMS" (S1 §5)
- E-22 "Decisions must be explainable to the applicant on request" (S1 §6.3)

Decomposition:

| Feature | Requirements | Depends on |
|---|---|---|
| F-05 Application intake | FR-11 (E-4) | none |
| F-06 Eligibility rules engine (enabling) | BR-4, BR-5 (E-10) | none |
| F-07 Automatic eligibility decision | FR-12 (E-9), NFR-3 | F-05, F-06 |
| F-08 Manual review queue | FR-13 (E-10 band 550–599) | F-07 |
| F-09 Decision notification | FR-14 (E-15) | F-07 |
| F-10 Decision explanation | FR-15 (E-22) | F-07 |

Note that the inclusivity of "550–599" was confirmed with the owner during analysis (BR-5: 550 ≤ score ≤ 599).
