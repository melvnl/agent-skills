---
name: database-design
description: Designs relational schemas from the domain: entities and ownership, keys, constraints that enforce invariants in the database, history and decision snapshots, money and time types, soft-delete and enum trade-offs, and indexes derived from real queries. Use when adding or changing tables, columns, relationships or indexes, or updating the data model documentation.
---

# Database Design

## Overview

Data outlives code. A schema that lets invalid states in, overwrites history, or stores money as floats creates defects no application fix can fully undo. This skill designs schemas where the database enforces the invariants it can, history stays reconstructable, and indexes follow the queries the application actually runs.

## When to use

- New tables, columns, relationships, constraints, or indexes.
- Modeling history, decisions, or audit-relevant data.
- Updating `engineering/DATA_MODEL.md`.

**When not to use:** writing and rolling out the migration → `database-migrations`. MySQL engine behavior (InnoDB, locking, isolation, online DDL) → `mysql-engineering`. ORM mechanics → `django-engineering`.

## Inputs and context

1. The spec and design: entities, lifecycle states, business rules, expected volumes and growth, query patterns (filters, sorts, joins), retention.
2. The existing data model (`engineering/DATA_MODEL.md`, models, migrations): naming conventions, key types, timestamp and money conventions, soft-delete usage, tenancy.
3. The database engine and version (constraint support differs; MySQL enforces `CHECK` only from 8.0.16).
4. Data classification for each new column (`logging-security-and-redaction` tiers).

## Process

1. **Model the domain first**: entities, relationships with cardinality, the owner of each record (user, tenant, system), and lifecycle states with allowed transitions. Write invariants in plain language ("an application has at most one active decision").
2. **Choose keys**:
   - Surrogate primary keys by default; natural keys get a `UNIQUE` constraint.
   - For clustered-index engines (InnoDB), random UUIDv4 primary keys scatter inserts and fragment the index; prefer an auto-increment key internally with an opaque public id, or a time-ordered id (UUIDv7, ULID). Store UUIDs compactly (`BINARY(16)`) when volume matters, and follow the existing convention otherwise.
   - Never expose sequential internal ids where enumeration is a risk; use opaque public ids.
3. **Enforce invariants in the database** where possible: `NOT NULL`, foreign keys, `UNIQUE` (including composite natural keys and "one active row" rules, implemented per engine), `CHECK` where enforced. Application validation is additional, not a substitute: concurrent writers and other code paths bypass it.
4. **Type values exactly**: money `DECIMAL(p, s)` with currency (`money-and-decimal-arithmetic`); instants in UTC (`DATETIME(6)` in MySQL to avoid `TIMESTAMP`'s 2038 limit and session time-zone conversion, unless the project's convention differs); local dates as `DATE` with the zone documented; units in column names (`duration_ms`, `amount_idr`).
5. **Keep history stable.** Records of past events snapshot the values they depended on: a decision stores its inputs, score, rule version, and outcome, rather than joining to mutable current data. Use append-only history tables or effective-dated rows (`valid_from`, `valid_to`) for data whose past values matter (`financial-auditability`).
6. **Decide soft delete deliberately.** It complicates unique constraints (deleted rows still collide), every query (filters), and privacy deletion. Prefer hard delete plus a history or audit record unless recovery or reference requirements demand soft delete.
7. **Choose enum storage**: a lookup table when values carry attributes or change often; a constrained `VARCHAR` (with `CHECK`, or validated in code) for small, stable sets; avoid engine `ENUM` types where reordering or adding values requires table rebuilds or locks.
8. **Use JSON columns only for genuinely schemaless, rarely filtered data** (e.g. a raw vendor payload snapshot). Anything you filter, join, or constrain gets real columns.
9. **Derive indexes from queries.** For each query pattern: equality columns first, then the range or sort column, in a composite index whose left prefix serves the most queries; consider covering indexes for hot reads. Every index costs write time and storage, so don't index speculatively (`mysql-engineering` for verification with `EXPLAIN`).
10. **Plan size and retention**: row growth per day, archival or purge strategy, partitioning only with evidence of need.
11. **Minimize personal data**: store only what the spec needs; mark sensitive columns in the data model; plan deletion.
12. **Update `engineering/DATA_MODEL.md`** (entities, fields with types and units, ownership, invariants, indexes, retention) in the same change.

## Output

A schema change description (DDL or model changes) plus the `DATA_MODEL.md` update: entities, fields, keys, constraints, indexes with the queries they serve, history strategy, classification of sensitive columns, retention.

## Verification

- [ ] Every invariant is enforced by a constraint or documented as application-enforced with the reason.
- [ ] Money and time columns use exact and UTC conventions.
- [ ] Records representing past events don't depend on mutable reference data.
- [ ] Each index maps to a named query; no duplicate or left-prefix-redundant indexes.
- [ ] Sensitive columns are classified; retention is stated.
- [ ] `DATA_MODEL.md` updated.

## Escalation

Ask when: the change alters ownership, tenancy, or isolation; personal or financial data is added; a key-type or convention change is implied; history semantics are unclear (what must be reconstructable, and for how long); or volume forces partitioning or archival decisions.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "The app validates it, so no constraint needed." | Concurrent requests, scripts and other services don't go through that validation. |
| "Join to the current rule table to explain old decisions." | The rule changed last month; the explanation is now wrong. Snapshot. |
| "Add an index on every column we filter by." | Write amplification and memory pressure. Index the query patterns, composite where needed. |
