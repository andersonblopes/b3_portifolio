# 09 — Known Limitations & Roadmap

Distinguishing **documented tradeoffs** (don't "fix" without a real reason)
from **actual gaps** (fair game for improvement) matters here — several
things that look like bugs at first glance are intentional.

## Documented tradeoffs (not bugs)

- **Residual R$0.01–2.00 gap on Atualização/BROKER_TRANSFER cost resets** vs.
  what the bank itself reports. Cause: banks use B3's proprietary intraday
  reference price; this app uses yfinance D-1 close, the best free
  approximation available. See doc 02 and doc 04.
- **FX fallback rates are hardcoded** (`USD: 5.45`, `EUR: 5.90` in
  `get_exchange_rate`) and only used when yfinance is unreachable. They will
  drift from reality over time — periodic manual updates are expected
  maintenance, not a design flaw.
- **`calculate_portfolio` iterates row-by-row in Python** per ticker
  (`.iterrows()`-based loop). Acceptable for a personal-statement-sized
  dataset (hundreds to low thousands of rows); explicitly flagged in
  `.github/copilot-instructions.md` as "avoid adding more loop-based logic
  there" rather than "rewrite this vectorized" — a deliberate scope
  boundary, not an oversight.
- **`app.py` is excluded from coverage measurement** by design (Streamlit
  entrypoint, not unit-testable without a running server) — see doc 07.
- **No database / no persistence** — data lives only in
  `st.session_state` for the session; this is the stated privacy model in
  `README.md`, not a missing feature.

## Known gaps (candidates for improvement)

- **`detect_asset_type` suffix heuristic** can misclassify edge cases (e.g.
  single-letter or unusual tickers) — it's not backed by B3's actual
  instrument registry. Flagged explicitly in
  `.github/copilot-instructions.md` "Known Limitations".
- **`.github/copilot-instructions.md` has drifted from `src/utils.py`** on
  the `_main_types` set and the description of dedup as plain
  `drop_duplicates` (it's actually the file-aware max-per-group algorithm in
  doc 03). Worth reconciling next time that file is touched, so future
  agents don't get misled by the stale description.
- **README's brapi.dev token mention** for live prices/FX doesn't match the
  current `yfinance`-based implementation in `utils.py` — see doc 04. Worth
  clarifying in the README (brapi is only used for logos today).
- **`plot_bar_earnings_horizontal`** exists in `charts.py` but its current
  call sites should be re-verified — confirm whether the Earnings tab (or
  any tab) actually renders it before assuming it's live UI.

## Roadmap ideas from `README.md`

- Offline mode (no Yahoo Finance calls) — would need a manual price-entry
  path and a way to skip corporate-action fetches gracefully (already
  partially supported: `fetch_historical_price` returning `None` leaves cost
  basis unchanged rather than crashing).
- Improve parsers to support more B3 export layout variations (only one
  header-offset heuristic exists today, doc 03).
- Better consolidated Excel export (not currently implemented at all).

## Process notes for future changes

- Any change to the cost-basis engine (doc 02) must keep
  `references/corporate-events.md` in the `fintech/b3-portfolio-analysis`
  Hermes skill in sync — that skill is the portable, cross-project version
  of the same rules.
- Financial correctness bar applies uniformly: every displayed number is
  decision-critical (`.github/copilot-instructions.md`). When in doubt,
  favor showing a warning/fallback over guessing a number.
