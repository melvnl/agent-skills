---
name: performance-engineering
description: Improves backend and web frontend performance by measurement on any stack: a target (p95 latency, throughput, Core Web Vitals), reproduction under realistic data, load and devices, profiling to the real bottleneck (queries, remote calls, pools, locks, CPU, bundle size, render and hydration cost), the highest-leverage fix, and same-conditions before/after evidence. Use when a service or page is slow, before optimizing, or when sizing capacity.
---

# Performance Engineering

## Overview

Performance work without measurement optimizes the wrong thing. Slowness usually comes from a handful of causes (on the server: queries, N+1, remote calls, saturated pools, lock contention; in the browser: render-blocking resources, oversized JavaScript, slow server responses, layout shifts, long main-thread tasks), and intuition about which one is often wrong. This skill sets a target, measures where time actually goes, fixes the dominant cost, and proves the improvement with numbers taken the same way before and after.

## When to use

- "X is slow": an endpoint, a job, a page, an interaction. Latency or throughput regressions, timeouts under load.
- A target needs to be met or verified: an NFR or SLO (p95, throughput, batch window) or Core Web Vitals (LCP, INP, CLS).
- Capacity planning: pool sizes, worker counts, instance counts.

**When not to use:** the issue is incorrect behavior, not speed → `debugging-and-error-recovery`. Query plans and locking once the database is the proven bottleneck → `database-queries-and-concurrency`. Cache design → `caching-and-coordination`.

## Inputs and context

1. **The target**: the NFR or SLO (p95 < 300 ms at 50 rps), or Core Web Vitals at the 75th percentile of real users (LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1), or the owner's agreed goal. "Faster" isn't a target.
2. **Current field measurements**: production latency percentiles and throughput (metrics, APM traces); for pages, real-user data (RUM, CrUX, the framework's web-vitals reporting). Single local timings and one Lighthouse run are not the baseline.
3. A reproduction environment with **realistic data volume**, the same engine and runtime versions, and the team's load tool (k6, Locust, autocannon, wrk); for pages, a throttled mid-range device profile.
4. Profilers available for the runtime: APM traces; language profilers (`py-spy`/`pyinstrument`, `node --cpu-prof`/clinic.js/`0x`, pprof, async-profiler); database slow-query logs and `EXPLAIN`; browser DevTools Performance panel, Lighthouse, bundle analyzers.

## Process

1. **State the target and the gap** in percentiles: "p95 is 1.2 s, target 300 ms"; "LCP p75 is 4.1 s on mobile, target 2.5 s". Averages hide the tail.
2. **Reproduce** with realistic data, load, and devices. N+1, missing indexes and lock contention appear only at production volume; frontend problems appear only on throttled CPU and network.
3. **Find where the time goes**, top-down. For a request: a trace of a slow request (database, remote calls, application code), then a profile of the dominant part; count queries; check pool wait time and lock waits. For a page: break LCP into server response (TTFB), resource load delay, load duration and render delay; for INP, find the long tasks behind the slow interaction; for CLS, the shifting elements. Read [references/web-frontend.md](references/web-frontend.md) for page work.
4. **Classify the bottleneck** and apply the matching fix, highest leverage first:

   | Bottleneck | Typical fix |
   |---|---|
   | N+1 or excess queries | eager loading, batching, query-count test (`database-queries-and-concurrency`) |
   | Slow query | index or rewrite verified with `EXPLAIN` (`database-queries-and-concurrency`) |
   | Remote call latency | parallelize independent calls, tighter timeouts, cache stable responses, move off the request path to a queue |
   | Pool saturation (DB, HTTP, threads, workers) | right-size by Little's law; fix leaks and long holds before adding capacity |
   | Lock contention | shorter transactions, narrower locks, atomic updates |
   | Blocked event loop (Node, asyncio) | move CPU work or sync I/O off the loop (worker threads, executors, queues) |
   | CPU in application code | algorithmic change first; move heavy work off the request path; parallel processes for CPU work |
   | Serialization | serialize less (fields, pagination) before a faster serializer |
   | Slow TTFB on pages | the backend rows above, then static or cached rendering where data allows |
   | Heavy JavaScript / hydration | ship less: server-render static parts, split by route and interaction, drop or defer dependencies |
   | Late LCP resource | discoverable in the HTML, prioritized, correctly sized and formatted |
   | Layout shift | reserved dimensions for media, ads and late content; font fallback metrics |

5. **Size capacity with Little's law**: concurrency in use ≈ throughput × latency (50 rps × 0.2 s ≈ 10 concurrent requests). Size pools and workers for the target load with headroom; every worker multiplies connections against the database's limit.
6. **Cache last**, and only with a freshness requirement and an invalidation plan (`caching-and-coordination`). A cache in front of a slow query hides the query and adds consistency risk.
7. **Change one thing at a time**, and re-measure under identical conditions (same data, load profile or device profile, warm-up, duration). Keep the measurement script so the result can be reproduced.
8. **Guard against regression**: query-count assertions for hot endpoints; a load test before releases where the NFR is critical; bundle-size or Lighthouse budgets in CI for key pages; latency and web-vitals alerts (`observability-engineering`).

## Output

A performance report:

```markdown
### Performance: GET /store/products (and /products page)
- Target: p95 < 300 ms at 50 rps; LCP p75 ≤ 2.5 s mobile
- Before: p95 1.2 s, 103 queries/request (staging, 2M rows, k6 5 min); LCP p75 4.1 s (RUM, 7 days)
- Cause: N+1 on variants + prices (trace + query log); hero image lazy-loaded and unsized (LCP breakdown: 2.2 s load delay)
- Fix: eager-load relations, query count pinned at 4; hero image eager, prioritized, responsive sizes
- After: p95 180 ms, 4 queries/request (same setup); lab LCP 2.1 s (same device profile); field LCP to re-check after 7 days
- Not done: caching (not needed to meet target)
```

## Verification

- [ ] Before and after numbers use the same data, load or device profile, and method, as percentiles.
- [ ] The bottleneck was identified by measurement (trace, profile, query log, performance trace), not assumed.
- [ ] The target is met, or the remaining gap and next candidate are stated; frontend wins are re-checked in field data when available.
- [ ] Correctness is unchanged: the full test suite passes.
- [ ] A regression guard exists for the fixed path.

## Escalation

Ask when: no target exists (it's a product decision); meeting the target needs infrastructure changes, new caches, or architectural change (moving work async, changing rendering strategy changes behavior); or a fix trades consistency, freshness or features for speed.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Obviously it's the JSON serialization." | Measure. It is usually the database. |
| "Add a cache." | Now you have a slow query, a cache, and an invalidation problem. |
| "Lighthouse says 98." | On a fast laptop, once. Users are on mid-range phones; check field data. |
| "It was faster after the change." | One request, warm cache, 100 rows. Same conditions, percentiles, or it didn't happen. |

## References

- [references/web-frontend.md](references/web-frontend.md): read for page and interaction performance: Core Web Vitals diagnosis, JavaScript and hydration cost, images and fonts, server-rendering frameworks such as Next.js.
