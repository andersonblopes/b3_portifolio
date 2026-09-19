# 04 — Market Data Integration

Scope: every outbound network call in the project. All calls are read-only,
optional (the app still functions with stale/fallback data if they fail),
and wrapped in `@st.cache_data` so Streamlit's rerun-on-every-interaction
model doesn't hammer external APIs.

## Providers used

| Provider | Purpose | Auth | Fallback on failure |
|---|---|---|---|
| Yahoo Finance (`yfinance`) | Current prices, FX rates, split history, historical close prices | none | see per-function below |
| brapi.dev icons CDN | Ticker logo images | none (public asset URLs) | `None` per ticker (UI shows no image) |

Note: `README.md` also mentions an *optional* brapi.dev token for live
prices/FX as an alternative data source — as of the current `src/utils.py`,
prices/FX actually go through `yfinance`, not brapi's authenticated
endpoints. Treat the brapi-token mention in `README.md` as aspirational/
historical; verify against `utils.py` before trusting it, and fix the README
if you touch pricing.

## Functions

### `get_exchange_rate(base_currency="USD")` — `utils.py:55-69`
- `@st.cache_data(ttl=3600)` (1 hour).
- Ticker pattern: `f"{base}BRL=X"` (e.g. `USDBRL=X`, `EURBRL=X`).
- On any exception: logs `.exception(...)` and returns a **fixed fallback**
  (`USD: 5.45`, `EUR: 5.90`, else `5.45`). These fallbacks are hardcoded —
  update them periodically or the fallback drifts far from reality if
  yfinance is down for an extended period.

### `fetch_market_prices(tickers)` — `utils.py:625-654`
- `@st.cache_data(ttl=3600)`.
- Batch `yf.download(sa_tickers, period="1mo", group_by="ticker",
  auto_adjust=True)` — `period="1mo"` (not `"1d"`) specifically so prices
  survive multi-day holiday gaps (e.g. Easter week) via
  `.dropna().iloc[-1]`.
- Returns `{ticker: {"p": float|None, "live": bool}}`. Renamed tickers are
  resolved through `TICKER_REMAP` before querying (`.SA` suffix appended).
- Per-ticker failures are caught individually so one bad ticker doesn't zero
  out the whole batch; `live=False` signals the UI to show a ⚠️ badge and the
  caller (`app.py:486-501`) falls back to `avg_price` as the displayed
  current price (never `0`, which would corrupt PnL%).

### `fetch_split_history(tickers: tuple)` — `utils.py:559-586`
- `@st.cache_data(ttl=86400)` (24h — splits are rare, don't change intraday).
- **Must receive a `tuple`, not a `list`** — `st.cache_data` requires
  hashable arguments. Callers do `tuple(sorted(...))`.
- Returns `{ticker: [{"date": Timestamp, "ratio": float}, ...]}`; ratio > 1
  is a forward split, < 1 a reverse split. Discontinued tickers are skipped
  entirely.
- Consumed by `calculate_portfolio` (doc 02) to inject synthetic
  `SPLIT`/`REVERSE_SPLIT` rows **only** for tickers whose MOV file didn't
  already report the corporate action, to avoid double-application.

### `fetch_historical_price(ticker, date)` — `utils.py:589-622`
- `@st.cache_data(ttl=86400)`.
- Powers `COST_RESET` and `BROKER_TRANSFER` in the cost-basis engine (doc 02).
- **D-1 close convention**: fetches a ±7-day window, returns the last close
  strictly before `date`; falls back to the first close on/after `date` if
  no prior day exists in the window (e.g. event on a Monday with a holiday
  Friday); falls back further to the last available close in the whole
  window if even that's empty. Returns `None` only if the window has no data
  at all — callers must treat `None` as "leave cost basis unchanged, log a
  warning", never as `0`.

### `fetch_asset_logos(tickers: tuple)` — `utils.py:665-685`
- `@st.cache_data(ttl=86400)`.
- brapi.dev has no listing endpoint, so each ticker is probed with a
  `HEAD` request (3s timeout) against
  `https://icons.brapi.dev/icons/{ticker}.svg`; `200` → logo URL, anything
  else (including network errors) → `None`, handled gracefully in
  `tables.py`'s `ImageColumn` (no crash, blank cell).

## Data source limits (important for correctness discussions)

- **CVM does not publish daily FII NAV** — only a monthly `informe mensal`,
  and that's for regular FI funds via `inf_diario_fi`, not FIIs at all. This
  is why `fetch_historical_price` uses yfinance close, not CVM data, for
  `COST_RESET`. See the skill's `references/cvm-data-sources.md` for dataset
  URLs if CVM integration is ever added.
- Banks compute Atualização cost resets using B3's proprietary intraday
  reference price, which this app cannot access for free. Expect a
  **R$0.01–2.00 residual gap** vs. the bank's own displayed cost basis —
  this is documented behavior, not a bug to "fix" by tweaking the fetch
  window.

## Caching gotchas

- Never pass a `list` to any `@st.cache_data` function in this file — lists
  aren't hashable; always convert to `tuple` at the call site.
- Manual "Refresh Market Prices" button and the auto-refresh timer both call
  `.clear()` on the cached functions (`utils.fetch_market_prices.clear()`,
  `utils.get_exchange_rate.clear()`) — see `src/app.py:378-383`. If you add a
  new cached market-data function, wire it into that same refresh handler or
  it'll silently stay stale until the TTL expires.
- In tests, bypass the cache with `fn.__wrapped__(args)` — the established
  pattern in this codebase; don't call `.clear()` or monkeypatch the
  decorator (see `07-testing-and-quality.md`).
