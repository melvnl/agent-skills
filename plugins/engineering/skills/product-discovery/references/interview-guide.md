# Interview guide

Pick questions; don't recite them. Each question should build on the previous answer and use the owner's own words. Prefer the question whose answer would change the most downstream.

## Depth calibration (ask once, early)

| Project kind | Interview depth | Must cover |
|---|---|---|
| Personal side project | 6–10 questions | problem, user (often the owner), first version, non-goals, constraints (time, cost) |
| Business or team project | 10–15 questions | all topics below; who approves; success measure the business cares about |
| Regulated or financial (credit, payments, personal data) | 12–18 questions | all topics, plus data classification, auditability, authorization, compliance owner, failure behavior |

## Mode A topics (idea to product)

**Problem and user**
- What problem are you solving, and for whom? Describe the last time this person hit it.
- How do they handle it today (spreadsheet, another tool, a person, nothing)? What does that cost them?
- Why build this now?

**Outcome and success**
- If this works, what changes for that person in the first month?
- How will you know it worked? (a number if possible: signups, hours saved, approvals per day, revenue)

**Core journey**
- Walk me through the one journey that must work in the first version, from start to finish.
- What is the smallest version someone would actually use?

**Scope and non-goals**
- What are you deliberately *not* building in the first version?
- Which ideas are tempting but can wait? (record as Future consideration)

**Rules and data**
- Are there rules the system must apply (limits, thresholds, eligibility, pricing, rounding)? Exact values and edge cases?
- What data will you store about people? Anything sensitive (identity numbers, financial data, location, health)?

**Constraints**
- Time, budget, platform (web, mobile, internal tool), integrations that must exist, technology you want or must avoid.
- Who else must approve or be consulted (business partner, client, compliance)?

**Non-functional needs** (by depth)
- How many users or requests at launch, and in a year? Any latency expectation?
- What happens if it is down for an hour? Who notices?
- Who may see or change what (roles)? Does anything need an audit trail?
- What must operators be able to see when something goes wrong?

**Business context** (business projects only; keep it light)
- Who pays, and for what? Is there a deadline tied to a customer or launch?
- For market, competitor, or pricing research, hand off to marketing or research skills rather than guessing here.

**Risks**
- What is the riskiest assumption here? How could we test it cheaply before building much?

## Mode B topics (request without a PRD, existing project)

- What triggered this request (incident, customer ask, business change, regulation)?
- Who uses it, and what do they do today? (confirm by reading the current code and specs first)
- What should be true after the change that isn't true now? (observable outcome)
- Exact rules: thresholds, inclusivity, units, time zones, rounding.
- Edge cases you already know about: empty, duplicate, concurrent, failure of a dependency.
- Which existing behavior must not change? Which contracts or clients are affected?
- Relevant non-functional needs: latency, volume, security, privacy, audit, observability.
- Rollout: flag, migration, communication, deadline.

## Good follow-ups

| The answer was… | Ask |
|---|---|
| Vague ("fast", "easy", "secure") | "What would be too slow / too hard? Can you give a number or an example?" |
| A solution ("we need a dashboard") | "What decision would someone make from it? What do they do today?" |
| Everything is must-have | "If only one journey works at launch, which one?" |
| "I don't know" | Offer 2–3 options with your recommendation, or record an Open question and what it blocks |
| A contradiction with an earlier answer | Quote both and ask which holds |

## Stop conditions

Stop when the done-test in the skill passes, when the owner asks to stop, or when two consecutive answers add nothing new. Remaining unknowns become Open questions with what they block.
