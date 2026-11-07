# Discovering a project's logging stack

Do this before adding any log call. The aim is to reuse what exists, not to introduce a second logging style.

## 1. Find the library and entry points

```bash
grep -rnE "^\s*(import logging|from logging|import structlog|from structlog|from loguru)" --include=*.py . | head -50
grep -rnE "getLogger\(|get_logger\(|structlog\.get_logger|logger\s*=\s*" --include=*.py . | head -50
grep -rnE "LOGGING\s*=|dictConfig\(|fileConfig\(|basicConfig\(" --include=*.py --include=*.ini --include=*.yaml --include=*.yml --include=*.toml . | head
```

| Finding | Meaning |
|---|---|
| `logging.getLogger(__name__)` everywhere | stdlib logging; context comes from `extra=`, filters, or adapters |
| `structlog.get_logger()` + `structlog.configure(...)` | structured key/value calls; check the processor chain |
| `from loguru import logger` | loguru; context via `bind()`; JSON via `serialize=True` |
| `from <project>.logging import get_logger` (or similar) | **internal wrapper**: read it (step 3) |
| Django `LOGGING = {...}` in settings | dictConfig: read `formatters`, `filters`, `handlers`, `loggers` |
| `uvicorn` / `gunicorn` config | the server may already emit access logs per request |

## 2. Read the configuration

- **Formatter.** Does it produce JSON or key/value (e.g. a JSON formatter class, `structlog.processors.JSONRenderer`, `structlog.stdlib.ProcessorFormatter`)? With a plain `logging.Formatter("%(levelname)s %(message)s")`, fields passed via `extra=` are **not printed**: they exist on the record but the format string never references them.
- **Filters.** Look for filters that add `request_id` or similar to every record (often fed by middleware through a thread-local or `contextvars`).
- **Handlers and destination.** stdout (container log collector), files, a cloud log agent. Note which platform parses the output, if documented.
- **Levels per logger.** Which loggers are at DEBUG or WARNING in production settings.

## 3. If there is an internal wrapper, read it

Open the module that defines the wrapper and answer:

| Question | Why it matters |
|---|---|
| What is the exact signature of each method you plan to call? | Calling a non-existent method or keyword fails at runtime, or is silently ignored |
| Does it accept keyword context, an `extra` dict, or a positional dict? | Determines the call shape |
| Does it add context automatically (service name, request id)? | Avoid duplicating fields |
| Does it redact or truncate anything? | Don't assume it does; verify |
| How does it render output? | Run it once in a test or REPL and look |

Then read two or three real call sites and copy their shape. If the wrapper's behavior is unclear after reading it, ask. Don't guess.

## 4. Find how correlation context reaches logs

```bash
grep -rniE "request_id|correlation_id|trace_id|x-request-id|contextvars|threading\.local|LoggerAdapter|bind_contextvars|bind\(" --include=*.py . | head -40
```

Typical mechanisms: middleware sets a contextvar or thread-local, and a logging filter copies it onto each record; a `LoggerAdapter` or bound structlog logger carries it; tracing instrumentation (e.g. OpenTelemetry logging integration) injects `trace_id`/`span_id`. Record which one the project uses. If none exists, that is an escalation (see the skill), not something to improvise per call site.

## 5. Write down the conventions you found

In a Software Factory project, add or update a short *Logging conventions* subsection in `engineering/DEVELOPMENT_GUIDE.md` (library, how to get a logger, event naming, standard fields, how context is attached). Changing an existing convention is a proposal for the owner, not a silent edit.
