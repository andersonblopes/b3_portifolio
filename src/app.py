import pandas as pd
import streamlit as st

import charts
import tables
import utils
from langs import LANGUAGES

st.set_page_config(page_title="B3 Master", layout="wide", page_icon="📈")


@st.dialog("📊 Analysis", width="large")
def _show_analysis_modal(ticker, analysis, fmt_reg, texts):
    """Render the position analysis modal dialog."""
    if analysis is None:
        st.warning(texts['analysis_no_data'])
        return

    # _mdfmt escapes '$' so Streamlit markdown does not treat it as a LaTeX delimiter.
    # use this wherever fmt_reg output is embedded inside a markdown string.
    # st.metric values are plain text and do not need escaping.
    _mdfmt = lambda v: fmt_reg(v).replace('$', r'\$')  # noqa: E731

    rec = analysis['recommendation']
    rec_badge = texts.get(f'rec_{rec}', rec.upper())
    _scen = texts.get(f'analysis_scenario_{analysis["scenario"]}', analysis['scenario'])
    _yoc = analysis.get('yield_on_cost', 0.0)

    # pick rationale key once; reused in the popover and nowhere else
    if rec == 'exit':
        _rationale_key = 'rec_rationale_exit'
    elif rec == 'trim':
        _rationale_key = 'rec_rationale_trim'
    elif rec == 'dca':
        _rationale_key = 'rec_rationale_dca'
    elif _yoc >= 8.0 and analysis['scenario'] == 'loss':
        _rationale_key = 'rec_rationale_hold_dividend'
    elif analysis['scenario'] in ('gain', 'flat'):
        _rationale_key = 'rec_rationale_hold'
    else:
        _rationale_key = 'rec_rationale_hold_concentration'

    # header: ticker + scenario on the left; recommendation badge + rationale popover on the right
    _hc1, _hc2 = st.columns([3, 1])
    _hc1.markdown(f"**{texts['analysis_title']}: {ticker}** — {_scen}")
    with _hc2:
        st.markdown(f"**{texts['analysis_rec_label']}:** {rec_badge}")
        with st.popover(texts['rec_rationale_title'], use_container_width=True):
            st.markdown(texts[_rationale_key])

    # executive summary — one sentence chosen by recommendation + context
    st.divider()
    st.markdown(f"##### {texts['analysis_exec_summary_title']}")
    if rec == 'exit':
        _exec_key = 'exec_exit'
    elif rec == 'trim':
        _exec_key = 'exec_trim'
    elif rec == 'hold' and analysis['scenario'] in ('gain', 'flat'):
        _exec_key = 'exec_hold_gain'
    elif rec == 'hold' and _yoc >= 8.0:
        _exec_key = 'exec_hold_dividend'
    elif rec == 'hold':
        _exec_key = 'exec_hold_concentration'
    else:
        _exec_key = 'exec_dca'
    st.info(texts[_exec_key])

    # key metrics — each carries a help tooltip explaining what it measures
    st.divider()
    _c1, _c2, _c3, _c4, _c5 = st.columns(5)
    _c1.metric(texts['analysis_current_return'], f"{analysis['yield_pct']:+.1f}%",
               help=texts['metric_help_yield_pct'])
    _c2.metric(texts['analysis_breakeven'], fmt_reg(analysis['breakeven']),
               help=texts['metric_help_breakeven'])
    _c3.metric(texts['analysis_trailing_stop'], fmt_reg(analysis['trailing_stop']),
               help=texts['metric_help_trailing_stop'])
    _c4.metric(texts['analysis_yoc_label'], f"{_yoc:.1f}%",
               help=texts['metric_help_yoc'])
    _c5.metric(texts['analysis_weight_label'], f"{analysis.get('current_weight', 0.0):.1f}%",
               help=texts['metric_help_weight'])

    # math of recovery section
    if analysis['targets'] or analysis['dca']:
        st.divider()
        st.markdown(f"##### {texts['analysis_math_title']}")

    if analysis['targets']:
        for _tgt in analysis['targets']:
            _lbl = texts.get(f'analysis_{_tgt["label"]}', _tgt['label'])
            st.write(f"• {_lbl} — {_mdfmt(_tgt['price'])} ({int(_tgt['qty_to_sell'])} unidades)")
    elif analysis['scenario'] in ('gain', 'flat'):
        st.write(texts['analysis_no_targets'])

    if analysis['dca']:
        for _d in analysis['dca']:
            _lbl = texts.get(f'analysis_{_d["label"]}', _d['label'])
            _add_cap = _d['add_qty'] * _d['add_price']
            _ca, _cb, _cc, _cd, _ce = st.columns(5)
            _ca.metric(texts['analysis_dca_add_qty'], int(_d['add_qty']))
            _cb.metric(texts['analysis_dca_at_price'], fmt_reg(_d['add_price']))
            _cc.metric(texts['analysis_dca_new_avg'], fmt_reg(_d['new_avg']))
            _cd.metric(texts['analysis_dca_new_total'], fmt_reg(_add_cap))
            _ce.metric(texts['analysis_post_dca_weight'], f"{_d.get('new_weight', 0.0):.1f}%")
            if _d.get('concentration_risk'):
                st.warning(texts['risk_concentration'].format(weight=_d.get('new_weight', 0.0)))
            st.caption(f"— {_lbl}")
    elif analysis['scenario'] == 'loss':
        st.write(texts['analysis_no_dca'])

    # risk warnings — values shown as metrics; _mdfmt used only in the text template
    _has_warnings = (
        analysis.get('price_below_stop')
        or analysis['yield_pct'] < -30
        or (analysis['dca'] and all(_d.get('concentration_risk') for _d in analysis['dca']))
    )
    if _has_warnings:
        st.divider()
        st.markdown(f"##### {texts['analysis_risk_section_title']}")

    if analysis.get('price_below_stop'):
        _rc1, _rc2 = st.columns(2)
        _rc1.metric(texts['analysis_current_return'], fmt_reg(analysis.get('current_price', 0)),
                    delta=f"{analysis['yield_pct']:+.1f}%", delta_color="inverse")
        _rc2.metric(texts['analysis_trailing_stop'], fmt_reg(analysis['trailing_stop']))
        st.warning(texts['risk_exit_alert'].format(
            price=_mdfmt(analysis.get('current_price', 0)),
            stop=_mdfmt(analysis['trailing_stop']),
        ))

    if analysis['yield_pct'] < -30:
        st.warning(texts['risk_sunk_cost'])

    if analysis['dca'] and all(_d.get('concentration_risk') for _d in analysis['dca']):
        _worst = max(_d.get('new_weight', 0.0) for _d in analysis['dca'])
        _wc1, _wc2 = st.columns(2)
        _wc1.metric(texts['analysis_post_dca_weight'], f"{_worst:.1f}%",
                    delta="limite: 10%", delta_color="inverse")
        st.warning(texts['risk_concentration'].format(weight=_worst))

    # actionable next step — full sentences, currency via _mdfmt to avoid LaTeX mangling
    if rec == 'exit':
        _action = texts['action_exit'].format(stop=_mdfmt(analysis['trailing_stop']))
    elif rec == 'trim':
        _action = texts['action_trim']
    elif rec == 'hold' and _yoc >= 8.0 and analysis['scenario'] == 'loss':
        _action = texts['action_hold_dividend'].format(yoc=_yoc)
    elif rec == 'dca' and analysis['dca'] and all(_d.get('concentration_risk') for _d in analysis['dca']):
        _action = texts['action_dca_blocked']
    elif rec == 'dca' and analysis['dca']:
        _best = next((_d for _d in analysis['dca'] if not _d.get('concentration_risk')), analysis['dca'][0])
        _action = texts['action_dca'].format(
            capital=_mdfmt(_best['add_qty'] * _best['add_price']),
            new_avg=_mdfmt(_best['new_avg']),
        )
    else:
        _action = texts['action_hold']

    st.divider()
    st.markdown(f"##### {texts['analysis_action_title']}")
    st.success(f"➡️ {_action}")


