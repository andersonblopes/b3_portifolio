import streamlit as st

import charts
import utils
from langs import LANGUAGES

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="B3 Portfolio Master",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="auto"
)

# --- 2. INITIALIZE SESSION STATE ---
if 'raw_df' not in st.session_state:
    st.session_state['raw_df'] = None
if 'last_hash' not in st.session_state:
    st.session_state['last_hash'] = None

# --- 3. SIDEBAR CONTROLS ---
lang_choice = st.sidebar.selectbox("🌐 Language / Idioma", ["Português (Brasil)", "English"])
texts = LANGUAGES[lang_choice]

st.sidebar.divider()
currency_choice = st.sidebar.radio(texts['currency_label'], ["BRL (R$)", "USD ($)"])
exchange_rate = utils.get_exchange_rate()
st.sidebar.metric(label=texts['exchange_rate_msg'], value=f"R$ {exchange_rate:.2f}")

curr_symbol, conv_factor = ("$", 1 / exchange_rate) if currency_choice == "USD ($)" else ("R$", 1.0)

st.sidebar.divider()
uploaded_files = st.sidebar.file_uploader(
    texts['upload_msg'],
    type=['xlsx'],
    accept_multiple_files=True
)

# --- 4. FILE PROCESSING ---
if uploaded_files:
    incoming_df = utils.load_and_process_files(uploaded_files)
    if not incoming_df.empty:
        new_hash = utils.get_data_hash(incoming_df)
        if new_hash != st.session_state['last_hash']:
            st.session_state['raw_df'] = incoming_df
            st.session_state['last_hash'] = new_hash
        else:
            st.sidebar.info(texts['warning_duplicate'])

# --- 5. MAIN CONTENT ---
if st.session_state['raw_df'] is not None:
    # ... (Keep your existing Dashboard State code here) ...
    raw_df = st.session_state['raw_df'].copy()
    st.sidebar.success(texts['status_loaded'])

    # [Rest of your calculation and tab logic remains the same]
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

    t_cost, t_mkt = portfolio[C['col_total_cost']].sum(), portfolio[mkt_val_label].sum()
    t_earn = portfolio[C['col_earnings']].sum()
    perf = ((t_mkt / t_cost) - 1) * 100 if t_cost > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(texts['total_invested'], f"{curr_symbol} {t_cost:,.2f}")
    c2.metric(texts['market_value'], f"{curr_symbol} {t_mkt:,.2f}", f"{perf:.2f}%")
    c3.metric(texts['gross_pnl'], f"{curr_symbol} {(t_mkt - t_cost):,.2f}")
    c4.metric(texts['total_earnings'], f"{curr_symbol} {t_earn:,.2f}")

    st.divider()
    tab_charts, tab_data = st.tabs([f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"])

    with tab_charts:
        st.markdown(f"### 📈 {texts['evolution_title']} & {texts['monthly_earnings_title']}")
        ev_df = utils.calculate_evolution(raw_df, conv_factor)
        mn_df = utils.calculate_earnings_monthly(raw_df, conv_factor)
        st.plotly_chart(charts.plot_combined_evolution(ev_df, mn_df, curr_symbol, texts), use_container_width=True)
        st.divider()
        col_pie, col_bar = st.columns(2, gap="large")
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
        st.markdown(f"### {texts['detailed_title']}")
        st.dataframe(portfolio.style.format({
            C['col_avg_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_curr_price']: f'{curr_symbol} ' + '{:.2f}',
            C['col_total_cost']: f'{curr_symbol} ' + '{:.2f}',
            mkt_val_label: f'{curr_symbol} ' + '{:.2f}',
            C['col_pnl']: f'{curr_symbol} ' + '{:.2f}',
            C['col_earnings']: f'{curr_symbol} ' + '{:.2f}',
            C['col_qty']: '{:,.2f}',
            C['col_yield']: '{:.2f}%'
        }).background_gradient(subset=[C['col_yield']], cmap='RdYlGn'), use_container_width=True, hide_index=True)

    st.sidebar.divider()
    if st.sidebar.button("🗑️ Reset Session"):
        st.session_state['raw_df'] = None
        st.session_state['last_hash'] = None
        st.rerun()

else:
    # --- 6. PREMIUM CSS HERO PAGE (ZERO SCROLL) ---
    st.markdown("""
        <style>
            .block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
            .hero-container {
                background: linear-gradient(135deg, #1a1a1a 0%, #0e1117 100%);
                border: 1px solid rgba(0, 255, 170, 0.2);
                border-radius: 20px;
                height: 55vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                position: relative;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                margin-top: 20px;
            }
            .hero-container::before {
                content: "";
                position: absolute;
                top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(0,255,170,0.05) 0%, transparent 70%);
                animation: rotate 10s linear infinite;
            }
            @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            .hero-text { position: relative; z-index: 1; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>📈 B3 Portfolio Master</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align: center; font-size: 1.1rem; opacity: 0.8; margin-top: 5px;'>{texts['welcome_msg']}</p>",
        unsafe_allow_html=True)

    # These boxes now contain the clickable hyperlink
    col_msg1, col_msg2, col_msg3 = st.columns(3)
    with col_msg1:
        st.info(texts['step_1'])
    with col_msg2:
        st.info(texts['step_2'])
    with col_msg3:
        st.info(texts['step_3'])

    st.markdown(f"""
        <div class="hero-container">
            <div class="hero-text">
                <div style="font-size: 80px; margin-bottom: 10px;">📊</div>
                <h2 style="color: #00FFAA; font-weight: 300; border: none;">{texts['welcome_sub']}</h2>
                <p style="opacity: 0.6; font-size: 0.9rem;">{texts['upload_msg']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
