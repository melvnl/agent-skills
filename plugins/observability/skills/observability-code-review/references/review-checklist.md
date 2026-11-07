# Observability review checklist

Detection hints are starting points for reading code, not verdicts. Confirm every hit in context.

## 1. Missing important signals

- [ ] Each changed endpoint or handler: completion observable with outcome and duration (via middleware, APM, or an explicit event)?
- [ ] Each external call: failure, timeout, and retry observable with `dependency` and `error_code`?
- [ ] Each state transition that matters operationally: `from_state` → `to_state` logged or recorded?
- [ ] Each fallback or degraded path: logged at WARNING?
- [ ] Each consumer or job: start (if long-running), completion, failure, and redelivery visible?

Hints: new `requests.`/`httpx.`/`boto3` calls without a surrounding error log; `except ...: return default` with no log; new Celery tasks with no completion signal.

## 2. Correlation

- [ ] Ingress reads or creates the id; egress injects it; consumers extract and bind it.
- [ ] Executor / thread hand-offs copy context.
- [ ] No new id minted mid-flow.

Hints: `send_message(` without `MessageAttributes`; `receive_message(` without `MessageAttributeNames`; `executor.submit(` in request code; `uuid4()` outside ingress.

## 3. Severity

- [ ] Business rejections are not ERROR.
- [ ] Caller validation errors are not ERROR.
- [ ] Recovered conditions are WARNING, not ERROR.
- [ ] Nothing needed in an incident is DEBUG-only.

## 4. Sensitive data

- [ ] No tier-1 values (tokens, passwords, keys, auth headers, cookies) in any form.
- [ ] No raw tier-2 values (identity numbers, contact details, account numbers, bureau data).
- [ ] No whole objects: `request`, `request.data`, `request.headers`, `.json()`, `vars(x)`, `__dict__`, ORM instances, `%s` of a model.
- [ ] No unsanitized exception text that can echo values.

Hints: `logger.*(.*request`, `extra={.*body`, `f"{.*}"` inside log calls, `str(e)`/`repr(e)` in log args.

## 5. Structure and conciseness

- [ ] Constant message or event name; variable data in fields.
- [ ] Field names match the project's existing names; units in names; numbers as numbers.
- [ ] Messages short; no multi-line payload dumps.
- [ ] stdlib `extra` keys don't collide with `LogRecord` attributes (`message`, `asctime`, `name`, `module`, ...).
- [ ] The formatter actually emits structured fields.

## 6. Error context

- [ ] Exceptions logged once, at the handling layer, with traceback where useful (`logger.exception` inside `except`).
- [ ] Error logs carry `error_code`, operation, and correlation ids.
- [ ] Re-raised exceptions preserve the cause (`raise ... from exc`).

## 7. Volume and cost

- [ ] No INFO+ log per item inside loops over unbounded collections.
- [ ] No per-query success logs.
- [ ] New INFO+ events on hot paths justified by a rate estimate.
- [ ] Sampling, if used, doesn't drop security or audit events.

## 8. Metrics

- [ ] Correct type (counter vs gauge vs histogram); unit stated.
- [ ] Labels bounded: no ids, raw paths, emails, messages.
- [ ] Latency as histograms when percentiles matter.

## 9. Audit vs diagnostics

- [ ] Decisions, permission changes, and financially relevant changes that must be reconstructable are stored as durable records, not only logged.
