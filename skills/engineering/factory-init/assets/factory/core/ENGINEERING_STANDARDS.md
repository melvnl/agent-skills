# Engineering Standards

> **Scope:** Project-agnostic. Each project declares its concrete technology stack in its own documentation (conventionally `engineering/TECH_STACK.md`). This file defines *how* to build, not *what* to build with.

---

## 1. Architecture principles

| Standard | Rule |
|---|---|
| Default topology | Start as a **modular monolith**: one deployable, internally split into modules with explicit boundaries. Split into services only with an ADR showing a concrete need (independent scaling, independent deployment cadence, team ownership, isolation). |
| Module boundaries | Modules are organized by **feature/domain**, not by technical layer. A module exposes a small public surface (an `index` file or equivalent); other modules do not import its internals. |
| Dependency direction | `UI / transport → application services → domain ← infrastructure adapters`. Domain code depends on nothing outside itself. |
| Dependency inversion | Where infrastructure is expected to change (storage, external providers), domain/application code depends on an interface ("port") the infrastructure implements ("adapter"). Do not create ports for things that will not change. |
| Shared code | Only genuinely cross-cutting utilities go in a shared module. "Shared" is not a dumping ground; if only one module uses it, it lives in that module. |

## 2. Separation of business logic and infrastructure

- Business rules (calculations, validations, state transitions, policies) live in **pure functions or plain classes** with no I/O.
- Request handlers, UI components, and jobs are **thin**: parse input → call an application service → map the result to output.
- Infrastructure adapters (database repositories, HTTP clients, storage, AI/ML providers) contain no business decisions.
- **Test of compliance:** core business logic can be unit-tested without a database, network, browser, or framework runtime.

## 3. API and contract design

Applies to HTTP APIs, RPC, internal service interfaces, events, and client/server data contracts.

- **Explicit schemas** for every request, response, and event, validated at runtime at trust boundaries (incoming requests, external API responses, data read from untrusted storage).
- **Contracts are documented before implementation** (conventionally in `engineering/API_CONTRACTS.md` or an OpenAPI/schema file).
- **Consistent error shape** across the contract (e.g. `{ code, message, details? }`); error `code`s are stable, machine-readable identifiers.
- **Versioning:** public/external APIs are versioned (e.g. `/v1/`). Internal in-process interfaces are not versioned but must be changed atomically with all callers.
- **REST conventions** (when REST is used): resource nouns, standard HTTP verbs and status codes, pagination for unbounded collections, idempotency for retried writes.
- **Do not invent an API layer** where a platform's direct, secured access (e.g. a database with row-level authorization) is simpler and equally safe. Record that choice in an ADR.

## 4. Database and data modeling principles

- **Model the domain first**, then the storage. Document entities, relationships, ownership, and invariants (conventionally `engineering/DATA_MODEL.md`).
- **Every record has a clear owner** (user, tenant, or system). Ownership is a column, not an inference.
- **Identifiers:** prefer globally unique IDs (UUID/ULID) generated where the record is created, so records can move between stores without collisions.
- **Timestamps:** store instants in UTC (ISO 8601 / `timestamptz`). Store the user's local date/timezone separately when business logic depends on "which day" something happened.
- **Units:** every numeric quantity has a documented unit, ideally encoded in the field name (`amount_mg`, `duration_ms`).
- **History stability:** records that represent past events snapshot the values they depend on; editing a reference/definition must not rewrite history.
- **Migrations:** schema changes are forward-only, versioned, reviewed, and reversible-by-follow-up. Destructive migrations (drop/rename/narrow) require explicit human approval and a data backup plan.
- **Derived data** (aggregates, summaries) is computed from source records unless there is measured performance need to store it; if stored, document how it is kept consistent.

## 5. Error handling

