import streamlit as st

import charts
import utils
from langs import LANGUAGES

# --- PAGE CONFIG ---
st.set_page_config(page_title="B3 Portfolio Master", layout="wide", page_icon="📈")

# --- INITIALIZE SESSION STATE ---
if 'raw_df' not in st.session_state:
    st.session_state['raw_df'] = None
if 'last_hash' not in st.session_state:
    st.session_state['last_hash'] = None

# --- SIDEBAR ---
lang_choice = st.sidebar.selectbox("🌐 Language / Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]

st.sidebar.divider()
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
exchange_rate = utils.get_exchange_rate()
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {exchange_rate:.2f}")

curr_symbol, conv_factor = ("$", 1 / exchange_rate) if currency_choice == "USD ($)" else ("R$", 1.0)

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

# --- MAIN CONTENT ---
if st.session_state['raw_df'] is not None:
    raw_df = st.session_state['raw_df'].copy()
    st.sidebar.success(texts['status_loaded'])

    # 1. Processing Logic
    portfolio = utils.calculate_portfolio(raw_df, lang_choice)
    C = {k: texts[k] for k in texts if k.startswith('col_')}
    prices_brl = utils.fetch_market_prices(portfolio[C['col_ticker']].tolist(), lang_choice)

    portfolio[C['col_curr_price']] = (portfolio[C['col_ticker']].map(prices_brl).fillna(
        portfolio[C['col_avg_price']])) * conv_factor
    portfolio[C['col_avg_price']] *= conv_factor
    portfolio[C['col_total_cost']] *= conv_factor
    portfolio[C['col_earnings']] *= conv_factor
    mkt_val_label = texts['market_value']
    portfolio[mkt_val_label] = portfolio[C['col_curr_price']] * portfolio[C['col_qty']]
    portfolio[C['col_pnl']] = portfolio[mkt_val_label] - portfolio[C['col_total_cost']]
    portfolio[C['col_yield']] = (portfolio[C['col_pnl']] / portfolio[C['col_total_cost']] * 100)

    # 2. Header Metrics
    t_cost, t_mkt = portfolio[C['col_total_cost']].sum(), portfolio[mkt_val_label].sum()
    t_earn = portfolio[C['col_earnings']].sum()
    perf = ((t_mkt / t_cost) - 1) * 100 if t_cost > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(texts['total_invested'], f"{curr_symbol} {t_cost:,.2f}")
    c2.metric(texts['market_value'], f"{curr_symbol} {t_mkt:,.2f}", f"{perf:.2f}%")
    c3.metric(texts['gross_pnl'], f"{curr_symbol} {(t_mkt - t_cost):,.2f}")
    c4.metric(texts['total_earnings'], f"{curr_symbol} {t_earn:,.2f}")

    st.divider()

    # 3. TAB ORGANIZATION
    tab_charts, tab_data = st.tabs([f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"])

    with tab_charts:
        st.markdown(f"### 📈 {texts['evolution_title']} & {texts['monthly_earnings_title']}")
        ev_df = utils.calculate_evolution(raw_df, conv_factor)
        mn_df = utils.calculate_earnings_monthly(raw_df, conv_factor)
        # Combined chart with left-aligned legend
        st.plotly_chart(charts.plot_combined_evolution(ev_df, mn_df, curr_symbol, texts), use_container_width=True)

        st.divider()

        col_pie, col_bar = st.columns(2)
        with col_pie:
            st.markdown(f"#### ⚖️ {texts['allocation_title']}")
            st.plotly_chart(
                charts.plot_sunburst_allocation(portfolio, [C['col_category'], C['col_ticker']], mkt_val_label),
                use_container_width=True)
        with col_bar:
            st.markdown(f"#### 🏆 {texts['earnings_title']}")
            st.plotly_chart(charts.plot_top_earners(portfolio, C['col_ticker'], C['col_earnings'], curr_symbol),
                            use_container_width=True)

    with tab_data:
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
    st.title("📈 B3 Portfolio Master")
    st.markdown(f"### {texts['welcome_msg']}")
    st.caption(texts['welcome_sub'])

    col_msg1, col_msg2, col_msg3 = st.columns(3)
    with col_msg1:
        st.info(texts['step_1'])
    with col_msg2:
        st.info(texts['step_2'])
    with col_msg3:
        st.info(texts['step_3'])

    st.divider()
    st.image("https://images.unsplash.com/photo-1611974714851-eb605161ca81?auto=format&fit=crop&q=80&w=1000")
