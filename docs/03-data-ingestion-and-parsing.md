# 03 — Data Ingestion & Parsing

Scope: `utils.load_and_process_files()` (`src/utils.py:104-393`) — turning
raw B3 `.xlsx` exports into the normalized `main_df` / `audit_df` / `stats_df`
trio consumed by the rest of the app.

## Statement type detection

B3 exports two distinct file layouts; both are auto-detected by column
presence — no filename convention is relied upon:

| Statement | Detection column | Contents |
|---|---|---|
| **NEG** (Negociação / Trading) | `Data do Negócio` | BUY/SELL trades |
| **MOV** (Movimentação) | `Movimentação` (sometimes after a header-offset fix, see below) | Corporate actions, earnings, fees, transfers |

If a MOV file has an offset header (some B3 exports don't start the header
on row 0), the loader scans rows for one containing the literal string
`"Data"` and re-slices the DataFrame from there (`utils.py:176-182`). If
neither detection matches, the file is skipped with a `WARNING` log — no
exception is raised, so one bad file in a multi-file upload doesn't abort
the whole import.

## Normalized column schema

Every row that reaches `main_df` or `audit_df` carries:

```
date      pd.Timestamp (dayfirst=True parsed; NaT on failure)
ticker    str, canonicalized via clean_ticker()
type      str enum — see doc 08 glossary + doc 02 event table
qty       float (0.0 if missing/unparseable)
val       float, signed for MOV rows (see sign handling below)
inst      str, brokerage/institution name ("Desconhecida" if missing)
source    "NEG" | "MOV" | "yfinance_split" (synthetic rows injected later)
desc      str, original B3 movement description (for audit/display)
sub_type  str, only set for MOV rows (Dividend/JCP/Amortization/Income) — earnings breakdown label
```

## NEG (trading) mapping

```python
temp["type"] = "IGNORE"
temp.loc[movement.str.contains("COMPRA", na=False), "type"] = "BUY"
temp.loc[movement.str.contains("VENDA", na=False), "type"] = "SELL"
```

Anything that isn't explicitly COMPRA/VENDA stays `IGNORE` and goes to
`audit_df` — never guessed as SELL by default. `Valor` is the trade total
(already qty × price, per B3's export convention); the code never multiplies
qty × unit price itself for BUY/SELL.

## MOV (movements) mapping — `map_mov()`

Text is normalized first via `_norm()` (`utils.py:14-19`): uppercase +
strip accents (NFKD decompose + drop non-ASCII), so `"Atualização"` and
`"ATUALIZACAO"` match the same keyword. Keyword → type table lives in doc 02
(`02-domain-financial-rules.md`) since it's really a financial classification
concern; the full precedence order (checked top to bottom, first match
wins) is in `src/utils.py:202-242` and mirrored in the skill's
`references/corporate-events.md`.

Sign handling: `val` is multiplied by `-1` when `Entrada/Saída` column says
Débito (`_norm(x)` contains `"DEB"`), `+1` for Crédito. If the column is
absent, sign defaults to `+1` (`utils.py:190-196`).

## Which rows reach `main_df` vs `audit_df`

```python
_main_types = {
    "EARNINGS",
    "SPLIT",
    "REVERSE_SPLIT",
    "SELL",
    "COST_RESET",
    "AMORTIZATION",
    "BROKER_TRANSFER",
}
```
(`src/utils.py:275-278`) — everything else from MOV (`FEES`, `TRANSFER`,
`IGNORE`) goes to `audit_df` only. All NEG `IGNORE` rows also go to
`audit_df`. This split exists so the portfolio math (main_df) only ever sees
rows that change qty/cost/earnings, while the Audit tab (doc 06) can still
show the full picture for transparency.

> Note: `.github/copilot-instructions.md` currently states an older, smaller
> `_main_types` set (`BUY/SELL/EARNINGS` only). That doc has drifted from the
> code — trust `src/utils.py` and this file, and fix the copilot doc if you
> touch this area.

## Cross-file deduplication

Users often upload overlapping date-range exports. A flat
`drop_duplicates()` on key columns is wrong: it would also collapse two
*genuine* identical trades on the same day (same ticker, same price, same
qty — happens with round-lot splits at a broker).

Algorithm (`_dedup()`, `utils.py:313-348`), tagging each row with its
source file index at parse time (`temp_main["_file_idx"] = file_idx`):

```python
key_cols = [date, ticker, type, qty, val, inst, source, sub_type, desc]  # whichever exist
grp = df.groupby(key_cols + ["_file_idx"]).size()  # count per (key, file)
max_per_group = grp.groupby(key_cols)["_n"].max()  # keep the max seen in any single file
# then keep only the first `max_per_group` occurrences of each key across the concatenated data
```

If file A has 2 identical rows and file B (an overlapping export) also has
2, the result keeps 2 — not 4, not 1. If only file A has 2, it still keeps 2.
Runs independently on `main_df` and `audit_df`. A dedup summary row is
appended to `stats_df` (`detected == "DEDUP"`) and surfaced in the sidebar
(`src/app.py:411-426`).

## Ticker cleaning — `clean_ticker()`

```python
re.search(r"([A-Z]{4}(?:11|34|33|31|[3-8]))(F)?", raw)
```

Handles B3's fractional-market suffix (`KLBN4F → KLBN4`). Two-digit suffixes
(`11`, `34`, `33`, `31`) are matched **before** the single-digit class
`[3-8]` in the regex alternation to avoid partial matches — e.g. `VERZ34`
must resolve to `VERZ34`, not `VERZ3`. Falls back to taking the first
whitespace/dash-delimited token if the regex doesn't match at all. `NaN`
input returns the literal string `"UNKNOWN"`.

`detect_asset_type()` (`utils.py:93-101`) then classifies by suffix only:
`11` → FII/ETF, `34/31/33` → BDR, `3-8` (excluding those already matched) →
Ação, else → Outro. This is a simple heuristic, not a lookup against B3's
actual instrument registry — see doc 09 for known misclassification edge
cases.

## Import stats & auditability

`stats_df` accumulates one row per file (`detected` = NEG/MOV) with counts
(`rows_buy`, `rows_sell`, `rows_earnings`, `rows_fees`, `rows_transfer`,
`rows_ignored`), plus the synthetic `(ALL)/DEDUP` summary row. Displayed
verbatim in the sidebar import expander so a user can sanity-check what was
parsed without opening the Audit tab.