- **Classify errors:** *validation* (caller's fault, recoverable, show a specific message), *expected domain failures* (e.g. not found, conflict), *infrastructure failures* (network, storage; maybe retryable), *programming errors* (bugs; fail loudly).
- **Fail fast at boundaries:** validate input at the edge; inside the core, trust validated types.
- **Never swallow errors.** Every `catch` either handles the error meaningfully, adds context and rethrows, or reports it.
- **User-facing errors** are actionable and free of internals (no stack traces, SQL, or secrets).
- **Retries** only for idempotent operations, with bounded attempts and backoff.

## 6. Logging and observability

- **Structured logs** (key/value or JSON) with level, timestamp, event name, and correlation/request ID where applicable.
- **Levels:** `error` = needs attention; `warn` = unexpected but handled; `info` = significant lifecycle events; `debug` = development detail (off in production by default).
- **Never log** secrets, credentials, tokens, full personal records, or sensitive personal data (health, financial, precise location). Log identifiers, not contents.
- **Metrics/tracing** proportional to the system: a local-only app may need only error reporting; a multi-user service needs request metrics and error tracking.
- Each project documents where logs and errors go (console, error tracker, platform logs).

## 7. Security

- **Authentication** is handled by a proven provider or library — never hand-rolled crypto or session schemes.
- **Authorization** is enforced server-side (or at the data layer), never only in the UI. Default deny.
- **Data isolation** between users/tenants is designed explicitly and covered by automated tests that attempt cross-user access.
- **Input** is validated and output is encoded for its context (HTML, SQL, shell, URLs). Use parameterized queries.
- **Secrets** live in environment variables or a secret manager; `.env*` files with real values are git-ignored; an `.env.example` documents required variables with dummy values.
- **Client exposure:** anything shipped to a browser or mobile client is public. Only explicitly public keys go there.
- **Dependencies** are scanned for known vulnerabilities as part of CI where available.
- **Sensitive data** (health, financial, biometric, children's data, precise location) triggers a project-level privacy section documenting collection, storage, retention, and deletion.

## 8. Dependency management

Before adding a dependency, answer in the PR/task description:

1. What problem does it solve that the platform/standard library or an existing dependency does not?
2. Is it actively maintained (recent releases, issue activity) and widely used?
3. What is its size/runtime cost (bundle size for clients)?
4. What is its license, and is it compatible?
5. How hard is it to remove later?

Rules:
- Pin versions via a lockfile; commit the lockfile.
- One library per concern (do not add a second date library, state manager, or HTTP client).
- Upgrade dependencies deliberately, one major upgrade per change, with tests passing.

## 9. Configuration management

- Configuration is read from the environment at startup, validated against a schema, and exposed through a single typed config module. Missing required config fails startup with a clear message.
- No environment-specific `if (prod)` branches scattered in code; behavior differences come from config values.
- Feature flags (if used) have an owner and a removal date.
- Each project documents all configuration variables, their purpose, and whether they are secret/public.

## 10. Backward compatibility

- **Stored data** written by an older version must remain readable by the newer version, or be migrated explicitly.
- **Contracts** consumed by others (APIs, events, client storage schemas, export formats) change in an additive way where possible: add optional fields; do not remove/rename/retype without a deprecation path.
- **Breaking changes** require: an ADR or spec section describing impact, a migration path, and human approval.
- **Client-side persisted data** (browser storage, mobile local DBs) has a schema version and explicit upgrade steps; users must never lose data due to an app update.

## 11. Frontend standards (when applicable)

- Use the type-safe language variant with **strict mode** enabled (e.g. TypeScript `strict: true`).
- Component-based architecture: presentational components receive data via props; data fetching/mutation lives in hooks or services, not scattered in leaf components.
- Accessibility: semantic HTML, keyboard operability, visible focus, labels for inputs, sufficient color contrast (WCAG 2.2 AA as the target).
- Responsive, mobile-first layouts unless the project states otherwise.
- Every data-driven view handles **loading, empty, error, and success** states explicitly.
