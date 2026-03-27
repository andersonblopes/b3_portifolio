import logging
import os
import re
import warnings
import unicodedata

import pandas as pd
import streamlit as st
import yfinance as yf

logger = logging.getLogger(__name__)


def _norm(s: object) -> str:
    """Normalize text for robust comparisons (uppercase + strip accents)."""
    if s is None:
        return ""
    txt = str(s).strip().upper()
    return (
        unicodedata.normalize("NFKD", txt)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

# Some B3 exports trigger this common openpyxl warning; keep other warnings visible.
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="openpyxl",
    message=r".*Workbook contains no default style.*",
)

# some FIIs and stocks change their B3 ticker code over time (renaming, fund mergers, etc.).
# each entry maps the old code (as it appears in B3 exports) to a dict with:
#   "new"  — the current active ticker on Yahoo Finance
#   "note" — human-readable explanation shown in the Ticker Changes tab
TICKER_REMAP: dict[str, dict] = {
    "BRIT3":  {"new": "BRST3",  "note": "Renamed after incorporation by Brisanet Serviços (Nov 2024)"},
    "CVBI11": {"new": "PCIP11", "note": "Fund renamed on B3 (Sep 2025)"},
    "MALL11": {"new": "PMLL11", "note": "Fund renamed on B3 (Jul 2025)"},
    "RVBI11": {"new": "PSEC11", "note": "Fund renamed on B3 (Oct 2025)"},
}

# tickers that have been delisted or wound down with no successor and no tradeable value.
# positions in these are excluded from portfolio calculations to avoid distorting totals.
# maps ticker → reason string shown in the Ticker Changes tab.
DISCONTINUED_TICKERS: dict[str, str] = {
    "LSPA11": "Leste Riva Equity — fund in wind-down, last trade Dec 2024",
}


@st.cache_data(ttl=3600)
def get_exchange_rate(base_currency: str = "USD"):
    """Fetch FX rate for base_currency/BRL via yfinance.

    Falls back to a fixed value when yfinance is unavailable.
    """
    base = str(base_currency).upper().strip()
    fallback = {"USD": 5.45, "EUR": 5.90}.get(base, 5.45)
    try:
        fx_ticker = f"{base}BRL=X"
        data = yf.download(fx_ticker, period="5d", progress=False, auto_adjust=True)
        return float(data["Close"].dropna().iloc[-1].item())
    except Exception:
        logger.exception("Failed to fetch %s/BRL from yfinance. Using fallback.", base)
        return float(fallback)


def clean_ticker(text):
    """Normalize B3 tickers.

    Handles cases like fractional market tickers (e.g., KLBN4F -> KLBN4).
    """
    if pd.isna(text):
        return "UNKNOWN"

    raw = str(text).upper().strip()

    # two-digit suffixes must come before the single-digit [3-8] to prevent
    # partial matches (e.g. VERZ34 must not be captured as VERZ3)
    match = re.search(r"([A-Z]{4}(?:11|34|33|31|[3-8]))(F)?", raw)
    if match:
        ticker = match.group(1)
        return ticker

    # Fallback: take the first token before a space/dash
    return raw.split(" ")[0].split("-")[0]


def detect_asset_type(ticker):
    t = str(ticker).upper()
    if t.endswith('11'):
        return 'FII/ETF'
    elif any(t.endswith(s) for s in ['34', '31', '33']):
        return 'BDR'
    elif any(t.endswith(s) for s in ['3', '4', '5', '6', '7', '8', '2']):
        return 'Ação'
    return 'Outro'