@st.fragment
def _data_lab_groups():
    """Render asset-type expanders with selectable tables inside the Data Lab tab.

    Defined as a fragment so that row-click reruns only this section and do not
    reset the active tab back to the first one.
    """
    _pm = st.session_state._lab_pm
    _texts = st.session_state._lab_texts
    _fmt = st.session_state._lab_fmt
    _prices = st.session_state._lab_prices
    _mkt_total = st.session_state._lab_mkt_total

    types = sorted(_pm['asset_type'].unique())
    for t in types:
        sub_df = _pm[_pm['asset_type'] == t].copy()
        sub_df = sub_df.sort_values('yield', ascending=False).reset_index(drop=True)
        t_mkt = sub_df['v_mercado'].sum()
        weight = (t_mkt / _mkt_total) * 100 if _mkt_total > 0 else 0
        label_assets = _texts['assets_count']
        title = f"📁 {t} | {len(sub_df)} {label_assets} | {_fmt(t_mkt)} ({weight:.2f}%)"
        with st.expander(title, expanded=True):
            _tbl_key = f"tbl_{t}"
            _prev_key = f"_analysis_prev_{t}"
            event = tables.render_portfolio_table(
                sub_df, _texts, _fmt, selectable=True, table_key=_tbl_key
            )
            if event and event.selection.rows:
                _idx = event.selection.rows[0]
                _ticker = sub_df.iloc[_idx]['ticker']
                # only open modal on a new selection; prevents reopening after dismiss
                if st.session_state.get(_prev_key) != _ticker:
                    st.session_state[_prev_key] = _ticker
                    _row = sub_df.iloc[_idx]
                    _has_live = _prices.get(_ticker, {}).get('p') is not None
                    if _has_live:
                        _an = utils.analyze_position(
                            ticker=_ticker,
                            qty=float(_row['qty']),
                            avg_price=float(_row['avg_price']),
                            total_cost=float(_row['total_cost']),
                            current_price=float(_row['p_atual']),
                            earnings=float(_row['earnings']),
                            asset_type=str(_row['asset_type']),
                            portfolio_total_value=float(_mkt_total),
                        )
                    else:
                        _an = None
                    _show_analysis_modal(_ticker, _an, _fmt, _texts)


