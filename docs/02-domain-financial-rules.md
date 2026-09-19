# 02 — Domain & Financial Rules (Cost Basis Engine)

Scope: `utils.calculate_portfolio()` (`src/utils.py:396-556`) and the event
types produced by the parser (doc 03) that flow into it. This is the most
financially sensitive code in the project — every number here is treated as
decision-critical (per `.github/copilot-instructions.md` "Agent Roles").

## Core model

Positions are computed by replaying every relevant row **in chronological
order, per ticker** (`data.sort_values("date")`, grouped by canonicalized
ticker). State kept per ticker while replaying: `qty`, `cost` (total cost
basis in BRL), `earnings` (accumulated cash distributions, tracked
separately and never mixed into `cost`), `realized_pnl` (banked trading
profit/loss, survives full exits), `gross_buys` (lifetime BUY cash outlay,
never netted against SELLs — see "Invested capital vs. total bought" below).

## Event → effect table

| `type`            | Effect                                                              | Code ref |
|-------------------|----------------------------------------------------------------------|----------|
| `BUY`             | `qty += row.qty; cost += row.val; gross_buys += row.val`             | utils.py:450 |
| `SELL`            | `avg = cost/qty; qty -= sell_qty; cost = qty * avg` (clamped so qty never goes negative) | utils.py:454 |
| `COST_RESET`      | `cost = qty * fetch_historical_price(ticker, date)` — Atualização (patrimonial restatement) | utils.py:475 |
| `EARNINGS`        | `earnings += val` — does not touch qty/cost                          | utils.py:499 |
| `AMORTIZATION`    | `cost = max(0, cost - val)` — return of capital, reduces cost, not income | utils.py:502 |
| `BROKER_TRANSFER` | `cost = qty * fetch_historical_price(...)`, only when `val` is empty/zero (plain inter-broker transfer, not a settlement row) | utils.py:517 |
| `SPLIT`           | MOV-sourced: `qty += new_shares_credited`. yfinance-sourced: `qty *= ratio` | utils.py:541 |
| `REVERSE_SPLIT`   | MOV-sourced: `qty = new_qty` (absolute, not delta). yfinance-sourced: `qty *= ratio` (ratio < 1) | utils.py:549 |

Cost basis is **never** adjusted for splits/reverse-splits — only quantity
changes, so `avg_price` naturally rescales. Cost is only reset on explicit
Atualização, inter-broker transfers, and reduced by amortization payouts.
`gross_buys` is untouched by every reset/reduction event (COST_RESET,
BROKER_TRANSFER, AMORTIZATION, SELL) — it is a pure running sum of BUY rows.

A position is only kept in the final summary if `round(qty, 4) > 0` **or**
`earnings != 0` **or** `realized_pnl != 0` **or** `gross_buys != 0`
(utils.py:567) — so a fully-sold ticker that still paid dividends, realized
a gain/loss, or was ever bought still shows up in the relevant totals.

## Invested capital vs. total bought (dashboard KPIs)

Two dashboard numbers look similar but answer different questions — the
distinction matters because "sum of BUY − sum of SELL" is *not* a valid
substitute for either one:

- **Invested capital** (`inv_total` in `app.py`, sourced from
  `total_cost`): cost basis of positions **still held** (`qty > 0` only).
  Answers "what would it cost to rebuild what I currently hold". A profitable
  SELL does not appear here at all — the remaining shares keep their original
  average price, they're just fewer of them.
- **Total bought** (`gross_buys_total` in `app.py`, sourced from
  `gross_buys`): lifetime cash outlay across every BUY row, for every
  ticker, including fully-exited ones. Answers "how much of my own money did
  I ever put into B3". Never reduced by a SELL.

Naively computing "money invested" as `sum(BUY.val) - sum(SELL.val)` conflates
these two concerns and additionally launders realized trading P/L into the
capital figure: selling above cost shrinks the naive total by more than the
capital actually returned (the excess is profit, not principal), and selling
at a loss does the opposite. Realized P/L is reported separately
(`realized_pnl` / "Realized P/L" KPI) precisely so it isn't double-counted
this way.