def load_and_process_files(uploaded_files):
    """Load B3 exported XLSX statements.

    Returns:
        main_df: normalized rows used by the current dashboards (NEG BUY/SELL + MOV EARNINGS)
        stats_df: per-file parsing summary
        audit_df: extra rows for auditing (MOV FEES/TRANSFER/IGNORE + NEG IGNORE)
    """

    all_data = []
    stats_rows = []
    audit_rows = []

    for file in uploaded_files:
        file_name = getattr(file, "name", "uploaded.xlsx")
        df = pd.read_excel(file)

        # --- Trading / Negotiation statement ---
        if 'Data do Negócio' in df.columns:
            temp = pd.DataFrame()
            temp['date'] = pd.to_datetime(df['Data do Negócio'], dayfirst=True, errors='coerce')
            temp['ticker'] = df['Código de Negociação'].apply(clean_ticker)
            temp['qty'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
            temp['val'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
            temp['inst'] = df['Instituição'].fillna('Desconhecida')

            # Explicit mapping to avoid treating unknown types as SELL.
            movement = df['Tipo de Movimentação'].astype(str).str.upper()
            temp['type'] = 'IGNORE'
            temp.loc[movement.str.contains('COMPRA', na=False), 'type'] = 'BUY'
            temp.loc[movement.str.contains('VENDA', na=False), 'type'] = 'SELL'

            temp['source'] = 'NEG'
            temp['desc'] = df['Tipo de Movimentação'].astype(str)

            stats_rows.append(
                {
                    'file': file_name,
                    'detected': 'NEG',
                    'rows_total': int(len(temp)),
                    'rows_buy': int((temp['type'] == 'BUY').sum()),
                    'rows_sell': int((temp['type'] == 'SELL').sum()),
                    'rows_earnings': 0,
                    'rows_fees': 0,
                    'rows_transfer': 0,
                    'rows_ignored': int((temp['type'] == 'IGNORE').sum()),
                }
            )

            audit_rows.append(temp[temp['type'] == 'IGNORE'])
            all_data.append(temp[temp['type'] != 'IGNORE'])
            continue

        # --- Movements statement ---
        if 'Data' not in df.columns:
            # Some exports have a header offset; try to detect the row that contains "Data".
            for i, row in df.iterrows():
                if 'Data' in [str(v) for v in row.values]:
                    df.columns = df.iloc[i]
                    df = df.iloc[i + 1:].reset_index(drop=True)
                    break

        if 'Movimentação' in df.columns:
            temp = pd.DataFrame()
            temp['date'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            temp['ticker'] = df['Produto'].apply(clean_ticker)
            temp['inst'] = df['Instituição'].fillna('Desconhecida')

            # Apply sign based on Entrada/Saída (Credito/Debito) when available.
            sign = 1
            if 'Entrada/Saída' in df.columns:
                es = df['Entrada/Saída'].map(_norm)
                # Handles "Débito" / "Debito" / "DEBIT" variations
                sign = es.map(lambda x: -1 if 'DEB' in x else 1).fillna(1)

            temp['val'] = pd.to_numeric(df['Valor da Operação'], errors='coerce').fillna(0) * sign
            qty_col = df['Quantidade'] if 'Quantidade' in df.columns else 0
            temp['qty'] = pd.to_numeric(qty_col, errors='coerce').fillna(0)
            temp['desc'] = df['Movimentação'].astype(str)

            def map_mov(m):
                m_upper = _norm(m)

                earn_terms = ['RENDIMENTO', 'DIVIDENDO', 'JCP', 'JUROS SOBRE', 'AMORTIZA',
                              'EMPRESTIMO', 'LEILAO DE FRACAO', 'REEMBOLSO']
                fee_terms = ['TAXA', 'TARIFA', 'IR', 'IOF']
                transfer_terms = ['TRANSFER', 'LIQUIDA']

                if any(t in m_upper for t in earn_terms):
                    return 'EARNINGS'
                if any(t in m_upper for t in fee_terms):
                    return 'FEES'
                if any(t in m_upper for t in transfer_terms):
                    return 'TRANSFER'
                # reverse split: B3 records the new consolidated qty as a credit
                if 'GRUPAMENTO' in m_upper:
                    return 'REVERSE_SPLIT'
                # split / bonus shares: additional shares credited at zero cost
                if 'DESDOBRAMENTO' in m_upper or 'BONIFICACAO' in m_upper:
                    return 'SPLIT'
                # fractional shares removed by the custodian (proceeds come via leilão)
                if 'FRACAO EM ATIVOS' in m_upper:
                    return 'SELL'
                return 'IGNORE'

            temp['type'] = df['Movimentação'].apply(map_mov)

            def classify_earning(m):
                m_upper = _norm(m)
                if 'DIVIDENDO' in m_upper:
                    return 'Dividend'
                if 'JUROS SOBRE' in m_upper or 'JCP' in m_upper:
                    return 'JCP'
                if 'AMORTIZA' in m_upper:
                    return 'Amortization'
                return 'Income'

            temp['sub_type'] = df['Movimentação'].apply(classify_earning)
            temp['source'] = 'MOV'

            stats_rows.append(
                {
                    'file': file_name,
                    'detected': 'MOV',
                    'rows_total': int(len(temp)),
                    'rows_buy': 0,
                    'rows_sell': 0,
                    'rows_earnings': int((temp['type'] == 'EARNINGS').sum()),
                    'rows_fees': int((temp['type'] == 'FEES').sum()),
                    'rows_transfer': int((temp['type'] == 'TRANSFER').sum()),
                    'rows_ignored': int((temp['type'] == 'IGNORE').sum()),
                }
            )

            # corporate actions (splits, reverse splits, fractional debits) must flow into
            # main_df alongside earnings so calculate_portfolio can adjust share counts.
            _main_types = {'EARNINGS', 'SPLIT', 'REVERSE_SPLIT', 'SELL'}
            all_data.append(temp[temp['type'].isin(_main_types)])

            audit_rows.append(temp[~temp['type'].isin(_main_types)])

    main_df = pd.concat(all_data).sort_values(by='date', ascending=False) if all_data else pd.DataFrame()
    stats_df = pd.DataFrame(stats_rows).sort_values(['file', 'detected']) if stats_rows else None
    audit_df = pd.concat(audit_rows).sort_values(by='date', ascending=False) if audit_rows else pd.DataFrame()

    # --- Deduplication across multiple uploads (common when importing overlapping periods) ---
    def _dedup(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
        if df is None or df.empty:
            return df, 0, 0
        before = int(len(df))

        cols = [c for c in ['date', 'ticker', 'type', 'qty', 'val', 'inst', 'source', 'sub_type', 'desc'] if c in df.columns]
        out = df.drop_duplicates(subset=cols, keep='first')
        after = int(len(out))
        return out, before, after

    main_df, main_before, main_after = _dedup(main_df)
    audit_df, audit_before, audit_after = _dedup(audit_df)

    # Append a small summary row to the import stats (non-breaking for the UI).
    if stats_df is None:
        stats_df = pd.DataFrame()

    if (main_before and main_after) or (audit_before and audit_after):
        stats_df = pd.concat(
            [
                stats_df,
                pd.DataFrame(
                    [
                        {
                            'file': '(ALL)',
                            'detected': 'DEDUP',
                            'rows_total': main_before,
                            'rows_buy': None,
                            'rows_sell': None,
                            'rows_earnings': None,
                            'rows_fees': None,
                            'rows_transfer': None,
                            'rows_ignored': None,
                            'dedup_removed_main': main_before - main_after,
                            'dedup_removed_audit': audit_before - audit_after,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return main_df, stats_df, audit_df


def calculate_portfolio(df, split_history=None):
    """Compute current positions and cost basis for each ticker.

    split_history: optional dict from fetch_split_history().
    When provided, yfinance split events are injected for tickers that have
    no MOV-sourced corporate action rows (Grupamento / Desdobramento / Bonificação).
    This ensures correct qty/cost even when only a NEG file was uploaded.
    """
    summary = []

    for ticker, data in df.groupby('ticker'):
        if ticker in DISCONTINUED_TICKERS:
            logger.debug("Skipping discontinued ticker %s.", ticker)
            continue
        data = data.sort_values('date').copy()
        qty, cost, earnings = 0.0, 0.0, 0.0

        # only inject yfinance splits when the MOV file didn't already supply them,
        # to avoid double-applying the same corporate action from two sources.
        has_mov_splits = data['type'].isin(['SPLIT', 'REVERSE_SPLIT']).any()

        if not has_mov_splits and split_history and ticker in split_history:
            synthetic = []
            for ev in split_history[ticker]:
                split_type = 'SPLIT' if ev['ratio'] >= 1.0 else 'REVERSE_SPLIT'
                synthetic.append({
                    'date': ev['date'],
                    'ticker': ticker,
                    'type': split_type,
                    # store ratio in the qty field; identified by source='yfinance_split'
                    'qty': ev['ratio'],
                    'val': 0.0,
                    'source': 'yfinance_split',
                })
            if synthetic:
                extra = pd.DataFrame(synthetic)
                for col in data.columns:
                    if col not in extra.columns:
                        extra[col] = None
                data = pd.concat([data, extra], ignore_index=True).sort_values('date')

        for _, row in data.iterrows():
            if row['type'] == 'BUY':
                qty += float(row.get('qty', 0) or 0)
                cost += float(row.get('val', 0) or 0)

            elif row['type'] == 'SELL':
                sell_qty = float(row.get('qty', 0) or 0)
                if qty <= 0:
                    continue

                if sell_qty > qty:
                    # Guardrail: avoid negative quantities if statement is inconsistent.
                    logger.warning(
                        "Sell quantity greater than current position for %s: sell=%s, held=%s. Clamping.",
                        ticker,
                        sell_qty,
                        qty,
                    )
                    sell_qty = qty

                avg_p = cost / qty if qty > 0 else 0
                qty -= sell_qty
                cost = qty * avg_p

            elif row['type'] == 'EARNINGS':
                earnings += float(row.get('val', 0) or 0)

            elif row['type'] == 'SPLIT':
                if str(row.get('source', '')) == 'yfinance_split':
                    # ratio stored in qty: multiply current position
                    qty = qty * float(row.get('qty', 1.0) or 1.0)
                else:
                    # MOV-sourced: qty column holds the number of new shares credited
                    qty += float(row.get('qty', 0) or 0)

            elif row['type'] == 'REVERSE_SPLIT':
                if str(row.get('source', '')) == 'yfinance_split':
                    # ratio stored in qty: multiply current position (ratio < 1 so qty shrinks)
                    qty = qty * float(row.get('qty', 1.0) or 1.0)
                else:
                    # MOV-sourced: qty column holds the exact post-grupamento shares
                    new_qty = float(row.get('qty', 0) or 0)
                    if new_qty > 0:
                        qty = new_qty

        if round(qty, 4) > 0 or earnings != 0:
            summary.append(
                {
                    'ticker': ticker,
                    'qty': qty,
                    'avg_price': cost / qty if qty > 0 else 0,
                    'total_cost': cost,
                    'earnings': earnings,
                    'asset_type': detect_asset_type(ticker),
                }
            )

    return pd.DataFrame(summary)


@st.cache_data(ttl=86400)
def fetch_split_history(tickers: tuple) -> dict:
    """Fetch split/reverse-split history from yfinance for every ticker.

    Uses a 24-hour TTL because splits are rare and don't change intraday.
    Accepts a tuple (not list) so st.cache_data can hash the argument.

    Returns {ticker: [{'date': pd.Timestamp, 'ratio': float}, ...]} where
    ratio > 1 is a forward split (more shares) and ratio < 1 is a reverse split.
    """
    result = {}
    for t in tickers:
        sa = f"{TICKER_REMAP[t]['new'] if t in TICKER_REMAP else t}.SA"
        try:
            splits = yf.Ticker(sa).splits
            if splits is not None and not splits.empty:
                events = []
                for dt, ratio in splits.items():
                    ts = pd.Timestamp(dt)
                    if ts.tzinfo is not None:
                        ts = ts.tz_localize(None)
                    events.append({"date": ts, "ratio": float(ratio)})
                result[t] = sorted(events, key=lambda x: x["date"])
        except Exception:
            logger.debug("Could not fetch split history for %s.", sa)
    return result


@st.cache_data(ttl=3600)
def fetch_market_prices(tickers):
    """Fetch latest prices for B3 tickers via yfinance (.SA suffix).

    Uses period='1mo' so that prices remain available through multi-day
    holiday periods (e.g. Easter week). dropna().iloc[-1] always picks
    the most recent trading day.

    Returns a dict: {ticker: {"p": float|None, "live": bool}}
    """
    if not tickers:
        return {}
    prices = {t: {"p": None, "live": False} for t in tickers}
    try:
        # resolve any renamed tickers before querying Yahoo Finance
        sa_tickers = [f"{TICKER_REMAP[t]['new'] if t in TICKER_REMAP else t}.SA" for t in tickers]
        data = yf.download(sa_tickers, period="1mo", progress=False, group_by="ticker", auto_adjust=True)
        for t in tickers:
            try:
                s = f"{TICKER_REMAP[t]['new'] if t in TICKER_REMAP else t}.SA"
                close = data[s]["Close"] if len(tickers) > 1 else data["Close"]
                price = close.dropna().iloc[-1].item()
                prices[t] = {"p": price, "live": True}
            except Exception:
                logger.debug("No yfinance price for %s.", t)
    except Exception:
        logger.exception("yfinance batch download failed.")
    return prices


def analyze_position(ticker, qty, avg_price, total_cost, current_price, earnings, asset_type):
    """Return a structured position analysis with actionable recommendations.

    Strategies applied:
    - Gain scenario: trailing stop, partial-profit targets, DCA top-up sizing
    - Loss scenario: DCA to reduce average, break-even study, max safe add-on

    Returns a dict with keys:
        scenario       : 'gain' | 'loss' | 'flat'
        yield_pct      : float  (unrealised return %)
        breakeven      : float  (price needed to recover total cost incl. earnings)
        trailing_stop  : float
        targets        : list of {'label': str, 'price': float, 'qty_to_sell': float}
        dca            : list of {'label': str, 'add_qty': float, 'add_price': float,
                                  'new_avg': float, 'new_total': float} | None
        notes          : list of str (contextual observations)
    """
    if current_price <= 0 or qty <= 0:
        return None

    yield_pct = (current_price - avg_price) / avg_price * 100
    market_value = current_price * qty

    # effective breakeven accounting for earnings already received
    effective_cost = max(total_cost - earnings, 0)
    breakeven_price = effective_cost / qty if qty > 0 else avg_price

    notes = []
    targets = []
    dca = None

    # trailing stop levels: tighter for FIIs (less volatile), wider for stocks
    # rule: protect at least the cost basis; floor at avg_price
    if asset_type in ('FII/ETF',):
        trail_pct = 0.08  # 8% trail for FIIs
    elif asset_type == 'BDR':
        trail_pct = 0.12  # 12% for BDRs (FX exposure)
    else:
        trail_pct = 0.15  # 15% for stocks

    trailing_stop = max(current_price * (1 - trail_pct), breakeven_price)

    if yield_pct >= 0:
        scenario = 'gain' if yield_pct > 0.5 else 'flat'

        # partial profit targets — classic pyramid scale-out
        target_levels = [
            ('target_20pct',    avg_price * 1.20, 0.25),   # sell 25% at +20%
            ('target_50pct',    avg_price * 1.50, 0.33),   # sell 33% at +50%
            ('target_double',   avg_price * 2.00, 0.50),   # sell 50% at 2×
        ]
        for label, price, frac in target_levels:
            if price >= current_price:  # only show future targets
                targets.append({
                    'label': label,
                    'price': round(price, 2),
                    'qty_to_sell': round(qty * frac, 0),
                })

        # if already above +20%, suggest a top-up only if still below a base target
        if yield_pct < 20:
            # room to add: buy up to 50% more at current to keep avg cost reasonable
            add_qty = round(qty * 0.50, 0)
            new_qty = qty + add_qty
            new_avg = (total_cost + add_qty * current_price) / new_qty
            dca = [{
                'label': 'dca_topup',
                'add_qty': add_qty,
                'add_price': current_price,
                'new_avg': round(new_avg, 2),
                'new_total': round(total_cost + add_qty * current_price, 2),
            }]

        if yield_pct > 50:
            notes.append('note_high_gain')
        if earnings / total_cost >= 0.05 if total_cost > 0 else False:
            notes.append('note_earnings_offset')

    else:
        scenario = 'loss'

        # DCA strategy: calculate how many shares to buy at each price level
        # to move the average cost to a meaningful target
        dca_levels = [
            # target: midpoint between current price and original avg (50% recovery)
            ('dca_50pct_recovery', (avg_price + current_price) / 2),
            # target: 5% above current price (minimal viable recovery target)
            ('dca_5pct_above',     current_price * 1.05),
        ]
        dca = []
        for label, target_avg in dca_levels:
            # add_qty = (total_cost - target_avg * qty) / (target_avg - current_price)
            # valid only when target_avg > current_price
            if target_avg <= current_price or target_avg >= avg_price:
                continue
            add_qty = (total_cost - target_avg * qty) / (target_avg - current_price)
            if add_qty <= 0:
                continue
            add_qty = round(add_qty, 0)
            new_qty = qty + add_qty
            new_avg = (total_cost + add_qty * current_price) / new_qty
            dca.append({
                'label': label,
                'add_qty': add_qty,
                'add_price': current_price,
                'new_avg': round(new_avg, 2),
                'new_total': round(total_cost + add_qty * current_price, 2),
            })

        if abs(yield_pct) > 30:
            notes.append('note_deep_loss')
        if earnings > 0:
            notes.append('note_earnings_offset')

    return {
        'scenario': scenario,
        'yield_pct': round(yield_pct, 2),
        'breakeven': round(breakeven_price, 2),
        'trailing_stop': round(trailing_stop, 2),
        'targets': targets,
        'dca': dca or [],
        'notes': notes,
    }
