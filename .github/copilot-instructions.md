# B3 Portfolio Master — Project Guidelines

## Agent Roles

When implementing or reviewing any feature in this project, reason from two simultaneous perspectives:

**Senior Software Architect**
- Enforce clean module boundaries, single responsibility, and testability.
- Prefer simple, explicit code over clever abstractions.
- Every public function must be unit-testable without Streamlit.
- 90% coverage floor is a hard constraint, not a target.

**Senior Portfolio Risk Analyst**
- Treat every financial number displayed to the user as potentially decision-critical.
- Cost basis, breakeven prices, DCA quantities, and profit targets must be arithmetically correct under edge cases (zero qty, earnings > cost, partial sells, corporate actions).
- Trailing stops must never be placed below the effective cost basis — doing so would expose the user to a guaranteed loss at trigger.
- DCA recommendations must be financially sound: only suggest adding to a position when the formula produces a positive, reachable target average.
- Prefer conservative defaults: when data is missing or ambiguous, show a warning rather than a potentially wrong number.
- Label all advisory output clearly as a suggestion, never as financial advice.

## Overview

A local Streamlit financial dashboard that parses B3 (Brazilian Stock Exchange) `.xlsx` export files,
calculates portfolio metrics, and displays interactive charts. All data processing is local;
the only external calls are optional Yahoo Finance requests for prices and FX rates.

## Architecture

```
src/app.py      — Streamlit UI: sidebar, session state, tabs, KPI layout
src/utils.py    — Parsing, FIFO cost-basis calculation, yfinance integration
src/charts.py   — Plotly chart factory functions (no Streamlit imports)
src/tables.py   — Streamlit dataframe renderers
src/langs.py    — i18n strings (EN, PT, ES, FR) — single source of truth for UI copy
tests/          — pytest unit tests (no Streamlit dependency; mock uploads with io.BytesIO)
```

## Build and Test

```bash
# Install runtime deps
make install

# Install dev deps (ruff, black, pytest, pre-commit)
make install-dev

# Run linter
make lint

# Run formatter
make format

# Run tests
make test

# Launch app
make run
```

The app runs at http://127.0.0.1:8501.

## Code Conventions

### Python style
- Line length: **100** (enforced by `black` and `ruff`).
- Target: **Python 3.9+** — avoid syntax unavailable in 3.9.
- Imports: `ruff` (isort rules) manages ordering; `src/` is the known-first-party package.

### Streamlit patterns
- Use `st.session_state` for all UI state. Persist critical state also in `st.query_params` so it survives browser reloads.
- Use `@st.cache_data(ttl=3600)` for any external network call (yfinance).
- Never import Streamlit inside `charts.py` or `utils.py` except where `@st.cache_data` is needed.

### Data pipeline
- Raw B3 files can be either **NEG** (Trading/Negotiation, detected by `Data do Negócio` column) or **MOV** (Movements, detected by `Movimentação` column).
- Parsed rows always carry these normalized columns: `date`, `ticker`, `type`, `qty`, `val`, `inst`, `source`, `desc`.
- `type` values: `BUY`, `SELL`, `EARNINGS`, `FEES`, `TRANSFER`, `IGNORE`.
- Only `BUY`/`SELL`/`EARNINGS` rows go into `main_df`. Everything else goes to `audit_df`.
- Deduplication runs after every upload using `drop_duplicates` on the full set of normalized columns.

### Ticker handling
- Always go through `clean_ticker()` in `utils.py`; do not manually strip suffixes elsewhere.
- Asset type detection uses `detect_asset_type()` — suffix-based: `11` → FII/ETF, `34/31/33` → BDR, `3-6` → Ação.

### i18n
- All user-visible strings must come from `langs.py` via the `texts` dict. No hardcoded Portuguese/English in `app.py`.
- When adding a new UI string, add it to **all four languages** in the same commit, in the same key order.

### tests
- Tests must not depend on Streamlit. Use `io.BytesIO` with a `.name` attribute to mock uploaded files.
- Test files map 1-to-1 with source modules: `tests/test_utils.py` ↔ `src/utils.py`.
- `@st.cache_data` functions can be tested by calling the underlying logic with `._cached_func` or by patching `st`.
- **Minimum coverage: 90%** across `src/`, excluding `app.py` (Streamlit entrypoint — not unit-testable). Enforced by `pytest --cov=src` using the `[tool.coverage.report] fail_under = 90` and `omit` config in `pyproject.toml`.
- When adding a new feature, always add or update the corresponding test before committing.

## Comments
Write comments as a senior developer would — plain, lowercase, short lines. No decorative dividers, no Unicode box art, no ASCII banners.

```python
# good
# retry limit reached; fall back to cached value

# bad
# ══════════════════ SECTION TITLE ══════════════════
```

## Commits

- Only commit when `make test` passes and the app starts cleanly with `make run`.
- Commit message format: `BRANCH_NAME: short clear message` — e.g., `main: add FII allocation chart`.
- No Conventional Commits type keywords (no feat/fix/refactor/chore prefixes).
- One logical change per commit. Do not batch unrelated changes.
- No decorative or emoji-heavy commit messages. Keep them plain and descriptive.

```bash
# good
git commit -m "main: add monthly earnings breakdown by sub_type"

# bad
git commit -m "✨ feat: added AMAZING new stuff!!! 🚀"
```

## README

- `README.md` is the single entry point for any new contributor. Keep it current.
- When adding a new feature (new tab, new chart, new CLI flag, new config option), update the relevant section in `README.md` in the same commit.
- When changing install steps, build commands, or environment requirements, update the README immediately — do not leave it stale.
- Do not add sections to the README for internal implementation details; those belong in code comments or this file.

## Report Files

B3 `.xlsx` export files used as input are always located at:

```
/Users/andersonlopes/Documents/dev/projects/b3/reports
```

When testing locally, referencing sample files, or pointing the app at real statements, always use this directory as the base path.

## Known Limitations / Watch Points
- **Market prices** are fetched via **yfinance** using the `.SA` suffix (covers all B3 tickers). No token required.
- **FX rates** (USD/BRL, EUR/BRL) are also fetched via **yfinance** (`USDBRL=X`, `EURBRL=X`). Falls back to fixed rates (USD 5.45, EUR 5.90) if yfinance is unavailable.
- `calculate_portfolio` iterates row-by-row in Python — acceptable for personal statement sizes, but avoid adding more loop-based logic there.
- `detect_asset_type` uses simple suffix matching; edge cases (e.g. single-letter tickers) may misclassify.