# Initialization of Session State
if 'raw_df' not in st.session_state:
    st.session_state.raw_df = None
if 'import_stats' not in st.session_state:
    st.session_state.import_stats = None
if 'audit_df' not in st.session_state:
    st.session_state.audit_df = None

# Sidebar Controls
# Note: this label is intentionally bilingual because we need the selection before we can load `texts`.

# Persist language + currency in the URL query params as a hard guarantee against resets.
# (Some reruns / browser behaviors can wipe session_state; query params survive reloads.)
qp = st.query_params

# Use stable language *codes* internally so labels can change without breaking state.
LANG_CODE_TO_KEY = {
    "pt": "Português (Brasil)",
    "en": "English",
    "es": "Español",
    "fr": "Français",
}
LANG_KEY_TO_CODE = {v: k for k, v in LANG_CODE_TO_KEY.items()}

if "lang_code" not in st.session_state:
    # Accept either code (pt/en/es/fr) or a legacy full language key in the URL
    raw = qp.get("lang", "pt")
    if raw in LANG_CODE_TO_KEY:
        st.session_state.lang_code = raw
    else:
        st.session_state.lang_code = LANG_KEY_TO_CODE.get(raw, "pt")

if "currency_code" not in st.session_state:
    st.session_state.currency_code = qp.get("cur", "BRL")


def _sync_lang_to_url():
    st.query_params["lang"] = st.session_state.lang_code


def _sync_currency_to_url():
    st.query_params["cur"] = st.session_state.currency_code


language_codes = ["pt", "en", "es", "fr"]


def fmt_lang(code: str) -> str:
    # Display-friendly labels (no need to say "(Brasil)" in the UI)
    return {
        "pt": "Português",
        "en": "English",
        "es": "Español",
        "fr": "Français",
    }.get(code, str(code))


lang_code = st.sidebar.selectbox(
    "🌐 Language / Idioma",
    language_codes,
    key="lang_code",
    format_func=fmt_lang,
    on_change=_sync_lang_to_url,
)
texts = LANGUAGES[LANG_CODE_TO_KEY[lang_code]]

