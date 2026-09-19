# 06 — UI / Frontend (Streamlit)

Scope: `src/app.py`, `src/tables.py`, `src/charts.py`, `src/langs.py`.

## Streamlit execution model (why the code looks the way it does)

Streamlit re-runs the **entire script top-to-bottom** on every user
interaction (button click, selectbox change, etc.). Consequences visible in
this codebase:
- Expensive work (network calls) must be `@st.cache_data`-wrapped or it
  reruns every click (see doc 04).
- Persistent UI choices must live in `st.session_state` (survives reruns
  within a session) and, for the two settings that must survive a full page
  reload, also in `st.query_params` (`lang_code`, `currency_code` —
  `src/app.py:257-341`).
- `st.fragment` (`_data_lab_groups`, `app.py:193-242`) scopes a rerun to just
  that fragment so clicking a table row to open the analysis modal doesn't
  reset the user back to the first tab — a real Streamlit UX pitfall this
  code specifically works around.
- Because fragments can't take arbitrary runtime arguments cleanly, the
  fragment reads its inputs from dedicated `st.session_state._lab_*` keys
  set immediately before calling it.

## Page structure

```
Sidebar
  🌐 language selectbox (persisted to ?lang=)
  ⚙️ Settings: currency radio (persisted to ?cur=)
  📈 Market data: auto-refresh toggle + interval, manual refresh button, FX metric
  📄 Import: multi-file uploader, import stats table, dedup summary, Clear button

Main area (only rendered when raw_df is not None; otherwise a welcome screen)
  KPI row: Invested, Market Value (+delta%), Gross PnL, [Total Earnings, Net Earnings if any]
  Tabs (dynamic set, built from tab_labels list):
    📊 Visuals    — cashflow evolution area chart, allocation pie (asset type + institution),
                     monthly earnings bar chart (if earnings present)
    📝 Data Lab   — st.fragment; per-asset-type expanders with selectable tables →
                     click a row opens the Analysis modal (doc 05)
    💰 Earnings   — (only if has_earnings) allocation by sub_type/asset_type, earnings log table
    🧾 Audit      — (only if audit_df non-empty) paginated Fees / Transfers / Ignored tables
    🔄 Ticker Changes — static TICKER_REMAP / DISCONTINUED_TICKERS tables, yfinance corporate
                        actions since first purchase, tickers with no live price (possible delist)
```

Tab indices are computed dynamically (`earnings_tab_idx`, `audit_tab_idx`,
`ticker_changes_tab_idx`, `src/app.py:543-545`) since earlier tabs are
conditionally included — don't hardcode a tab index anywhere else.

## Currency conversion at the UI boundary

`factor` is `1.0` (BRL), `1/rate` (USD), or `1/rate` (EUR) depending on
`currency_code`, computed once (`src/app.py:434-442`) and applied to
`avg_price`, `total_cost`, `earnings`, `p_atual` right before display. All
upstream cost-basis math (doc 02) stays in BRL — never convert earlier in
the pipeline, or corporate-event math and dedup keys (doc 03) could drift
across a currency toggle within the same session.

`fmt_reg(v)` (`src/app.py:445-447`) formats with the right symbol and
decimal separator convention (comma for BRL, dot for USD/EUR).
`_mdfmt` in the modal additionally escapes `$` so Streamlit markdown doesn't
interpret it as a LaTeX delimiter — reuse `_mdfmt` (not `fmt_reg` directly)
whenever a formatted currency value is embedded in `st.markdown(...)`.

## Tables (`src/tables.py`)

`render_portfolio_table(df, texts, fmt_func, selectable, table_key, logos)`:
renames columns to i18n labels, applies a pandas Styler with per-column
`fmt_func` formatting and a red-yellow-green background gradient on the
yield column (`vmin=-15, vmax=15`). When `selectable=True`, adds a clickable
hint column and returns the `st.dataframe(on_select="rerun",
selection_mode="single-row")` event object so the caller can react to row
clicks (this is how the Analysis modal is triggered). Logos, when present,
are inserted as a leading `ImageColumn`.

`render_earnings_log(df, texts, fmt_func)`: simple renamed/formatted read-
only table for the Earnings tab audit log.

## Charts (`src/charts.py`)

Pure functions, **no Streamlit import** (enforced convention) — each takes
already-prepared data plus `sym`/`is_usd`/`title` and returns a
`plotly.graph_objects.Figure` styled with `template="plotly_dark"`. Decimal
separator (`seps = ".," if is_usd else ", "`) is set per-locale so hover
tooltips render correctly for both US and BR number formats.

- `plot_evolution` — cumulative cashflow area chart.
- `plot_allocation` — generic pie chart (used for asset-type, institution,
  earnings sub-type/asset-type breakdowns — same function, different
  `names_col`/`val_col`).
- `plot_earnings_evolution` — monthly earnings bar chart.
- `plot_bar_earnings_horizontal` — top-10 horizontal bar (defined but verify
  current call sites before assuming it's wired into a visible tab).

Rendered via `st.plotly_chart(..., config=PLOTLY_CONFIG)` where
`PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}` — the mode
bar (zoom/pan/download icons) is intentionally hidden across the whole app
for a cleaner dashboard look; don't re-enable it in just one chart without a
reason, for consistency.

## i18n (`src/langs.py`)

`LANGUAGES` dict, top-level keys are the four supported languages
(`"English"`, `"Português (Brasil)"`, `"Español"`, `"Français"`) — note the
dict key is the *full display name*, not the short code; `app.py` maps
between the two via `LANG_CODE_TO_KEY`/`LANG_KEY_TO_CODE` since URL query
params and internal state use the short code (`pt/en/es/fr`) for stability
across UI relabeling.

Hard rule (`.github/copilot-instructions.md`): every user-visible string
comes from `texts[...]`, sourced from `langs.py` — **no hardcoded copy in
`app.py`**. When adding a string, add it to **all four languages in the same
commit**, same key order (the file's own header comment enforces this).
`ruff`'s per-file ignore for `E501` (line length) is scoped to `langs.py`
only, since translated copy is long and splitting it hurts diffability.

## Session state keys reference

| Key | Purpose |
|---|---|
| `raw_df`, `import_stats`, `audit_df` | parsed data, set on upload, cleared by "Clear session data" |
| `lang_code`, `currency_code` | UI prefs, mirrored to `st.query_params` |
| `last_auto_refresh_count` | dedupe auto-refresh ticks from `st_autorefresh` |
| `_lab_pm`, `_lab_texts`, `_lab_fmt`, `_lab_prices`, `_lab_mkt_total`, `_lab_logos` | inputs for the `_data_lab_groups` fragment |
| `_analysis_prev_{asset_type}` | prevents the Analysis modal from reopening after the user dismisses it, until a *new* row is selected |
| `tbl_{asset_type}` | `st.dataframe` widget keys, one per asset-type expander |
| `{key_prefix}_page`, `{key_prefix}_page_size` | Audit tab pagination state (fees/transfers/ignored, independently paginated) |
