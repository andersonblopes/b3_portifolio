import hashlib
import re

import pandas as pd
import streamlit as st
import yfinance as yf

from langs import LANGUAGES


def get_data_hash(df):
    return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()


@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        data = yf.download("USDBRL=X", period="1d", progress=False)
        return float(data['Close'].iloc[-1])
    except:
        return 5.45


def clean_ticker(text):
    if pd.isna(text): return "UNKNOWN"
    match = re.search(r'([A-Z]{4}[34567811]{1,2})', str(text).upper())
    return match.group(1) if match else str(text).split(' ')[0]


def map_operation_type(text):
    text = str(text).upper()
    if any(term in text for term in ['COMPRA', 'BUY', 'LIQUIDAÇÃO']): return 'BUY'
    if any(term in text for term in ['VENDA', 'SELL', 'RESGATE']): return 'SELL'
    if any(term in text for term in ['RENDIMENTO', 'DIVIDEND', 'JCP', 'PROVENTO']): return 'EARNINGS'
    return None


@st.cache_data
def load_and_process_files(uploaded_files):
    all_data = []
    for file in uploaded_files:
        file.seek(0)
        df = pd.read_excel(file)
        if 'Data' not in df.columns:
            for i, row in df.iterrows():
                if 'Data' in [str(v) for v in row.values]:
                    df.columns = df.iloc[i];
                    df = df.iloc[i + 1:].reset_index(drop=True);
                    break
        temp = pd.DataFrame()
        temp['date'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        temp['type'] = df['Movimentação'].apply(map_operation_type)
        temp['ticker'] = df['Produto'].apply(clean_ticker)
        temp['raw_product'] = df['Produto']
        temp['quantity'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
        temp['operation_value'] = pd.to_numeric(df['Valor da Operação'], errors='coerce').fillna(0)
        all_data.append(temp.dropna(subset=['date', 'type']))
    return pd.concat(all_data).sort_values(by='date') if all_data else pd.DataFrame()


def get_asset_category(ticker, product_name, lang_code):
    t, p = str(ticker).upper(), str(product_name).upper()
    trans = LANGUAGES[lang_code]
    if 'TESOURO' in p or 'TREASURY' in p: return trans['cat_treasury']
    if t.endswith('11'): return trans['cat_reits']
    if any(t.endswith(s) for s in ['3', '4', '5', '6']): return trans['cat_stocks']
    return trans['cat_others']


def calculate_portfolio(df, lang_code):
    summary = []
    trans = LANGUAGES[lang_code]
    for asset in df['ticker'].unique():
        asset_data = df[df['ticker'] == asset].sort_values('date')
        qty, cost, earnings = 0.0, 0.0, 0.0
        for _, row in asset_data.iterrows():
            if row['type'] == 'BUY':
                qty += float(row['quantity']);
                cost += float(row['operation_value'])
            elif row['type'] == 'SELL' and qty > 0:
                avg_p = cost / qty;
                qty -= float(row['quantity']);
                cost = qty * avg_p
            elif row['type'] == 'EARNINGS':
                earnings += float(row['operation_value'])
        if round(qty, 2) > 0:
            summary.append({
                trans['col_ticker']: asset,
                trans['col_category']: get_asset_category(asset, asset_data['raw_product'].iloc[-1], lang_code),
                trans['col_qty']: round(qty, 2),
                trans['col_avg_price']: cost / qty,
                trans['col_total_cost']: cost,
                trans['col_earnings']: earnings
            })
    return pd.DataFrame(summary)


def calculate_evolution(df, conv_factor):
    df_ev = df.copy()
    df_ev['flow'] = df_ev.apply(
        lambda r: r['operation_value'] if r['type'] == 'BUY' else (-r['operation_value'] if r['type'] == 'SELL' else 0),
        axis=1)
    ev = df_ev.groupby('date')['flow'].sum().cumsum().reset_index()
    ev['flow'] *= conv_factor
    return ev


def calculate_earnings_monthly(df, conv_factor):
    df_earn = df[df['type'] == 'EARNINGS'].copy()
    if df_earn.empty: return pd.DataFrame(columns=['month_year', 'operation_value'])
    df_earn['month_year'] = df_earn['date'].dt.strftime('%Y-%m')
    monthly = df_earn.groupby('month_year')['operation_value'].sum().reset_index()
    monthly['operation_value'] *= conv_factor
    return monthly


@st.cache_data(ttl=3600)
def fetch_market_prices(tickers, lang_code):
    prices = {}
    msg = LANGUAGES[lang_code]['fetching_prices']
    p_bar = st.progress(0, text=msg)
    for i, t in enumerate(tickers):
        try:
            data = yf.download(f"{t}.SA", period="1d", progress=False, threads=False)
            prices[t] = float(data['Close'].iloc[-1]) if not data.empty else None
        except:
            prices[t] = None
        p_bar.progress((i + 1) / len(tickers))
    p_bar.empty()
    return prices
