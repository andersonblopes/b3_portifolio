# 01 — Overview & Architecture

## What this app is

B3 Portfolio Master is a single-user, local-first **Streamlit** dashboard
that ingests Brazilian stock exchange (B3) brokerage export files (`.xlsx`),
reconstructs portfolio positions with correct cost basis across every asset
type (stocks, FIIs, ETFs, BDRs, FI funds), and shows valuation, PnL, income
and allocation analytics. No database, no server-side persistence, no
multi-tenant concerns — everything lives in `st.session_state` for the
duration of the browser session.

Privacy model: uploaded files are processed only in memory. The only network
calls are optional and read-only — Yahoo Finance (`yfinance`) for prices/FX/
splits/historical prices, and brapi.dev for ticker logos.

## Tech stack

- Python 3.9+ (see `pyproject.toml` target-version; `.venv`/`venv` use newer
  interpreters locally but code must stay 3.9-compatible syntax).
- Streamlit — UI framework, reactive rerun model, `st.session_state`,
  `st.cache_data`, `st.fragment`, `st.dialog`.
- pandas — all data wrangling (DataFrames as the internal row format).
- yfinance — market data (no API key).
- plotly (`plotly.express`) — charts, dark theme.
- pytest + ruff + black + pre-commit — quality gate (see doc 07).

## Module map

```
src/app.py       Streamlit UI: sidebar, session state, tabs, KPI layout, position-analysis modal
src/utils.py     Parsing (NEG/MOV), cost-basis engine, yfinance/brapi integration, position analysis
src/charts.py    Plotly figure factories — pure functions, NO Streamlit import
src/tables.py    Streamlit dataframe renderers (styling, column config, pagination helpers)
src/langs.py     i18n string dict: LANGUAGES["English"|"Português (Brasil)"|"Español"|"Français"]
src/log_config.py  Logging setup (writes to logs/app.log)
tests/           pytest unit tests, 1:1 with src/ modules, no Streamlit dependency
```

Hard architectural rule (enforced in `.github/copilot-instructions.md`):
**`charts.py` and `utils.py` must not import Streamlit**, except for the
`@st.cache_data` decorator in `utils.py` where network calls are cached.
This keeps the parsing/finance/chart logic unit-testable without a running
Streamlit server.

## Data flow (happy path)

```
uploaded .xlsx files (NEG and/or MOV)
        │
        ▼
utils.load_and_process_files()          — see doc 03
        │  returns (main_df, stats_df, audit_df)
        ▼
utils.fetch_split_history(tickers)      — see doc 04
        │  yfinance splits, only used when MOV has no SPLIT/REVERSE_SPLIT rows
        ▼
utils.calculate_portfolio(main_df, split_history)   — see doc 02
        │  per-ticker chronological replay → qty, avg_price, total_cost, earnings
        ▼
utils.fetch_market_prices(tickers)      — see doc 04
        │  current price + live/fallback flag per ticker
        ▼
app.py: compute v_mercado, pnl, yield, KPIs, currency conversion (factor)
        │
        ▼
tabs: Visuals (charts.py) | Data Lab (tables.py + analyze_position modal, doc 05)
      | Earnings | Audit (audit_df) | Ticker Changes
```

`raw_df` (renamed `main_df` from the loader) and `audit_df` are both kept in
`st.session_state` for the whole session; `calculate_portfolio` and price/FX
fetches are recomputed on every rerun (Streamlit's execution model — the
whole script re-runs top-to-bottom on each interaction), which is why the
expensive network calls are wrapped in `@st.cache_data`.

## Session state & URL persistence

- `st.session_state.raw_df / import_stats / audit_df` — cleared by the
  "Clear session data" button; set once per upload.
- `lang_code` and `currency_code` are mirrored into `st.query_params`
  (`?lang=pt&cur=EUR`) so a page reload doesn't reset UI preferences even if
  `session_state` is wiped by the browser — see `src/app.py:257-341`.
- `st.session_state._lab_*` keys are a workaround to pass runtime values into
  the `@st.fragment`-decorated `_data_lab_groups()` without Streamlit's
  fragment-argument serialization constraints (`src/app.py:193-242`).

## Currency handling

Display currency (BRL/USD/EUR) is a pure presentation concern applied once
in `app.py` via a `factor` (1.0 for BRL, `1/rate` for USD/EUR) multiplied
into `avg_price`, `total_cost`, `earnings`, `p_atual`. All cost-basis math in
`utils.calculate_portfolio` happens in BRL (the currency B3 statements are
denominated in); never convert before that stage.

## Where to go next

- Money math correctness → `02-domain-financial-rules.md`
- File parsing / column mapping → `03-data-ingestion-and-parsing.md`
- Network/market data → `04-market-data-integration.md`
- The "should I buy/sell/hold" advisor → `05-position-analysis-engine.md`
- UI/Streamlit specifics → `06-ui-frontend.md`
- Tests & coverage gate → `07-testing-and-quality.md`
