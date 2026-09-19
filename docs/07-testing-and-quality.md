# 07 — Testing & Quality Gate

Scope: `tests/`, `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`.

## Commands

```bash
make install        # runtime deps into venv/
make install-dev     # + ruff, black, pytest, pre-commit hooks
make lint            # ruff check .
make format          # ruff format . && black .
make test            # venv/bin/python -m pytest --cov=src
make run             # streamlit run src/app.py  → http://127.0.0.1:8501
```

Coverage with missing-lines detail: `./venv/bin/python -m pytest --cov=src
--cov-report=term-missing`.

## Coverage gate

`pyproject.toml`:
```toml
[tool.coverage.run]
omit = ["src/app.py"]     # Streamlit entrypoint, not unit-testable without a running server
[tool.coverage.report]
fail_under = 90
```
90% is a **hard constraint** per `.github/copilot-instructions.md`
("Senior Software Architect" role), not an aspirational target. `app.py` is
excluded from the measured set entirely — meaning all business logic that
matters for coverage purposes must live in `utils.py`/`tables.py`/
`charts.py`, not inline in `app.py`. This is also why `app.py` is fairly
"thick" with UI wiring but delegates all actual computation.

As of the last commit referenced in the workspace snapshot, the suite is at
74/74 tests passing (`ec7521e`). Re-run `make test` to get the current count
before relying on that number.

## Test-to-module mapping

```
tests/test_utils.py     ↔ src/utils.py     (61 test functions — by far the largest file:
                                             parsing, dedup, cost-basis engine, all event
                                             types, market data functions, analyze_position)
tests/test_tables.py    ↔ src/tables.py    (5)
tests/test_charts.py    ↔ src/charts.py    (4)
tests/test_langs.py     ↔ src/langs.py     (2 — likely key-parity checks across languages)
tests/test_log_config.py ↔ src/log_config.py (2)
```
No `tests/test_app.py` — by design, since `app.py` is Streamlit-only and
excluded from coverage.

## Established test patterns (do not deviate without reason)

- **No Streamlit dependency in tests.** Mock uploaded files with
  `io.BytesIO(...)` plus a `.name` attribute (B3 loader reads
  `getattr(file, "name", "uploaded.xlsx")`).
- **Bypassing `@st.cache_data`**: call `fn.__wrapped__(args)` to reach the
  undecorated function directly. Do **not** call `fn.clear()` or monkeypatch
  the decorator — this is the established pattern across the suite; a
  different approach will look inconsistent in review.
- **`pandas.Series.map(dict)` gotcha**: converts absent keys to `NaN`, not
  `None`. Tests asserting the "value not found" case must use `pd.isna(cell)`,
  never `cell is None` — this bit the original implementation once (see the
  `b3-portfolio-analysis` skill's pitfalls list).
- **`iterrows()` typing gotcha**: yields `(index, Series)`; `row["date"]` is
  typed as `Series` by static analysis (Pyright) but is a scalar at runtime.
  Wrap with `pd.Timestamp(row["date"])` when passing into a typed helper —
  purely to silence false-positive type warnings, not a real bug.
- **Never pass a `list`** to any function under test that's decorated with
  `@st.cache_data` (`fetch_split_history`, `fetch_asset_logos`, etc.) — use
  `tuple(...)`, matching what the real call sites do.

## When adding a new event type / feature (regression checklist)

Cribbed from the `b3-portfolio-analysis` skill's pitfalls, specific to this
repo's test suite:
1. Grep `tests/test_utils.py` for any assertion on
   `set(main_df['type'].unique())` or `audit_df['type']` — adding a type to
   `_main_types` (doc 03) will silently break these unless updated.
2. Check stats counters like `rows_transfer` — e.g. `rows_transfer == 0` is
   the *correct* expectation once all `Transferência` rows classify as
   `BROKER_TRANSFER` (a main_df type) rather than the legacy `TRANSFER`
   audit type. Don't "fix" a test back to a stale expectation.
3. Add/update a test **before** committing (per
   `.github/copilot-instructions.md` "tests" section) — this is a stated
   process rule, not just a suggestion.
4. Re-run `make test` and confirm coverage is still ≥ 90% before commit.

## Pre-commit / lint / format

- `ruff` rules enabled: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `UP`
  (pyupgrade), `B` (bugbear). Line length 100 for both `ruff` and `black`.
- `src/langs.py` is exempt from `E501` (long translated strings).
- `known-first-party = ["src"]` for isort — don't let `src/` imports get
  sorted as third-party.
- `.pre-commit-config.yaml` wires these into git hooks; `make install-dev`
  runs `pre-commit install`.

## Commit discipline (process, not code, but relevant to "done")

Per `.github/copilot-instructions.md`: only commit when `make test` passes
**and** the app starts cleanly with `make run`. Commit format:
`BRANCH_NAME: short clear message` (no Conventional Commits prefixes, no
emoji), one logical change per commit.
