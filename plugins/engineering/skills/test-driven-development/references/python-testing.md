# Python testing patterns

Match the project's existing style first. Check versions before using newer features.

## Boundaries with parametrize

```python
import pytest

@pytest.mark.parametrize(
    "score, expected",
    [(549, "rejected"), (550, "manual_review"), (599, "manual_review"), (600, "approved")],
)
def test_score_bands(score, expected):  # F-07 AC-1, AC-2 (BR-4, BR-5)
    assert decide(score=score).status == expected
```

`unittest` equivalent: `with self.subTest(score=score): ...`.

## Time

Inject a clock (a parameter or a small `Clock` dependency) in domain code; it keeps tests simple and avoids patching. When patching is unavoidable, use the library the project already has (`freezegun`, `time-machine`), and always state the time zone:

```python
from datetime import datetime, timezone

def test_offer_expires_after_24h():
    created = datetime(2026, 11, 7, 16, 59, tzinfo=timezone.utc)
    offer = Offer(created_at=created)
    assert offer.is_expired(now=datetime(2026, 11, 8, 17, 0, tzinfo=timezone.utc))
```

## Builders and factories

Prefer builders with sensible defaults over large literals (`build_application(score=600)`). If the project uses `factory_boy` or model bakery, use it; don't add a second one. Test data is synthetic: never real personal data.

## Django

- `django.test.TestCase` wraps each test in a transaction (fast; rolled back). `TransactionTestCase` truncates tables instead: use it only when testing transaction behavior (`on_commit`, `select_for_update` across connections).
- pytest-django: the `db` fixture for transactional-rollback access, `transactional_db` for real commits; `django_assert_num_queries` to pin query counts (catches N+1).
- `self.captureOnCommitCallbacks(execute=True)` (Django 3.2+) to run `transaction.on_commit` hooks inside `TestCase`.
- Test against the same database engine as production where behavior differs (MySQL collation, strictness, locking). SQLite can hide MySQL-specific bugs.

## FastAPI

```python
from fastapi.testclient import TestClient

def test_eligibility_endpoint(app, override_bureau):
    app.dependency_overrides[get_bureau_client] = lambda: override_bureau
    client = TestClient(app)
    resp = client.post("/v1/eligibility", json={"application_ref": "app-1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
```

Override dependencies through `app.dependency_overrides` and clear them after the test. For async code paths that need a real event loop, use the async client the project already uses (`httpx.AsyncClient` with an ASGI transport, plus `pytest-asyncio` or `anyio`).

## Asserting logs and events

```python
def test_completion_event(caplog):
    caplog.set_level("INFO")
    decide(score=600, request_id="req-1")
    rec = next(r for r in caplog.records if r.getMessage() == "eligibility_evaluation_completed")
    assert rec.request_id == "req-1" and rec.status == "approved"
```

Assert on fields, not formatted strings.

## Characterization tests

```python
def test_legacy_fee_rounding_characterization():
    # Pins current behavior before refactor; not an endorsement. See T-9.
    assert legacy_fee(Decimal("10.005")) == Decimal("10.00")
```

Mark them clearly so a later behavior change updates them deliberately.

## Running

- One test: `pytest path/to/test_file.py::test_name -q`
- Stop at first failure with short tracebacks: `pytest -x --tb=short -q`
- Django runner: `python manage.py test app.tests.test_module`
