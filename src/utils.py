import re

import pandas as pd
import streamlit as st
import yfinance as yf


def clean_ticker(text):
    if pd.isna(text): return "UNKNOWN"
    match = re.search(r'([A-Z]{4}[34567811]{1,2})', str(text).upper())
    return match.group(1) if match else str(text).split(' ')[0]


def get_asset_category(ticker, product_name):
    t, p = str(ticker).upper(), str(product_name).upper()
    if 'TESOURO' in p or 'TREASURY' in p: return 'Treasury Bonds'
    if t.endswith('11') and ('FII' in p or 'REAL ESTATE' in p or 'IMOBILIARIO' in p): return 'REITs (FIIs)'
    if any(t.endswith(s) for s in ['31', '32', '33', '34']): return 'BDRs'
    if any(t.endswith(s) for s in ['3', '4', '5', '6']): return 'Stocks'
    if any(x in p for x in ['CDB', 'LCI', 'LCA', 'DEBENTURE', 'CRI', 'CRA']): return 'Fixed Income'
    return 'ETFs/Units'


def map_operation_type(text):
    text = str(text).upper()
    if any(term in text for term in ['COMPRA', 'BUY', 'LIQUIDAÇÃO']): return 'BUY'
    if any(term in text for term in ['VENDA', 'SELL', 'RESGATE']): return 'SELL'
    if any(term in text for term in ['RENDIMENTO', 'DIVIDEND', 'JCP', 'INTEREST', 'PROVENTO']): return 'EARNINGS'
    return None


def calculate_portfolio(df):
    summary = []
    for asset in df['ticker'].unique():
        asset_data = df[df['ticker'] == asset].sort_values('date')
        qty, cost, earnings = 0.0, 0.0, 0.0

        for _, row in asset_data.iterrows():
            if row['type'] == 'BUY':
                qty += float(row['quantity'])
                cost += float(row['operation_value'])
            elif row['type'] == 'SELL' and qty > 0:
                avg_price = cost / qty
                qty -= float(row['quantity'])
                cost = qty * avg_price
            elif row['type'] == 'EARNINGS':
                earnings += float(row['operation_value'])

        if round(qty, 2) > 0:
            summary.append({
                'Ticker': asset,
                'Category': get_asset_category(asset, asset_data['raw_product'].iloc[-1]),
                'Quantity': round(qty, 2),
                'Avg Price': cost / qty,
                'Total Invested': cost,
                'Earnings Received': earnings
            })
    return pd.DataFrame(summary)


@st.cache_data(ttl=3600)
def fetch_market_prices(tickers):
    prices = {}
    p_bar = st.progress(0, text="Fetching market prices...")
    for i, t in enumerate(tickers):
        try:
            data = yf.download(f"{t}.SA", period="1d", progress=False, threads=False)
            prices[t] = float(data['Close'].iloc[-1]) if not data.empty else None
        except:
            prices[t] = None
        p_bar.progress((i + 1) / len(tickers))
    p_bar.empty()
    return prices
