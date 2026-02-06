import logging
import re
import warnings

import pandas as pd
import streamlit as st
import yfinance as yf

logger = logging.getLogger(__name__)

# Some B3 exports trigger this common openpyxl warning; keep other warnings visible.
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="openpyxl",
    message=r".*Workbook contains no default style.*",
)


@st.cache_data(ttl=3600)
def get_exchange_rate(base_currency: str = "USD"):
    """Fetch FX rate for base_currency/BRL.

    Examples:
      - USD/BRL: base_currency="USD" -> ticker "USDBRL=X"
      - EUR/BRL: base_currency="EUR" -> ticker "EURBRL=X"

    Falls back to a fixed value if Yahoo Finance is unavailable.
    """
    base = str(base_currency).upper().strip()

    # Simple fallbacks (used only when Yahoo is unavailable)
    fallback = {"USD": 5.45, "EUR": 5.90}.get(base, 5.45)

    try:
        data = yf.download(f"{base}BRL=X", period="1d", progress=False)
        close = data["Close"].dropna()
        return float(close.iloc[-1])
    except Exception:
        logger.exception(
            "Failed to fetch %s/BRL exchange rate from Yahoo Finance. Using fallback rate.",
            base,
        )
        return float(fallback)


def clean_ticker(text):
    """Normalize B3 tickers.

    Handles cases like fractional market tickers (e.g., KLBN4F -> KLBN4).
    """
    if pd.isna(text):
        return "UNKNOWN"

    raw = str(text).upper().strip()

    # Capture common B3 patterns and allow an optional trailing 'F' (mercado fracionário)
    match = re.search(r"([A-Z]{4}(?:11|[3-8]|3[134]|33|34))(F)?", raw)
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
    elif any(t.endswith(s) for s in ['3', '4', '5', '6']):
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
                es = df['Entrada/Saída'].astype(str).str.upper()
                sign = es.map(lambda x: -1 if 'DEB' in x else 1).fillna(1)

            temp['val'] = pd.to_numeric(df['Valor da Operação'], errors='coerce').fillna(0) * sign
            temp['desc'] = df['Movimentação'].astype(str)

            def map_mov(m):
                m_upper = str(m).upper()

                earn_terms = ['RENDIMENTO', 'DIVIDENDO', 'JCP', 'JUROS SOBRE', 'AMORTIZA']
                fee_terms = ['TAXA', 'TARIFA', 'IR', 'IOF']
                transfer_terms = ['TRANSFER', 'LIQUIDA']

                if any(t in m_upper for t in earn_terms):
                    return 'EARNINGS'
                if any(t in m_upper for t in fee_terms):
                    return 'FEES'
                if any(t in m_upper for t in transfer_terms):
                    return 'TRANSFER'
                return 'IGNORE'

            temp['type'] = df['Movimentação'].apply(map_mov)

            def classify_earning(m):
                m_upper = str(m).upper()
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

            # Keep only earnings in the main dataset for now (so existing views remain consistent).
            all_data.append(temp[temp['type'] == 'EARNINGS'])

            audit_rows.append(temp[temp['type'] != 'EARNINGS'])

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


def calculate_portfolio(df):
    summary = []

    for ticker, data in df.groupby('ticker'):
        data = data.sort_values('date')
        qty, cost, earnings = 0.0, 0.0, 0.0

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


@st.cache_data(ttl=3600)
def fetch_market_prices(tickers):
    if not tickers: return {}
    prices = {}
    try:
        data = yf.download([f"{t}.SA" for t in tickers], period="1d", progress=False, group_by='ticker')
        for t in tickers:
            try:
                s = f"{t}.SA"
                price = data[s]['Close'].iloc[-1].item() if len(tickers) > 1 else data['Close'].iloc[-1].item()
                prices[t] = {"p": price, "live": True}
            except:
                prices[t] = {"p": None, "live": False}
    except:
        for t in tickers: prices[t] = {"p": None, "live": False}
    return prices
