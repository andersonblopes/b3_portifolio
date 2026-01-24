from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

import utils
from langs import LANGUAGES

# --- PAGE CONFIG ---
st.set_page_config(page_title="B3 Portfolio Master", layout="wide", page_icon="💰")

# --- SESSION STATE ---
if 'raw_df' not in st.session_state:
    st.session_state['raw_df'] = None
if 'last_hash' not in st.session_state:
    st.session_state['last_hash'] = None

# --- SIDEBAR: LANGUAGE & CURRENCY ---
lang_choice = st.sidebar.selectbox("🌐 Language / Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]

st.sidebar.divider()
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
exchange_rate = utils.get_exchange_rate()

if currency_choice == "USD ($)":
    curr_symbol = "$"
    conv_factor = 1 / exchange_rate
    st.sidebar.caption(f"{texts['exchange_rate_msg']}: 1 USD = R$ {exchange_rate:.2f}")
else:
    curr_symbol = "R$"
    conv_factor = 1.0


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
        temp['type'] = df['Movimentação'].apply(utils.map_operation_type)
        temp['ticker'] = df['Produto'].apply(utils.clean_ticker)
        temp['raw_product'] = df['Produto']
        temp['quantity'] = pd.to_numeric(df['Quantidade'], errors='coerce').fillna(0)
        temp['operation_value'] = pd.to_numeric(df['Valor da Operação'], errors='coerce').fillna(0)
        all_data.append(temp.dropna(subset=['date', 'type']))
    return pd.concat(all_data).sort_values(by='date') if all_data else pd.DataFrame()


# --- UPLOAD LOGIC ---
st.sidebar.subheader(texts['settings'])
uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    incoming_df = load_and_process_files(uploaded_files)
    if not incoming_df.empty:
        new_hash = utils.get_data_hash(incoming_df)
        if new_hash == st.session_state['last_hash']:
            st.sidebar.warning(texts['warning_duplicate'])
        else:
            st.session_state['raw_df'] = incoming_df
            st.session_state['last_hash'] = new_hash

# --- DASHBOARD ---
if st.session_state['raw_df'] is not None:
    raw_df = st.session_state['raw_df']
    portfolio = utils.calculate_portfolio(raw_df, lang_choice)
    C = {k: texts[k] for k in texts if k.startswith('col_')}

    # 1. Market Data & Conversion
    prices = utils.fetch_market_prices(portfolio[C['col_ticker']].tolist(), lang_choice)

    portfolio[C['col_curr_price']] = (portfolio[C['col_ticker']].map(prices).fillna(
        portfolio[C['col_avg_price']])) * conv_factor
    portfolio[C['col_avg_price']] = portfolio[C['col_avg_price']] * conv_factor
    portfolio[C['col_total_cost']] = portfolio[C['col_total_cost']] * conv_factor
    portfolio[C['col_earnings']] = portfolio[C['col_earnings']] * conv_factor

    # 2. Calculations
    mkt_val_label = texts['market_value']
    portfolio[mkt_val_label] = portfolio[C['col_curr_price']] * portfolio[C['col_qty']]
    portfolio[C['col_pnl']] = portfolio[mkt_val_label] - portfolio[C['col_total_cost']]
    portfolio[C['col_yield']] = (portfolio[C['col_pnl']] / portfolio[C['col_total_cost']] * 100)

    # 3. KPIs
    t_cost = float(portfolio[C['col_total_cost']].to_numpy().sum())
    t_mkt = float(portfolio[mkt_val_label].to_numpy().sum())
    t_earn = float(portfolio[C['col_earnings']].to_numpy().sum())
    perf = ((t_mkt / t_cost) - 1) * 100 if t_cost > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(texts['total_invested'], f"{curr_symbol} {t_cost:,.2f}")
    c2.metric(texts['market_value'], f"{curr_symbol} {t_mkt:,.2f}", f"{perf:.2f}%")
    c3.metric(texts['gross_pnl'], f"{curr_symbol} {(t_mkt - t_cost):,.2f}")
    c4.metric(texts['total_earnings'], f"{curr_symbol} {t_earn:,.2f}")

    st.divider()

    # 4. Charts
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(texts['allocation_title'])
        fig_pie = px.pie(portfolio, values=mkt_val_label, names=C['col_category'], hole=0.4)
        fig_pie.update_traces(hovertemplate=f"{curr_symbol} %{{value:,.2f}}")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_b:
        st.subheader(texts['earnings_title'])
        fig_bar = px.bar(portfolio.sort_values(C['col_earnings'], ascending=False).head(10),
                         x=C['col_ticker'], y=C['col_earnings'])
        fig_bar.update_layout(yaxis_tickprefix=f"{curr_symbol} ", yaxis_tickformat=",.2f")
        st.plotly_chart(fig_bar, use_container_width=True)

    # 5. Dataframe
    st.subheader(texts['detailed_title'])
    st.dataframe(
        portfolio.style.format({
            C['col_avg_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_curr_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_total_cost']: f'{curr_symbol} ' + '{:.2f}',
            mkt_val_label: f'{curr_symbol} ' + '{:.2f}',
            C['col_pnl']: f'{curr_symbol} ' + '{:.2f}',
            C['col_earnings']: f'{curr_symbol} ' + '{:.2f}',
            C['col_qty']: '{:,.2f}', C['col_yield']: '{:.2f}%'
        }).map(lambda x: 'color: red' if str(x).startswith('-') else 'color: green',
               subset=[C['col_pnl'], C['col_yield']]),
        use_container_width=True, hide_index=True
    )

    # 6. Export
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        portfolio.to_excel(writer, index=False, sheet_name='Portfolio')
    st.download_button(texts['download_btn'], buffer, "Consolidated_Portfolio.xlsx")
else:
    st.info(texts['welcome_msg'])
