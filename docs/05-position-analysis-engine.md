# 05 — Position Analysis Engine (Advisory Modal)

Scope: `utils.analyze_position()` (`src/utils.py:688-867`), surfaced via the
"📊 Analysis" modal in `app.py` (`_show_analysis_modal`, `src/app.py:15-190`)
when a user clicks a row in the Data Lab tables.

**This is advisory output, not financial advice** — the modal explicitly
labels recommendations as suggestions (per `.github/copilot-instructions.md`
"Senior Portfolio Risk Analyst" role). Any change here must preserve that
framing.

## Inputs

`ticker, qty, avg_price, total_cost, current_price, earnings, asset_type,
portfolio_total_value=0.0`. Returns `None` immediately if `current_price <=
0` or `qty <= 0` — never computes ratios against zero/negative denominators.

## Key derived metrics

| Metric | Formula | Purpose |
|---|---|---|
| `yield_pct` | `(current_price - avg_price) / avg_price * 100` | unrealized return |
| `effective_cost` | `max(total_cost - earnings, 0)` | cost basis netted against dividends already received |
| `breakeven_price` | `effective_cost / qty` | price needed to be whole after counting dividends |
| `yield_on_cost` | `earnings / total_cost * 100` | income yield vs. original cost — drives the "dividend cushion" override |
| `current_weight` | `market_value / portfolio_total_value * 100` | concentration check |
| `trailing_stop` | `max(current_price * (1 - trail_pct), breakeven_price)` | see next section |

## Trailing stop — asset-class-aware, floored at breakeven

```python
trail_pct = 0.08 if asset_type == "FII/ETF" else 0.12 if asset_type == "BDR" else 0.15
trailing_stop = max(current_price * (1 - trail_pct), breakeven_price)
```

**Hard invariant** (per the Risk Analyst role): the stop is floored at
`breakeven_price`, never below it — placing a stop below effective cost
would guarantee a realized loss at trigger. Any refactor of this formula
must preserve the `max(...)` floor.

## Recommendation priority order (first match wins)

```
1. price_below_stop AND yield_on_cost >= 8%   → HOLD   (dividend income offsets the stop signal)
2. price_below_stop                            → EXIT
3. gain scenario AND yield_pct >= 50%          → TRIM
4. gain or flat scenario                       → HOLD
5. yield_on_cost >= 8% (loss scenario)         → HOLD   (dividend cushion)
6. dca list has an option with no concentration risk → DCA
7. else                                        → HOLD   (concentration blocked / no valid DCA)
```
Code: `src/utils.py:838-852`. When adding a new recommendation branch,
preserve this exact ordering — later branches are only reached if earlier
ones don't match, and the modal's rationale text (`app.py`'s
`_rationale_key` selection) mirrors this same precedence.

## Gain scenario: scale-out targets + DCA top-up

Pyramid targets at `+20%`, `+50%`, `+100% (double)` above `avg_price`, each
suggesting selling `25%`/`33%`/`50%` of the position respectively — only
included if the target price is still **above** `current_price` (i.e., not
already passed). If `yield_pct < 20`, also offers a single DCA top-up
(`add_qty = 50% of current qty`), gated by concentration (see below).

## Loss scenario: DCA formulas

Two DCA levels are attempted: recovering to the midpoint between
`avg_price` and `current_price`, and recovering to `current_price * 1.05`.
Each solves for `add_qty` such that buying that many shares at
`current_price` brings the new average down to `target_avg`:

```python
add_qty = (total_cost - target_avg * qty) / (target_avg - current_price)
```

Only kept if `target_avg` is strictly between `current_price` and
`avg_price` (the algebra is only meaningful in that range) and
`add_qty_raw > 0`. This is the "financially sound" constraint from the Risk
Analyst role — never suggest a DCA that can't mathematically reach its
stated target.

## Concentration guardrail

`_concentration(add_qty)` (`utils.py:754-761`) recomputes portfolio weight
*after* the hypothetical buy; any DCA option pushing the position above
**10%** of `portfolio_total_value` is flagged `concentration_risk: True` and
excluded from driving a `DCA` recommendation (though still shown in the
modal with a warning). If **all** DCA options are blocked by concentration,
the recommendation falls through to `HOLD` (step 7 above), not `DCA`.

## Notes list

`notes` accumulates informational keys (`note_high_gain`,
`note_earnings_offset`, `note_deep_loss`) resolved to i18n strings in
`app.py`/`langs.py`, shown as supplementary context — currently rendered
inconsistently (check `app.py` before assuming every note key is displayed;
some are computed but not all are wired into the modal UI).

## Editing checklist

1. Any new metric or branch must be covered by `tests/test_utils.py` — this
   function has the highest financial blast radius in the app.
2. Preserve the `None` short-circuit for invalid input (`price <= 0` or
   `qty <= 0`).
3. Preserve the breakeven floor on `trailing_stop`.
4. If you add a new `recommendation` value, add its `rec_*`, `exec_*`,
   `action_*`, `rec_rationale_*` keys to **all four languages** in
   `langs.py` — the modal will `KeyError`/`.get()`-fallback ugly otherwise.
