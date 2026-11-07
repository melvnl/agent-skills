---
name: performance-engineering
description: Improves backend latency, throughput and resource use by measurement: a target from the NFR, reproduction under realistic data and load, profiling to find the real bottleneck (queries, external calls, CPU, serialization, locks, pool saturation), the highest-leverage fix, and before/after evidence under the same conditions. Use when something is slow, before optimizing, when sizing capacity, or when an NFR target is at risk.
---

# Performance Engineering

## Overview

Performance work without measurement optimizes the wrong thing. Slowness in backend services is usually a handful of causes (queries, N+1, remote calls, saturated pools, lock contention), and intuition about which one is often wrong. This skill establishes a target, measures where time actually goes, fixes the dominant cost, and proves the improvement with numbers taken the same way before and after.

## When to use

- "X is slow", latency or throughput regressions, timeouts under load.
- An NFR target (p95, throughput, batch window) needs to be met or verified.
- Capacity planning: pool sizes, worker counts, instance counts.

**When not to use:** the issue is incorrect behavior, not speed → `debugging-and-error-recovery`. Query-plan details → `mysql-engineering` (used from here).

## Inputs and context

1. **The target**: the NFR or SLO (e.g. p95 < 300 ms at 50 rps), or, if none exists, the owner's agreed goal. "Faster" isn't a target.
2. **Current measurements**: production latency percentiles and throughput (metrics, APM traces), not single local timings.
3. A reproduction environment with **realistic data volume** and the same engine versions; load tools the team uses (Locust, k6, wrk).
4. Profiling tools available: APM, `cProfile`/`pyinstrument` locally, `py-spy` for sampling a running process, database slow-query logs and `EXPLAIN`.

## Process

1. **State the target and the gap** in percentiles: "p95 is 1.2 s, target 300 ms". Averages hide the tail.
2. **Reproduce** with realistic data and load. Many problems (N+1, missing indexes, lock contention) only appear at production volume or concurrency.
3. **Find where the time goes**, top-down: a trace of a slow request (time in DB, external calls, application code); then a profile of the dominant part. Count queries per request; check pool wait time; look at lock waits.
4. **Classify the bottleneck** and apply the matching fix, highest leverage first:

   | Bottleneck | Typical fix |
   |---|---|
   | N+1 or excess queries | eager loading, batching (`django-engineering`) |
   | Slow query | index or rewrite verified with `EXPLAIN` (`mysql-engineering`) |
   | Remote call latency | parallelize independent calls, tighter timeouts, cache stable responses, move off the request path to a queue |
   | Pool saturation (DB, HTTP, threads) | right-size by Little's law, fix leaks and long holds before adding capacity |
   | Lock contention | shorter transactions, narrower locks, atomic updates |
   | CPU in Python | algorithmic change first; vectorize or move heavy work out of the request; processes for parallel CPU work |
   | Serialization | serialize less (fields, pagination), faster serializer only after measuring |
   | Memory / GC | stream instead of loading whole results (`iterator()`), smaller objects |

5. **Size capacity with Little's law**: concurrency in use ≈ throughput × latency (50 rps × 0.2 s ≈ 10 concurrent requests). Size pools and workers for the target load with headroom, and remember every worker multiplies connections against the database's limits.
6. **Cache last**, and only with a freshness requirement and an invalidation plan (`redis-engineering`). A cache in front of a slow query hides the query and adds consistency risk.
7. **Change one thing at a time**, and re-measure under identical conditions (same data, load profile, warm-up, duration). Keep the measurement script so the result can be reproduced.
8. **Guard against regression**: query-count assertions in tests for hot endpoints, a benchmark or load test in CI or before releases where the NFR is critical, latency alerts (`observability-engineering`).

## Output

A performance report:

```markdown
### Performance: GET /v1/applications
- Target: p95 < 300 ms at 50 rps (NFR-4)
- Before: p95 1.2 s, p99 2.9 s; 103 queries/request (staging, 2M rows, k6 5 min, 50 rps)
- Cause: N+1 on applicant + bureau_summary in the serializer (trace + query log)
- Fix: select_related + prefetch; query count pinned at 4 in test
- After: p95 180 ms, p99 410 ms, 4 queries/request (same setup)
- Not done: caching (not needed to meet target)
```

## Verification

- [ ] Before and after numbers use the same data, load, and method, as percentiles.
- [ ] The bottleneck was identified by measurement (trace, profile, query log), not assumed.
- [ ] The target is met, or the remaining gap and next candidate are stated.
- [ ] Correctness is unchanged: the full test suite passes.
- [ ] A regression guard exists for the fixed path.

## Escalation

Ask when: no target exists (it's a product decision); meeting the target needs infrastructure changes, new caches, or architectural change (moving work async changes behavior); or a fix trades consistency or freshness for speed.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Obviously it's the JSON serialization." | Measure. It is usually the database. |
| "Add a cache." | Now you have a slow query, a cache, and an invalidation problem. |
| "It was faster on my laptop after the change." | One request, warm cache, 100 rows. Same conditions, percentiles, or it didn't happen. |