**Total profit** (`total_profit` in `app.py`) = `realized_pnl` (banked
trading P/L, all tickers) + `net_earnings` (dividends/JCP net of brokerage
fees). It deliberately excludes unrealized P/L (`gross_pnl`, the hero-tier
KPI) since that gain/loss isn't locked in yet.

## D-1 close convention (COST_RESET / BROKER_TRANSFER)

Both reset events call `fetch_historical_price(ticker, date)`
(`utils.py:590-622`), which fetches the **last trading day's close before**
the event date (D-1), matching B3's own convention for corporate-action
reference pricing:

```
window = history(start=date-7d, end=date+7d)
before = window[window.index < date]
return before["Close"].iloc[-1] if not before.empty else fallback-to-event-day-or-after
```

If the price fetch fails (`None`), the cost basis is left **unchanged** and a
`WARNING` is logged — never silently zero out or guess a value.

Known residual gap: banks use B3's proprietary intraday reference price for
Atualização events, not the exchange close. A R$0.01–2.00 gap vs. the bank's
own reported cost basis is expected and documented, not a bug (see
`04-market-data-integration.md` and the skill's `cvm-data-sources.md`).

## Distinguishing BROKER_TRANSFER resets from settlement rows

Plain `Transferência` (inter-broker custody move, `val` empty/zero) triggers
a reset. `Transferência - Liquidação` (trade settlement, `val` > 0) must
**not** trigger a reset — it's already captured by the NEG file. The gate is:

```python
str(row.get("val", "") or "").strip() in ("", "0", "nan", "0.0")
```

See `src/utils.py:511` and the mapping rule in doc 03.

## AMORTIZATION vs EARNINGS

Amortização is return of *principal*, not income. Routing it to `earnings`
would inflate yield-on-cost and understate true cost basis. It must reduce
`cost` directly and never touch `earnings`. This is enforced at the mapping
stage too (`map_mov()` returns `AMORTIZATION`, a distinct type from
`EARNINGS`, even though `classify_earning()` — used only for the earnings
sub_type label — separately tags amortization-flavoured EARNINGS text if it
ever slips through; the authoritative gate is the `type` column, not
`sub_type`).

## Ticker canonicalization (applies before all of the above)

`TICKER_REMAP` (`src/utils.py:34-42`) maps old B3 codes to current codes for
funds that were renamed/merged (e.g. `BRIT3→BRST3`, `CVBI11→PCIP11`).
`calculate_portfolio` applies this remap to the `ticker` column **before**
grouping (`utils.py:409`), so historical rows under the old code merge into
one position with the new code. Also applied before yfinance queries and
logo lookups. `DISCONTINUED_TICKERS` (`utils.py:47-52`) are excluded from the
portfolio summary entirely — funds wound down with no tradeable value or no
yfinance data.

When adding a new remap or discontinued entry, update **both** the code dict
and `langs.py` doesn't need changes (the Ticker Changes tab reads the dicts
directly, not langs) — but do check `README.md`'s "Roadmap" section isn't
claiming the opposite.

## Guardrails already in place

- `SELL` clamps `sell_qty` to available `qty` and logs a `WARNING` instead of
  going negative (statement inconsistencies happen — corrupted exports,
  partial history uploads).
- Split injection from yfinance is skipped per-ticker if the MOV file
  already supplied `SPLIT`/`REVERSE_SPLIT` rows, to avoid double-applying
  the same corporate action from two sources (`utils.py:420`).

## Extending this table (checklist)

When adding a new event `type`:
1. Add the mapping rule in `map_mov()` (doc 03) and add it to `_main_types`
   if it must reach `main_df`.
2. Add the branch in `calculate_portfolio`'s row loop.
3. Update this table and `references/corporate-events.md` in the
   `fintech/b3-portfolio-analysis` skill.
4. Grep `tests/test_utils.py` for any assertion on `set(main_df['type'])` or
   stats counters (`rows_transfer`, etc.) — they break silently otherwise.
5. Re-run `make test` and confirm the 90% coverage floor still holds.
