# Django ORM pitfalls

## N+1

```python
# N+1: one query for applications, one per application for applicant
for app in Application.objects.filter(status="pending"):
    print(app.applicant.reference)

# Fixed
for app in Application.objects.filter(status="pending").select_related("applicant"):
    ...

# Reverse / many-to-many
Applicant.objects.prefetch_related("applications")
Applicant.objects.prefetch_related(Prefetch("applications", queryset=Application.objects.filter(status="open")))
```

DRF serializers with nested serializers or `SerializerMethodField` cause N+1 the same way: optimize the viewset's `get_queryset()`.

Pin it in tests:

```python
def test_list_query_count(django_assert_num_queries, api_client, five_applications):
    with django_assert_num_queries(3):
        api_client.get("/v1/applications/")
# unittest: with self.assertNumQueries(3): ...
```

## Presence, counting, large scans

- `qs.exists()` for presence; `qs.count()` for a number you need; never `len(qs)` unless you also need the rows.
- `qs.iterator(chunk_size=2000)` streams large result sets without caching them. Combined with `prefetch_related`, `iterator()` prefetches per chunk from Django 4.1 and needs an explicit `chunk_size` (deprecated without one in 4.1, an error from 5.0).
- `values_list("id", flat=True)` when only ids are needed.

## Bulk operations skip business logic

| Operation | Calls `save()` | Sends `pre_save`/`post_save` | Updates `auto_now` |
|---|---|---|---|
| `obj.save()` | yes | yes | yes |
| `QuerySet.update()` | no | no | no |
| `bulk_create()` | no | no | sets `auto_now_add` and `auto_now` values on insert (no `save()`) |
| `bulk_update()` | no | no | no (include the field and set it yourself) |

`bulk_create()` sets primary keys on the returned objects only on backends that support it (PostgreSQL, MariaDB 10.5+, SQLite 3.35+). **MySQL does not**: re-query by a natural key if you need the ids.

## Lost updates

```python
# Race: two workers read 5, both write 6
account.attempts += 1; account.save()

# Atomic in the database
Account.objects.filter(pk=account.pk).update(attempts=F("attempts") + 1)
```

For read-modify-write logic that can't be one `UPDATE`, lock the row:

```python
with transaction.atomic():
    app = Application.objects.select_for_update().get(pk=app_id)
    if app.status != "pending":
        raise InvalidTransition(app.status)
    app.status = "approved"
    app.save(update_fields=["status", "updated_at"])
```

`save(update_fields=...)` writes only those columns, reducing overwrite races between processes editing different fields. Remember `auto_now` fields aren't updated unless listed.

## Side effects after commit

```python
def approve(app_id):
    with transaction.atomic():
        app = _approve_locked(app_id)
        transaction.on_commit(lambda: publish_decision(app.reference, app.status))
```

Pass values (not model instances whose state may change) into the callback. In tests, `TestCase` never commits; use `self.captureOnCommitCallbacks(execute=True)` (3.2+) or pytest-django's `django_capture_on_commit_callbacks`.

## Raw SQL

```python
with connection.cursor() as cursor:
    cursor.execute("SELECT id FROM app WHERE status = %s AND score >= %s", [status, threshold])
```

Never f-strings or `%` formatting into the SQL string itself.
