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

# --- SIDEBAR CONTROLS ---
lang_choice = st.sidebar.selectbox("🌐 Language / Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]

st.sidebar.divider()
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
exchange_rate = utils.get_exchange_rate()

if currency_choice == "USD ($)":
    curr_symbol, conv_factor = "$", 1 / exchange_rate
    st.sidebar.caption(f"{texts['exchange_rate_msg']}: 1 USD = R$ {exchange_rate:.2f}")
else:
    curr_symbol, conv_factor = "R$", 1.0

# --- UPLOAD LOGIC ---
st.sidebar.subheader(texts['settings'])
uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
    # CHAMADA CORRETA: utils.load_and_process_files
    incoming_df = utils.load_and_process_files(uploaded_files)

    if not incoming_df.empty:
        new_hash = utils.get_data_hash(incoming_df)
        if new_hash != st.session_state['last_hash']:
            st.session_state['raw_df'] = incoming_df
            st.session_state['last_hash'] = new_hash
        else:
            st.sidebar.info(texts['warning_duplicate'])

# --- DASHBOARD RENDERING ---
if st.session_state['raw_df'] is not None:
    st.sidebar.success(texts['status_loaded'])

    # Work on a copy to avoid corrupting session data during currency toggle
    raw_df = st.session_state['raw_df'].copy()

    portfolio = utils.calculate_portfolio(raw_df, lang_choice)
    C = {k: texts[k] for k in texts if k.startswith('col_')}

    # Market Data
    prices_brl = utils.fetch_market_prices(portfolio[C['col_ticker']].tolist(), lang_choice)

    # Apply Conversions
    portfolio[C['col_curr_price']] = (portfolio[C['col_ticker']].map(prices_brl).fillna(
        portfolio[C['col_avg_price']])) * conv_factor
    portfolio[C['col_avg_price']] *= conv_factor
    portfolio[C['col_total_cost']] *= conv_factor
    portfolio[C['col_earnings']] *= conv_factor

    mkt_val_label = texts['market_value']
    portfolio[mkt_val_label] = portfolio[C['col_curr_price']] * portfolio[C['col_qty']]
    portfolio[C['col_pnl']] = portfolio[mkt_val_label] - portfolio[C['col_total_cost']]
    portfolio[C['col_yield']] = (portfolio[C['col_pnl']] / portfolio[C['col_total_cost']] * 100)

    # Metrics
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

    # Visuals
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

    st.subheader(texts['detailed_title'])
    st.dataframe(
        portfolio.style.format({
            C['col_avg_price']: f'{curr_symbol} ' + '{:.2f}', C['col_curr_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_total_cost']: f'{curr_symbol} ' + '{:.2f}', mkt_val_label: f'{curr_symbol} ' + '{:.2f}',
            C['col_pnl']: f'{curr_symbol} ' + '{:.2f}', C['col_earnings']: f'{curr_symbol} ' + '{:.2f}',
            C['col_qty']: '{:,.2f}', C['col_yield']: '{:.2f}%'
        }).map(lambda x: 'color: red' if str(x).startswith('-') else 'color: green',
               subset=[C['col_pnl'], C['col_yield']]),
        use_container_width=True, hide_index=True
    )

    # Reset Data Button
    if st.sidebar.button("🗑️ Reset Session"):
        st.session_state['raw_df'] = None
        st.session_state['last_hash'] = None
        st.rerun()

else:
    st.info(texts['welcome_msg'])
