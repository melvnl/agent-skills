# Python feature availability by version

Check the project's **oldest supported** version before using a feature. "Runtime" means the construct is evaluated when the code runs; annotations can sometimes use newer syntax under `from __future__ import annotations` (3.7+), because annotations are then not evaluated, but tools that inspect annotations at runtime (Pydantic, FastAPI, dataclass helpers) still evaluate them.

| Feature | Minimum | Notes |
|---|---|---|
| f-strings | 3.6 | `f"{x=}"` debugging form: 3.8 |
| `dataclasses` | 3.7 | `slots=True`, `kw_only=True`: 3.10 |
| `contextvars` | 3.7 | |
| `from __future__ import annotations` | 3.7 | postpones annotation evaluation |
| Dict insertion order guaranteed | 3.7 | |
| Walrus `:=` | 3.8 | |
| Positional-only parameters `/` | 3.8 | |
| `typing.Literal`, `Final`, `Protocol`, `TypedDict` | 3.8 | earlier via `typing_extensions` |
| `functools.cached_property` | 3.8 | |
| Built-in generics `list[int]`, `dict[str, int]` at runtime | 3.9 | in annotations only with the `__future__` import on 3.7–3.8 |
| `zoneinfo` | 3.9 | `backports.zoneinfo` earlier |
| `asyncio.to_thread` | 3.9 | copies `contextvars` context |
| `str.removeprefix` / `removesuffix` | 3.9 | |
| `X \| Y` union types at runtime | 3.10 | `Optional[X]` / `Union[X, Y]` earlier |
| `match` statement | 3.10 | |
| Parenthesized context managers | 3.10 | officially |
| `zip(strict=True)` | 3.10 | |
| `tomllib` | 3.11 | `tomli` earlier |
| `ExceptionGroup`, `except*` | 3.11 | |
| `typing.Self`, `asyncio.TaskGroup`, `asyncio.timeout` | 3.11 | |
| `datetime.UTC` alias | 3.11 | `timezone.utc` works everywhere |
| `datetime.utcnow()` deprecated | 3.12 | use `datetime.now(timezone.utc)` |
| Type parameter syntax `def f[T](x: T)`, `type` statement | 3.12 | |
| `LoggerAdapter(merge_extra=True)` | 3.13 | |

## Legacy runtimes

- **Python 2.7**: no f-strings, no type annotations in signatures (comments only), `unicode` vs `str`, integer division with `/`. Treat as a separate dialect; check for `six` or `future` usage.
- **3.5 and below**: no f-strings, no variable annotations (3.6).
- When a project pins an end-of-life runtime, don't silently "modernize" it. Propose the upgrade as its own decision.
