# backend-engineering

Role agents for backend work. The plugin ships no backend skills: with-and-without evals showed Claude already applies API, database, migration, concurrency, caching, messaging and resilience practice without them. Put the project facts that change the right answer (deploy strategy, engine and version, broker, concurrency model) in the project's `CLAUDE.md` instead.

Depends on `spec-driven-engineering` and `observability` (installed automatically).

## Agents

- **[backend-engineer](agents/backend-engineer.md)**: Implements one approved task at a time test-first, instrumented, within scope; reports verified results; never approves its own work.
- **[database-engineer](agents/database-engineer.md)**: Schema changes, deploy-compatible migrations, resumable backfills and EXPLAIN-verified queries with rehearsal evidence; never touches production.
