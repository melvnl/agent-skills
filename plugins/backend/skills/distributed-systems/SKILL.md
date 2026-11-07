---
name: distributed-systems
description: Designs service interactions that survive partial failure: timeouts and deadlines, bounded retries with backoff and jitter, idempotency, unknown-outcome handling, the transactional outbox instead of dual writes, sagas with compensation, circuit breakers, bulkheads and backpressure, and ordering without trusting clocks. Use when a change calls another service, coordinates state across services, or migrates logic between services.
---

# Distributed Systems

## Overview

In a distributed system, every remote call can succeed, fail, or **time out with an unknown outcome**, and every message can arrive late, twice, or out of order. Code written as if calls were local produces duplicate charges, lost updates, and services that collapse when one dependency slows down. This skill applies the small set of patterns that make cross-service behavior correct and resilient.

## When to use

- A change adds or modifies a call to another service or external API.
- State must stay consistent across a database and a message broker, or across services.
- A dependency's slowness or failure is causing cascading failures.
- Logic moves between services (a service migration needing behavioral parity).

**When not to use:** message broker mechanics (SQS/SNS settings, DLQs, consumers) → `async-messaging`. HTTP contract shape → `api-design`.

## Inputs and context

1. The interaction: caller, callee, sync or async, the data that must stay consistent, and what each failure means for the user.
2. Each dependency's SLOs or observed latency (p50/p99), rate limits, and whether its operations are idempotent (or accept idempotency keys).
3. Existing resilience utilities in the codebase (retry decorators, circuit breakers, outbox tables). Reuse them.
4. The business consequence of duplicates vs omissions for this operation (a duplicate notification vs a duplicate decision are very different).

## Process

1. **Set a timeout on every remote call**, derived from the caller's own budget: if the endpoint must answer in 800 ms, a dependency can't take 2 s. Propagate deadlines downstream where the stack supports it.
2. **Retry only what is safe and worth it**: idempotent operations (or ones made idempotent with keys), on transient errors (timeouts, 429 with `Retry-After`, 503, connection resets), with exponential backoff, **jitter**, a small attempt cap, and an overall retry budget. Never retry validation errors or 4xx business rejections. Retries at several layers multiply (3 × 3 × 3 = 27 calls): retry at one layer.
3. **Handle the unknown outcome explicitly.** A timeout on a write means "maybe happened". Either retry with the same idempotency key, or query the dependency's state, or record the operation as *pending verification* and reconcile. Never assume failure and redo a non-idempotent action.
4. **Make consumers and handlers idempotent.** Delivery is at least once; "exactly once" is achieved as *effectively once* by deduplicating on a business key or message id with a unique constraint ([references/resilience-patterns.md](references/resilience-patterns.md)).
5. **Never dual-write** (update the database, then publish, as two independent steps): a crash between them loses or invents events. Use the **transactional outbox**: write the event to an outbox table in the same transaction as the state change, and publish it from a relay that retries until acknowledged. In Django, `on_commit` publishing is simpler but can still lose the event if the process dies after commit; use the outbox where losing an event is unacceptable.
6. **Coordinate multi-service changes with sagas**, not distributed transactions: a sequence of local transactions, each with a compensating action, and an explicit state machine recording progress. Compensations must be idempotent too.
7. **Contain failure**: circuit breakers around flaky dependencies (fail fast, serve a fallback, probe for recovery); bulkheads (separate pools or concurrency limits per dependency, so one slow dependency can't consume every worker); load shedding and backpressure (bounded queues, 429/503 when saturated) instead of unbounded buffering.
8. **Define fallbacks deliberately.** A fallback is a business decision (a default decision, cached data, "try again later"), recorded, logged at WARNING, and visible in metrics. For credit or eligibility decisions, the fallback policy must be specified by the owner (`credit-scoring-and-eligibility`).
9. **Don't order by wall clocks across machines.** Clocks skew. Use sequence numbers, versions, or the database's ordering; make consumers tolerate out-of-order arrival (compare versions, ignore older).
10. **Migrate logic between services with parity checks**: run old and new side by side (shadow or dual-run), compare outputs on real traffic, switch with a flag, and keep rollback possible until parity is proven.
11. **Instrument every interaction**: dependency latency, errors, retries, breaker state, fallback count (`observability-engineering`), with correlation propagated (`distributed-tracing-and-correlation`).

## Output

An interaction design note per dependency:

```markdown
| Dependency | Timeout | Retries | Idempotency | Unknown outcome | Breaker / limit | Fallback |
|---|---|---|---|---|---|---|
| credit bureau | 1.5 s | 2, backoff 200 ms + jitter, on timeout/503 | request key per application | query by request key before retry | breaker 50% / 30 s; max 20 concurrent | owner-defined fallback decision (BR-11) |
| decision events | n/a | outbox relay, unlimited with backoff | event id | relay retries until ack | none | none: must not be lost |
```

## Verification

- [ ] Every remote call has a timeout within the caller's budget.
- [ ] Retries exist at one layer only, are bounded, jittered, and wrap only safe operations.
- [ ] Timeout-on-write paths have a defined unknown-outcome strategy, tested with a stub that times out after applying the write.
- [ ] Consumers are idempotent: a duplicate-delivery test passes.
- [ ] No dual writes for events that must not be lost (outbox in place, or the risk explicitly accepted by the owner).
- [ ] Fallbacks are specified, logged, and counted.
- [ ] Out-of-order and duplicate inputs are tolerated where ordering matters.

## Escalation

Ask when: a fallback changes a business outcome (decisions, limits, money); consistency requirements across services aren't specified; a dependency offers no idempotency and the operation isn't naturally idempotent; or a service migration lacks a parity plan.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Retry three times to be safe." | At three layers that is 27 calls during an outage: a self-inflicted DDoS. |
| "Timeout means it failed." | It means you don't know. Redoing a non-idempotent write duplicates it. |
| "Publish right after commit; crashes are rare." | Rare per event, guaranteed at volume. Use the outbox when loss matters. |

## References

- [references/resilience-patterns.md](references/resilience-patterns.md): outbox schema and relay, dedup table, retry policy, breaker parameters, saga state.
