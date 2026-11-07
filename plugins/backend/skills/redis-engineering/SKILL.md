---
name: redis-engineering
description: Uses Redis safely for caching, rate limiting, short-lived locks and idempotency markers: cache-aside with TTLs and invalidation after commit, stampede protection, key design, memory and eviction awareness, atomic operations, correct lock release, and graceful degradation when Redis fails. Use when adding or changing Redis usage, caches, rate limits or locks.
---

# Redis Engineering

## Overview

Redis is fast and simple to start using, which is why it ends up holding things it can't guarantee. Typical failures: stale or poisoned caches, stampedes when a hot key expires, locks released by the wrong holder, memory exhaustion evicting data someone relied on, and outages when "just a cache" goes down. This skill uses Redis for what it is good at, with explicit expiry, atomicity, and a plan for when it is unavailable.

## When to use

- Adding or changing a cache, rate limiter, lock, idempotency marker, session, or counter in Redis.
- Diagnosing stale data, cache stampedes, memory pressure, evictions, or Redis latency.

**When not to use:** durable job queues and inter-service messaging → `async-messaging` (SQS/SNS). Records of decisions or money → the database.

## Inputs and context

1. Deployment: standalone, replicated, Cluster, or managed (ElastiCache, MemoryDB); version; persistence settings; `maxmemory` and `maxmemory-policy`.
2. The client library and its configuration: timeouts, connection pool, retry behavior.
3. Existing key naming conventions, serialization format, and TTL policies.
4. What reads and writes the underlying data, and how fresh the cached view must be (from the spec).

## Process

1. **Decide whether Redis is the right home.** Redis may lose acknowledged writes on failover (asynchronous replication) and evicts under memory pressure with eviction policies. Use it for derivable, expirable data: caches, rate limits, short-lived coordination. Never as the only copy of decisions, balances, or audit records.
2. **Cache-aside by default**: read cache → on miss, read source → set with a TTL. **Every key has a TTL**, with jitter (e.g. ±10%) so related keys don't expire together.
3. **Invalidate on write, after commit**: delete (don't update) the cached key once the database transaction commits (`transaction.on_commit` in Django). Updating the cache from the write path races with concurrent readers repopulating old values.
4. **Prevent stampedes on hot keys**: single-flight recomputation (a short `SET NX` lock so one worker refreshes while others serve stale or wait briefly), or early probabilistic refresh. Don't let thousands of requests recompute the same expired value.
5. **Design keys**: `<service>:<entity>:<version>:<id>` (`elig:decision:v2:app-123`). The version segment lets you invalidate everything after a format change by bumping it. Avoid personal data in key names (keys show up in monitoring and `SCAN` output).
6. **Serialize safely**: JSON (or the project's format) with a schema version. Never `pickle` data that anything untrusted could write: unpickling executes code.
7. **Keep commands bounded**: no `KEYS` in production (use `SCAN`); avoid unbounded `HGETALL`/`SMEMBERS`/`LRANGE 0 -1` on big collections; watch for big keys (MBs) and hot keys; pipeline batched commands.
8. **Use atomic operations** for counters and conditional updates: `INCR`, `SET key val NX EX ttl`, `MULTI/EXEC`, or a Lua script. A read-then-write from the client isn't atomic.
9. **Locks are short-lived and best-effort.** Acquire with `SET lock:<name> <unique-token> NX PX <ttl>`; release with a Lua compare-and-delete that checks the token, so you never delete another holder's lock; keep work shorter than the TTL. A Redis lock is not a correctness guarantee across failover or long pauses: for anything financial, the database (unique constraints, row locks, conditional updates) must still prevent double execution.
10. **Rate limits atomically**: fixed window with `INCR` plus `EXPIRE` set only when the key is new (or a Lua script); sliding window with a sorted set. Return `429` with `Retry-After` per `api-design`.
11. **In Redis Cluster**, multi-key commands and scripts must touch keys in the same hash slot; use hash tags (`elig:{app-123}:decision`) deliberately.
12. **Degrade gracefully.** Set client timeouts (tens of milliseconds for cache reads). If Redis is down, a cache read falls back to the source with protection (a circuit breaker or concurrency limit), so the database isn't flattened. Decide per use whether a rate limiter fails open or closed, and document it.
13. **Observe**: hit ratio, latency, evictions, memory, connection errors (`observability-engineering`).

## Output

The Redis usage with key schema, TTLs, invalidation points, failure behavior, and a short design note:

```markdown
| Key | Purpose | TTL | Invalidated by | On Redis failure |
|---|---|---|---|---|
| elig:decision:v2:{app_ref} | cache decision view | 10 min ±10% | decision written (on_commit delete) | read DB (concurrency-limited) |
| rl:bureau:{client_id}:{minute} | bureau call rate limit | 70 s | expiry | fail closed (protect quota) |
```

## Verification

- [ ] Every key written has a TTL; TTLs are jittered for bulk-populated keys.
- [ ] Invalidation happens after commit; a test covers read-after-write freshness.
- [ ] No `KEYS`, unbounded collection reads, or `pickle` of untrusted data.
- [ ] Lock release checks the owner token; critical operations are also protected by database constraints.
- [ ] Client timeouts are set; behavior with Redis unavailable is tested or explicitly documented.
- [ ] Cluster key-slot constraints respected for multi-key operations.

## Escalation

Ask when: Redis would hold data with no other source of truth; a change needs a different eviction policy, persistence mode, or capacity; or rate limiter fail-open/closed affects money or abuse protection.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "No TTL; we invalidate on write." | Some write path will forget. TTLs bound the damage. |
| "The Redis lock prevents double processing." | Until a failover or a GC pause outlives the TTL. Back it with a database constraint. |
| "Update the cache when we write the DB." | Concurrent readers can repopulate the old value after your update. Delete after commit. |
