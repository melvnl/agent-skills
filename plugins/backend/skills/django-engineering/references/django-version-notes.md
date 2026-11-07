# Django features by version

| Feature | Since |
|---|---|
| `Meta.constraints` with `UniqueConstraint`, `CheckConstraint`; `bulk_update()`; `request.headers` | 2.2 |
| `UniqueConstraint(condition=...)` (partial unique; backend support varies, not MySQL) | 2.2 |
| Async views and middleware | 3.1 |
| Cross-database `models.JSONField` | 3.1 |
| `DEFAULT_AUTO_FIELD` setting; `captureOnCommitCallbacks` | 3.2 |
| Functional indexes and expressions in `UniqueConstraint` | 3.2 / 4.0 |
| Async ORM interface (`aget`, `acreate`, `async for` over querysets) | 4.1 |
| `bulk_create(update_conflicts=True, ...)` | 4.1 |
| `Model.validate_constraints()` and constraint validation in `full_clean()` | 4.1 |
| `db_default` field option; `GeneratedField`; `USE_TZ` defaults to `True` | 5.0 |
| `CheckConstraint(condition=...)` (the `check=` argument deprecated) | 5.1 |

Notes:
- Upgrades are a planned change with the deprecation timeline in mind: Django removes deprecated features two feature releases later.
- Check database backend support: some features (partial unique constraints, `skip_locked`, `RETURNING` on bulk inserts) depend on the engine and its version.
- DRF versions track supported Django versions; check DRF's release notes before upgrading either.
