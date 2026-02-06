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
def get_exchange_rate():
    """Fetch USD/BRL FX rate.

    Falls back to a fixed value if Yahoo Finance is unavailable.
    """
    try:
        data = yf.download("USDBRL=X", period="1d", progress=False)
        return float(data["Close"].iloc[-1])
    except Exception:
        logger.exception("Failed to fetch USD/BRL exchange rate from Yahoo Finance. Using fallback rate.")
        return 5.45


def clean_ticker(text):
    if pd.isna(text): return "UNKNOWN"
    match = re.search(r'([A-Z]{4}[34567811]{1,2})', str(text).upper())
    return match.group(1) if match else str(text).split(' ')[0]


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
    all_data = []

    for file in uploaded_files:
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

            def map_earn(m):
                terms = ['RENDIMENTO', 'DIVIDENDO', 'JCP', 'JUROS SOBRE', 'AMORTIZA']
                return 'EARNINGS' if any(t in str(m).upper() for t in terms) else 'IGNORE'

            temp['type'] = df['Movimentação'].apply(map_earn)

            def classify_earning(m):
                m_upper = str(m).upper()
                if 'DIVIDENDO' in m_upper:
                    return 'Dividendo'
                if 'JUROS SOBRE' in m_upper or 'JCP' in m_upper:
                    return 'JCP'
                if 'AMORTIZA' in m_upper:
                    return 'Amortização'
                return 'Rendimento'

            temp['sub_type'] = df['Movimentação'].apply(classify_earning)
            temp['source'] = 'MOV'
            all_data.append(temp[temp['type'] == 'EARNINGS'])

    return pd.concat(all_data).sort_values(by='date', ascending=False) if all_data else pd.DataFrame()


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
