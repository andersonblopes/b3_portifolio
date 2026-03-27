import streamlit as st


def render_portfolio_table(df, texts, fmt_func, selectable=False, table_key=None):
    display_cols = {
        'ticker': texts['col_ticker'], 'qty': texts['col_qty'], 'avg_price': texts['col_avg_price'],
        'total_cost': texts['col_total_cost'], 'p_atual': texts['col_curr_price'], 'v_mercado': texts['market_value'],
        'pnl': texts['col_pnl'], 'yield': texts['col_yield'], 'status': texts['col_status'],
        'earnings': texts['col_earnings']
    }

    display_df = df[list(display_cols.keys())].rename(columns=display_cols)

    if selectable:
        # add a narrow hint column so users see rows are clickable
        display_df = display_df.copy()
        display_df.insert(0, "📊", "→")

    styled = display_df.style.format({
        texts['col_qty']: "{:.0f}",
        texts['col_yield']: "{:.2f}%",
        texts['col_avg_price']: fmt_func,
        texts['col_curr_price']: fmt_func,
        texts['col_total_cost']: fmt_func,
        texts['market_value']: fmt_func,
        texts['col_pnl']: fmt_func,
        texts['col_earnings']: fmt_func,
    }).background_gradient(subset=[texts['col_yield']], cmap='RdYlGn', vmin=-15, vmax=15)

    if selectable:
        col_cfg = {"📊": st.column_config.TextColumn(label=" ", width="small")}
        return st.dataframe(
            styled,
            on_select="rerun",
            selection_mode="single-row",
            key=table_key,
            column_config=col_cfg,
            width="stretch",
            hide_index=True,
        )

    st.dataframe(styled, width="stretch", hide_index=True)
    return None


def render_earnings_log(df, texts, fmt_func):
    audit_df = df.rename(columns={
        'date': texts['col_date'],
        'ticker': texts['col_ticker'],
        'val': texts['col_earnings'],
        'sub_type': texts['col_earning_type'],
        'inst': texts['col_inst']
    })

    st.dataframe(
        audit_df[
            [
                texts['col_date'],
                texts['col_ticker'],
                texts['col_inst'],
                texts['col_earning_type'],
                texts['col_earnings'],
            ]
        ].style.format(
            {
                texts['col_date']: lambda x: x.strftime('%d/%m/%Y'),
                texts['col_earnings']: fmt_func,
            }
        ),
        width="stretch",
        hide_index=True,
    )
