import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import utils
from langs import LANGUAGES

# --- PAGE CONFIG ---
st.set_page_config(page_title="B3 Portfolio Master", layout="wide", page_icon="📈")

# --- SESSION STATE ---
if 'raw_df' not in st.session_state: st.session_state['raw_df'] = None
if 'last_hash' not in st.session_state: st.session_state['last_hash'] = None

# --- SIDEBAR: GLOBAL CONTROLS ---
lang_choice = st.sidebar.selectbox("🌐 Language / Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]

st.sidebar.divider()
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
exchange_rate = utils.get_exchange_rate()

# --- IMPROVED FOREX DISPLAY ---
# Using metric for a cleaner, "Normal" look
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {exchange_rate:.2f}")

if currency_choice == "USD ($)":
    curr_symbol, conv_factor = "$", 1 / exchange_rate
else:
    curr_symbol, conv_factor = "R$", 1.0

st.sidebar.divider()
uploaded_files = st.sidebar.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

if uploaded_files:
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
    raw_df = st.session_state['raw_df'].copy()
    st.sidebar.success(texts['status_loaded'])

    # 1. Processing Logic
    portfolio = utils.calculate_portfolio(raw_df, lang_choice)
    C = {k: texts[k] for k in texts if k.startswith('col_')}
    prices_brl = utils.fetch_market_prices(portfolio[C['col_ticker']].tolist(), lang_choice)

    # Currency Conversion
    portfolio[C['col_curr_price']] = (portfolio[C['col_ticker']].map(prices_brl).fillna(
        portfolio[C['col_avg_price']])) * conv_factor
    portfolio[C['col_avg_price']] *= conv_factor
    portfolio[C['col_total_cost']] *= conv_factor
    portfolio[C['col_earnings']] *= conv_factor
    mkt_val_label = texts['market_value']
    portfolio[mkt_val_label] = portfolio[C['col_curr_price']] * portfolio[C['col_qty']]
    portfolio[C['col_pnl']] = portfolio[mkt_val_label] - portfolio[C['col_total_cost']]
    portfolio[C['col_yield']] = (portfolio[C['col_pnl']] / portfolio[C['col_total_cost']] * 100)

    # 2. Key Metrics
    t_cost, t_mkt = portfolio[C['col_total_cost']].sum(), portfolio[mkt_val_label].sum()
    t_earn = portfolio[C['col_earnings']].sum()
    perf = ((t_mkt / t_cost) - 1) * 100 if t_cost > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(texts['total_invested'], f"{curr_symbol} {t_cost:,.2f}")
    c2.metric(texts['market_value'], f"{curr_symbol} {t_mkt:,.2f}", f"{perf:.2f}%")
    c3.metric(texts['gross_pnl'], f"{curr_symbol} {(t_mkt - t_cost):,.2f}")
    c4.metric(texts['total_earnings'], f"{curr_symbol} {t_earn:,.2f}")

    st.divider()

    # 3. Evolution & Monthly Charts
    st.subheader(f"📈 {texts['evolution_title']}")
    evolution_df = utils.calculate_evolution(raw_df, conv_factor)
    fig_ev = px.area(evolution_df, x='date', y='flow')
    fig_ev.update_traces(line_color='#00FFAA', fillcolor='rgba(0, 255, 170, 0.1)')
    fig_ev.update_layout(height=350, yaxis_tickprefix=f"{curr_symbol} ", yaxis_title=None, xaxis_title=None)
    st.plotly_chart(fig_ev, use_container_width=True)

    st.subheader(f"💰 {texts['monthly_earnings_title']}")
    monthly_earn_df = utils.calculate_earnings_monthly(raw_df, conv_factor)
    if not monthly_earn_df.empty:
        fig_monthly = go.Figure()
        fig_monthly.add_trace(
            go.Bar(x=monthly_earn_df['month_year'], y=monthly_earn_df['operation_value'], name='Monthly',
                   marker_color='#FFD700'))
        avg_val = monthly_earn_df['operation_value'].mean()
        fig_monthly.add_trace(
            go.Scatter(x=monthly_earn_df['month_year'], y=[avg_val] * len(monthly_earn_df), name='Avg',
                       line=dict(color='white', dash='dash')))
        fig_monthly.update_layout(height=350, yaxis_tickprefix=f"{curr_symbol} ", showlegend=False, xaxis_title=None)
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.info("No income history found.")

    st.divider()

    # 4. Sunburst & Horizontal Bar
    col_pie, col_bar = st.columns([1, 1])
    with col_pie:
        st.subheader(texts['allocation_title'])
        fig_sun = px.sunburst(portfolio, path=[C['col_category'], C['col_ticker']], values=mkt_val_label)
        fig_sun.update_layout(height=450)
        st.plotly_chart(fig_sun, use_container_width=True)
    with col_bar:
        st.subheader(texts['earnings_title'])
        fig_bar = px.bar(portfolio.sort_values(C['col_earnings'], ascending=True).tail(10), y=C['col_ticker'],
                         x=C['col_earnings'], orientation='h', color=C['col_earnings'],
                         color_continuous_scale='Viridis')
        fig_bar.update_layout(height=450, xaxis_tickprefix=f"{curr_symbol} ", showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_bar, use_container_width=True)

    # 5. Data Table
    st.subheader(texts['detailed_title'])
    st.dataframe(
        portfolio.style.format({
            C['col_avg_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_curr_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_total_cost']: f'{curr_symbol} ' + '{:.2f}',
            mkt_val_label: f'{curr_symbol} ' + '{:.2f}',
            C['col_pnl']: f'{curr_symbol} ' + '{:.2f}',
            C['col_earnings']: f'{curr_symbol} ' + '{:.2f}',
            C['col_qty']: '{:,.2f}',
            C['col_yield']: '{:.2f}%'
        }).background_gradient(subset=[C['col_yield']], cmap='RdYlGn'),
        use_container_width=True, hide_index=True
    )

    if st.sidebar.button("🗑️ Reset Session"):
        st.session_state['raw_df'] = None
        st.session_state['last_hash'] = None
        st.rerun()
else:
    st.info(texts['welcome_msg'])