# Sidebar CSS: compact spacing to avoid vertical scrolling.
st.sidebar.markdown(
    """
<style>
section[data-testid="stSidebar"] .stVerticalBlock { gap: 0.35rem; }
section[data-testid="stSidebar"] .stMarkdown p { margin: 0.1rem 0; }
section[data-testid="stSidebar"] .stToggle label p { white-space: nowrap; }
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar.expander(texts['sidebar_settings'], expanded=False):
    # Store currency as a stable code in session_state so language changes never reset it.
    currency_codes = ["BRL", "USD", "EUR"]

    def fmt_currency(code: str) -> str:
        return {
            "BRL": "BRL (R$)",
            "USD": "USD ($)",
            "EUR": "EUR (€)",
        }.get(code, str(code))

    currency_code = st.radio(
        texts['currency_label'],
        currency_codes,
        key="currency_code",
        format_func=fmt_currency,
        on_change=_sync_currency_to_url,
    )

with st.sidebar.expander(texts['sidebar_market'], expanded=False):
    # Market refresh (manual + optional auto)
    from streamlit_autorefresh import st_autorefresh

    # Keep the label short to avoid wrapping in the sidebar.
    auto_refresh = st.toggle(texts['auto_refresh_label'], value=True, help=texts['auto_refresh_help'])

    refresh_count = None
    refresh_interval_ms = None

    if auto_refresh:
        refresh_interval_label = st.selectbox(
            texts['refresh_interval_label'],
            ["30s", "1m", "5m"],
            index=1,
            help=texts['refresh_interval_help'],
        )
        refresh_interval_ms = {"30s": 30_000, "1m": 60_000, "5m": 300_000}[refresh_interval_label]
        refresh_count = st_autorefresh(interval=refresh_interval_ms, key="auto_market_refresh")

    manual_refresh = st.button(texts['refresh_button'])

    # Clear caches when the user clicks the button OR when the autorefresh ticks.
    # st_autorefresh returns an incrementing counter; use it to detect actual ticks.
    if 'last_auto_refresh_count' not in st.session_state:
        st.session_state.last_auto_refresh_count = None

    auto_tick = (
        auto_refresh
        and refresh_count is not None
        and refresh_count != st.session_state.last_auto_refresh_count
    )

    if manual_refresh or auto_tick:
        utils.fetch_market_prices.clear()  # Clears the cache for prices
        utils.get_exchange_rate.clear()  # Clears the cache for USD rate
        if auto_tick:
            st.session_state.last_auto_refresh_count = refresh_count
        st.toast(texts['refresh_toast'], icon="⏳")

    # FX rate shown depends on selected display currency
    if currency_code == "EUR":
        fx_base = "EUR"
    else:
        fx_base = "USD"

    rate = utils.get_exchange_rate(fx_base)
    st.metric(label=texts['fx_rate_msg'].format(base=fx_base), value=f"R$ {rate:.2f}")

with st.sidebar.expander(texts['sidebar_import'], expanded=False):
    uploaded_files = st.file_uploader(texts['upload_msg'], type=['xlsx'], accept_multiple_files=True)

    if uploaded_files:
        # Processing only occurs when new files are uploaded
        (
            st.session_state.raw_df,
            st.session_state.import_stats,
            st.session_state.audit_df,
        ) = utils.load_and_process_files(uploaded_files)

    if st.session_state.import_stats is not None and not st.session_state.import_stats.empty:
        st.caption(texts['import_summary_label'])
        st.dataframe(st.session_state.import_stats, width="stretch", hide_index=True)

        # Optional dedup summary (if present)
        if 'dedup_removed_main' in st.session_state.import_stats.columns:
            dedup_row = st.session_state.import_stats[st.session_state.import_stats['detected'] == 'DEDUP']
            if not dedup_row.empty:
                removed = int((dedup_row['dedup_removed_main'].fillna(0).iloc[0] or 0) + (dedup_row['dedup_removed_audit'].fillna(0).iloc[0] or 0))
                before = int(dedup_row['rows_total'].fillna(0).iloc[0] or 0)
                after = int(before - (dedup_row['dedup_removed_main'].fillna(0).iloc[0] or 0))
                if removed > 0:
                    st.caption(texts['dedup_summary'].format(removed=removed, before=before, after=after))

    if st.button(texts['clear_data_button']):
        st.session_state.raw_df = None
        st.session_state.import_stats = None
        st.session_state.audit_df = None
        st.rerun()

is_usd = currency_code == "USD"
is_eur = currency_code == "EUR"

if is_usd:
    sym, factor = ("$", 1 / rate)
elif is_eur:
    sym, factor = ("€", 1 / rate)
else:
    sym, factor = ("R$", 1.0)


def fmt_reg(v):
    decimal = ',' if (not is_usd and not is_eur) else '.'
    return f"{sym} {v:.2f}".replace('.', decimal)


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


# Main UI Logic
if st.session_state.raw_df is not None:
    raw_df = st.session_state.raw_df

    # fetch split history for all tickers in raw data before portfolio calc,
    # so yfinance splits can fill in for tickers without MOV corporate action rows.
    _all_raw_tickers = tuple(sorted(raw_df['ticker'].dropna().unique().tolist()))
    split_history = utils.fetch_split_history(_all_raw_tickers)

    portfolio = utils.calculate_portfolio(raw_df, split_history=split_history)
    has_earnings = not raw_df[raw_df['type'] == 'EARNINGS'].empty
    portfolio_main = portfolio[portfolio['qty'] > 0].copy()

    # Fetch fresh prices using the cached function
    tickers = portfolio_main['ticker'].unique().tolist()
    prices = utils.fetch_market_prices(tickers)

    live_count = sum(1 for t in tickers if prices.get(t, {}).get('live'))
    missing_tickers = [t for t in tickers if not prices.get(t, {}).get('live')]

    if tickers and missing_tickers:
        st.sidebar.warning(
            texts['yahoo_unavailable_warning'].format(
                missing=len(missing_tickers),
                total=len(tickers),
            )
        )
        with st.sidebar.expander(texts['missing_prices_expander'], expanded=False):
            st.write(", ".join(sorted(missing_tickers)))

    # prices[t]['p'] can be None when yfinance has no data; 'or 0' guards against None * factor
    res = portfolio_main['ticker'].apply(
        lambda t: ((prices.get(t, {}).get('p') or 0) * factor, "✅" if prices.get(t, {}).get('live') else "⚠️"))

    portfolio_main['p_atual'] = [
        x[0] if x[0] > 0 else portfolio_main.loc[portfolio_main['ticker'] == t, 'avg_price'].values[0] * factor
        for t, x in zip(portfolio_main['ticker'], res)]
    portfolio_main['status'] = [x[1] for x in res]

    for c in ['avg_price', 'total_cost', 'earnings']: portfolio_main[c] *= factor
    portfolio_main['v_mercado'] = portfolio_main['p_atual'] * portfolio_main['qty']
    portfolio_main['pnl'] = portfolio_main['v_mercado'] - portfolio_main['total_cost']
    portfolio_main['yield'] = (portfolio_main['pnl'] / portfolio_main['total_cost'] * 100)
    mkt_total = portfolio_main['v_mercado'].sum()

    # KPIs
    inv_total, earn_total = portfolio_main['total_cost'].sum(), portfolio_main['earnings'].sum()

    fees_total = 0.0
    if st.session_state.audit_df is not None and not st.session_state.audit_df.empty:
        fees_total = float(st.session_state.audit_df[st.session_state.audit_df['type'] == 'FEES']['val'].sum())

    net_earnings = earn_total + fees_total

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(texts['total_invested'], fmt_reg(inv_total))
    k2.metric(texts['market_value'], fmt_reg(mkt_total), f"{(mkt_total / inv_total - 1) * 100:.2f}%")
    k3.metric(texts['gross_pnl'], fmt_reg(mkt_total - inv_total))
    if has_earnings:
        k4.metric(texts['total_earnings'], fmt_reg(earn_total))
        k5.metric(texts['kpi_earnings_net'], fmt_reg(net_earnings))

    show_audit = st.session_state.audit_df is not None and not st.session_state.audit_df.empty

    tab_labels = [f"📊 {texts['tab_visuals']}", f"📝 {texts['tab_data']}"]
    if has_earnings:
        tab_labels.append(f"💰 {texts['tab_earnings']}")
    if show_audit:
        tab_labels.append(f"🧾 {texts['tab_audit']}")
    tab_labels.append(f"🔄 {texts['tab_ticker_changes']}")

    tabs = st.tabs(tab_labels)

    earnings_tab_idx = 2 if has_earnings else None
    audit_tab_idx = (3 if has_earnings else 2) if show_audit else None
    ticker_changes_tab_idx = len(tab_labels) - 1

    with tabs[0]:  # Dashboard Global
        c1, c2 = st.columns(2)
        # Cashflow evolution (BUY = outflow, SELL/EARNINGS = inflow, FEES = outflow)
        cf = raw_df[['date', 'type', 'val']].copy()
        if not cf.empty:
            cf['cashflow'] = 0.0
            cf.loc[cf['type'] == 'BUY', 'cashflow'] = -cf.loc[cf['type'] == 'BUY', 'val']
            cf.loc[cf['type'].isin(['SELL', 'EARNINGS']), 'cashflow'] = cf.loc[
                cf['type'].isin(['SELL', 'EARNINGS']), 'val'
            ]

            cf2 = cf[['date', 'cashflow']]

            if st.session_state.audit_df is not None and not st.session_state.audit_df.empty:
                fees_df = st.session_state.audit_df[st.session_state.audit_df['type'] == 'FEES'][
                    ['date', 'val']
                ].copy()
                fees_df = fees_df.rename(columns={'val': 'cashflow'})
                cf2 = pd.concat([cf2, fees_df], ignore_index=True)

            ev = (
                cf2.dropna(subset=['date'])
                .sort_values('date')
                .groupby('date')['cashflow']
                .sum()
                .cumsum()
                .reset_index()
            )
            ev['cashflow'] *= factor
            c1.plotly_chart(
                charts.plot_evolution(ev.rename(columns={'cashflow': 'flow'}), sym, is_usd, texts['chart_evolution']),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )
        c2.plotly_chart(
            charts.plot_allocation(portfolio_main, 'asset_type', 'v_mercado', is_usd, texts['chart_allocation']),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

        st.divider()
        c3, c4 = st.columns(2)
        df_inst = raw_df[raw_df['source'] == 'NEG'].groupby('inst')['val'].sum().reset_index()
        df_inst['val'] *= factor
        c3.plotly_chart(
            charts.plot_allocation(df_inst, 'inst', 'val', is_usd, texts['chart_asset_inst']),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

        if has_earnings:
            earn_raw = raw_df[raw_df['type'] == 'EARNINGS'].copy()
            earn_raw['val'] *= factor
            res_m = earn_raw.copy()
            res_m['month_year'] = res_m['date'].dt.strftime('%Y-%m')
            res_m = res_m.groupby('month_year')['val'].sum().reset_index().sort_values('month_year')
            c4.plotly_chart(
                charts.plot_earnings_evolution(res_m, sym, is_usd, texts['chart_earn_monthly']),
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    with tabs[1]:  # Data Lab
        st.write(texts['status_legend'])
        # store runtime values so the fragment can read them without argument-serialization issues
        st.session_state._lab_pm = portfolio_main
        st.session_state._lab_texts = texts
        st.session_state._lab_fmt = fmt_reg
        st.session_state._lab_prices = prices
        st.session_state._lab_mkt_total = mkt_total
        _data_lab_groups()

    if has_earnings:
        with tabs[earnings_tab_idx]:  # Earnings
            earn_raw = raw_df[raw_df['type'] == 'EARNINGS'].copy()
            earn_raw['val'] *= factor
            r1_c1, r1_c2 = st.columns(2)
            with r1_c1:
                st.plotly_chart(
                    charts.plot_allocation(
                        earn_raw.groupby('sub_type')['val'].sum().reset_index(),
                        'sub_type',
                        'val',
                        is_usd,
                        texts['chart_earn_type'],
                    ),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                )
            with r1_c2:
                earn_raw['at_type'] = earn_raw['ticker'].apply(utils.detect_asset_type)
                st.plotly_chart(
                    charts.plot_allocation(
                        earn_raw.groupby('at_type')['val'].sum().reset_index(),
                        'at_type',
                        'val',
                        is_usd,
                        texts['chart_earn_asset_type'],
                    ),
                    use_container_width=True,
                    config=PLOTLY_CONFIG,
                )
            st.divider()
            st.subheader(texts['earnings_audit_title'])
            tables.render_earnings_log(earn_raw, texts, fmt_reg)

    if show_audit:
        with tabs[audit_tab_idx]:
            audit_df = st.session_state.audit_df.copy()

            fees_df = audit_df[audit_df['type'] == 'FEES'].copy()
            transfers_df = audit_df[audit_df['type'] == 'TRANSFER'].copy()
            ignored_df = audit_df[audit_df['type'] == 'IGNORE'].copy()

            def render_paged_df(df: pd.DataFrame, columns: list[str], key_prefix: str):
                if df.empty:
                    st.caption("(none)")
                    return

                df2 = df[columns].sort_values('date', ascending=False)
                total = int(len(df2))

                # Lightweight CSS to make pagination look closer to classic web UIs
                st.markdown(
                    """
<style>
/* Compact pagination buttons (audit tables)
   Note: selectors are broad in Streamlit; keep changes minimal. */
div[data-testid="stHorizontalBlock"] .stButton { margin: 0; padding: 0; }
div[data-testid="stHorizontalBlock"] .stButton button {
  padding: 0.10rem 0.35rem;
  min-height: 1.75rem;
  line-height: 1.1;
  font-size: 0.85rem;
  white-space: nowrap; /* avoid label wrapping */
}
/* Reduce extra vertical spacing around pagination rows */
div[data-testid="stHorizontalBlock"] { row-gap: 0.15rem; column-gap: 0.15rem; }
</style>
""",
                    unsafe_allow_html=True,
                )

                # State
                page_size_key = f"{key_prefix}_page_size"
                page_key = f"{key_prefix}_page"

                page_size_options = [25, 50, 100, 200, 500]
                page_size = int(st.session_state.get(page_size_key, 50))

                pages = max(1, (total + page_size - 1) // page_size)

                if page_key not in st.session_state:
                    st.session_state[page_key] = 1

                st.session_state[page_key] = max(1, min(int(st.session_state[page_key]), pages))
                page = int(st.session_state[page_key])

                # Slice + table (table first; controls go under it)
                start = (page - 1) * page_size
                end = min(start + page_size, total)
                st.dataframe(df2.iloc[start:end], width="stretch", hide_index=True)

                from typing import List, Union

                def page_buttons_window(curr: int, total_pages: int) -> List[Union[int, str]]:
                    """Return a list like [1, '…', 4, 5, 6, '…', 20]."""
                    if total_pages <= 7:
                        return list(range(1, total_pages + 1))

                    window = {1, total_pages}
                    for p in range(curr - 1, curr + 2):
                        if 1 <= p <= total_pages:
                            window.add(p)

                    if curr <= 3:
                        window.update({2, 3, 4})
                    if curr >= total_pages - 2:
                        window.update({total_pages - 3, total_pages - 2, total_pages - 1})

                    pages_sorted = sorted(p for p in window if 1 <= p <= total_pages)

                    out: List[Union[int, str]] = []
                    prev = None
                    for p in pages_sorted:
                        if prev is not None and p - prev > 1:
                            out.append('…')
                        out.append(p)
                        prev = p
                    return out

                items = page_buttons_window(page, pages)

                # Controls under the table, constrained to ~50% width (right column)
                outer_left, outer_right = st.columns([1, 1])
                with outer_right:
                    st.caption(texts['pagination_showing'].format(start=start + 1, end=end, total=total))

                    cols = st.columns([1] + [1] * len(items) + [1, 2])

                    # Prev
                    prev_disabled = page <= 1
                    if cols[0].button(texts['pagination_prev'], disabled=prev_disabled, key=f"{key_prefix}_prev"):
                        st.session_state[page_key] = max(1, page - 1)
                        st.rerun()

                    # Numbers
                    for i, it in enumerate(items, start=1):
                        if it == '…':
                            cols[i].markdown("…")
                            continue

                        p = int(it)
                        is_current = p == page
                        if cols[i].button(str(p), disabled=is_current, key=f"{key_prefix}_p_{p}"):
                            st.session_state[page_key] = p
                            st.rerun()

                    # Next
                    next_disabled = page >= pages
                    if cols[-2].button(texts['pagination_next'], disabled=next_disabled, key=f"{key_prefix}_next"):
                        st.session_state[page_key] = min(pages, page + 1)
                        st.rerun()

                    # Page size selector (right side)
                    cols[-1].selectbox(
                        texts['pagination_page_size'],
                        page_size_options,
                        index=page_size_options.index(page_size) if page_size in page_size_options else 1,
                        key=page_size_key,
                        label_visibility="collapsed",
                    )

            # Stack tables vertically (with pagination) to avoid horizontal scrolling.
            st.subheader(texts['audit_fees'])
            render_paged_df(fees_df, ['date', 'ticker', 'inst', 'val', 'desc'], key_prefix="audit_fees")

            st.divider()
            st.subheader(texts['audit_transfers'])
            render_paged_df(transfers_df, ['date', 'ticker', 'inst', 'val', 'desc'], key_prefix="audit_transfers")

            st.divider()
            st.subheader(texts['audit_ignored'])
            render_paged_df(ignored_df, ['date', 'ticker', 'inst', 'val', 'desc', 'source'], key_prefix="audit_ignored")

    with tabs[ticker_changes_tab_idx]:
        st.subheader(texts['ticker_changes_remap_title'])
        st.caption(texts['ticker_changes_remap_desc'])

        remap_rows = [
            {
                texts['ticker_changes_remap_col_old']: old,
                texts['ticker_changes_remap_col_new']: meta["new"],
                texts['ticker_changes_remap_col_note']: meta["note"],
            }
            for old, meta in utils.TICKER_REMAP.items()
        ]
        st.dataframe(pd.DataFrame(remap_rows), use_container_width=True, hide_index=True)

        st.divider()

        st.subheader(texts['ticker_changes_discontinued_title'])
        st.caption(texts['ticker_changes_discontinued_desc'])

        disc_rows = [
            {
                texts['ticker_changes_discontinued_col_ticker']: ticker,
                texts['ticker_changes_discontinued_col_reason']: reason,
            }
            for ticker, reason in utils.DISCONTINUED_TICKERS.items()
        ]
        st.dataframe(pd.DataFrame(disc_rows), use_container_width=True, hide_index=True)

        st.divider()

        # corporate actions fetched from yfinance for every portfolio ticker
        st.subheader(texts['ticker_changes_corp_title'])
        st.caption(texts['ticker_changes_corp_desc'])

        # first buy date per ticker — events before this date are irrelevant
        _first_buy = (
            raw_df[raw_df['type'] == 'BUY']
            .groupby('ticker')['date']
            .min()
            .apply(pd.Timestamp)
        )

        corp_rows = []
        _portfolio_tickers = set(portfolio['ticker'].unique()) if not portfolio.empty else set()
        for t in sorted(_portfolio_tickers):
            if t not in split_history:
                continue
            first_buy = _first_buy.get(t)
            for ev in split_history[t]:
                # skip events that pre-date the first purchase of this ticker
                if first_buy is not None and ev['date'] < first_buy:
                    continue
                is_reverse = ev['ratio'] < 1.0
                ev_type = texts['ticker_changes_corp_type_reverse'] if is_reverse else texts['ticker_changes_corp_type_split']
                if is_reverse:
                    # ratio=0.1 means 10:1 grouping
                    n = round(1 / ev['ratio'])
                    effect = f"{n}:1 → ×{ev['ratio']:.4g}"
                else:
                    effect = f"1:{round(ev['ratio'])} → ×{ev['ratio']:.4g}"
                corp_rows.append({
                    texts['ticker_changes_corp_col_ticker']: t,
                    texts['ticker_changes_corp_col_date']: ev['date'].strftime('%Y-%m-%d'),
                    texts['ticker_changes_corp_col_type']: ev_type,
                    texts['ticker_changes_corp_col_ratio']: f"{ev['ratio']:.4g}",
                    texts['ticker_changes_corp_col_effect']: effect,
                })

        if corp_rows:
            corp_df = pd.DataFrame(corp_rows).sort_values(
                [texts['ticker_changes_corp_col_ticker'], texts['ticker_changes_corp_col_date']]
            )
            st.dataframe(corp_df, use_container_width=True, hide_index=True)
        else:
            st.caption(texts['ticker_changes_corp_no_data'])

        st.divider()

        # tickers in the current portfolio that returned no live price — potential delists
        st.subheader(texts['ticker_changes_possibly_disc_title'])
        st.caption(texts['ticker_changes_possibly_disc_desc'])

        # compare against portfolio_main (active positions only)
        _no_live = [t for t in portfolio_main['ticker'].unique() if not prices.get(t, {}).get('live')]
        # exclude tickers already explicitly handled
        _no_live = [t for t in _no_live if t not in utils.DISCONTINUED_TICKERS]

        if _no_live:
            def _last_tx(t):
                rows = raw_df[raw_df['ticker'] == t]
                if rows.empty:
                    return '—'
                return pd.to_datetime(rows['date']).max().strftime('%Y-%m-%d')

            possibly_disc_rows = [
                {
                    texts['ticker_changes_possibly_disc_col_ticker']: t,
                    texts['ticker_changes_possibly_disc_col_last_tx']: _last_tx(t),
                }
                for t in sorted(_no_live)
            ]
            st.dataframe(pd.DataFrame(possibly_disc_rows), use_container_width=True, hide_index=True)
        else:
            st.caption(texts['ticker_changes_possibly_disc_no_data'])

else:
    st.title(texts['welcome_title'])
    st.subheader(texts['welcome_subheader'])
    st.markdown(f"### {texts['quick_start_title']}")
    st.info(texts['quick_start_step1'])
    st.info(texts['quick_start_step2'])
    st.info(texts['quick_start_step3'])
