---
name: caching-and-coordination
description: Uses caches and key-value stores (Redis, Valkey, Memcached, framework caches, CDN and HTTP caches) safely: cache-aside with TTLs, invalidation after commit, stampede protection, key design, atomic counters and rate limits, owner-checked short-lived locks, and graceful degradation when the cache fails. Use when adding or changing a cache, rate limit, lock or idempotency marker.
---

# Caching and Coordination

## Overview

A cache is fast and easy to add, which is why it ends up holding things it can't guarantee. Typical failures: stale or poisoned entries, stampedes when a hot key expires, locks released by the wrong holder, evictions removing data someone relied on, and outages when "just a cache" goes down. This skill applies the same rules whatever the store is: explicit expiry, invalidation after the source of truth commits, atomic operations, and a plan for when the cache is unavailable.

## When to use

- Adding or changing a cache (in-process, Redis-like store, framework data cache, HTTP/CDN cache), rate limiter, lock, idempotency marker, session, or counter.
- Diagnosing stale data, stampedes, memory pressure, evictions, or cache latency.

**When not to use:** durable job queues and inter-service messaging → `async-messaging`. Records of decisions, orders or money → the database. Browser and CDN caching as part of page speed → `performance-engineering` (it applies the freshness rules here).

## Inputs and context

1. The store and deployment: in-process, Redis/Valkey standalone or Cluster, managed service, framework cache layer; version; persistence; memory limit and eviction policy.
2. The client and its configuration: timeouts, pool, retry behavior.
3. Existing key naming, serialization format, and TTL conventions.
4. What writes the underlying data, and how fresh the cached view must be (from the spec). No freshness requirement, no cache.

## Process

1. **Decide whether a cache is the right home.** Replicated key-value stores can lose acknowledged writes on failover and evict under memory pressure. Store derivable, expirable data: caches, rate limits, short-lived coordination. Never the only copy of orders, balances, decisions or audit records.
2. **Cache-aside by default**: read cache → on miss, read source → set with a TTL. **Every key has a TTL**, jittered (±10%) for keys populated together.
3. **Invalidate on write, after commit**: delete (don't update) the cached entry once the database transaction commits, using the framework's after-commit hook or by deleting after the transaction returns. Updating the cache from the write path races with readers repopulating old values.
4. **Prevent stampedes on hot keys**: single-flight recomputation (a short `SET NX` lock or an in-process promise map so one caller refreshes while others wait briefly or serve stale), or early probabilistic refresh.
5. **Design keys**: `<service>:<entity>:<version>:<id>` (`store:product:v3:prod_123`). The version segment invalidates everything after a format change. Include every input that changes the value (region, currency, locale, customer group) or users see each other's prices. Keep personal data out of key names.
6. **Serialize safely**: JSON or the project's format with a schema version. Never deserialize formats that execute code (`pickle`, unsafe YAML, Java serialization) from anything an attacker could write.
7. **Keep commands bounded**: no `KEYS` in production (use `SCAN`); no unbounded collection reads; watch for big and hot keys; pipeline batches.
8. **Use atomic operations** for counters and conditional updates (`INCR`, `SET NX EX`, transactions, server-side scripts). Client-side read-then-write isn't atomic.
9. **Locks are short-lived and best-effort.** Acquire with a unique token and a TTL; release with a compare-and-delete on the token so you never delete another holder's lock; keep work shorter than the TTL. A cache lock is not a correctness guarantee across failover or long pauses: for money or stock, the database (unique constraints, conditional updates, row locks) must still prevent double execution (`database-queries-and-concurrency`).
10. **Rate-limit atomically**: fixed window with `INCR` plus an expiry set only when the key is new; sliding window with a sorted set. Return `429` with `Retry-After` (`api-design`).
11. **Clustered stores**: multi-key commands and scripts must stay in one hash slot; use hash tags (`{order_123}`) deliberately.
12. **Degrade gracefully.** Short client timeouts (tens of milliseconds for cache reads). If the cache is down, reads fall back to the source behind a concurrency limit or breaker so the database isn't flattened. Decide per use whether a rate limiter fails open or closed, and document it.
13. **HTTP and CDN caches follow the same rules**: explicit `Cache-Control` per response class, `private` or `no-store` for anything user-specific (carts, accounts, prices by customer group), a purge or revalidation path for content that changes.
14. **Observe** hit ratio, latency, evictions, memory, and errors (`observability-engineering`).

## Output

The cache usage with key schema, TTLs, invalidation points and failure behavior, recorded as a table:

```markdown
| Key | Purpose | TTL | Invalidated by | On cache failure |
|---|---|---|---|---|
| store:product:v3:{id}:{region} | product page data | 10 min ±10% | product updated (after-commit delete) | read DB, concurrency-limited |
| rl:login:{ip}:{minute} | login rate limit | 70 s | expiry | fail closed |
```

## Verification

- [ ] Every key written has a TTL; bulk-populated keys are jittered.
- [ ] Invalidation happens after commit; a test covers read-after-write freshness.
- [ ] Keys include every input the value depends on; user-specific responses are never shared-cached.
- [ ] No `KEYS`, unbounded reads, or unsafe deserialization of untrusted data.
- [ ] Lock release checks the owner token; critical operations are also protected in the database.
- [ ] Client timeouts are set; behavior with the cache unavailable is tested or documented.

## Escalation

Ask when: the cache would hold data with no other source of truth; a change needs a different eviction policy, persistence mode or capacity; or rate limiter fail-open/closed affects money or abuse protection.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "No TTL; we invalidate on write." | Some write path will forget. TTLs bound the damage. |
| "The lock prevents double processing." | Until a failover or a pause outlives the TTL. Back it with a database constraint. |
| "Update the cache when we write the DB." | Concurrent readers can repopulate the old value. Delete after commit. |
| "Cache the product page for everyone." | Prices vary by region and customer group. The key, or the cache scope, must too. |
