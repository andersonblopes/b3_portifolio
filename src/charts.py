import plotly.express as px
import plotly.graph_objects as go


def plot_combined_evolution(evolution_df, monthly_earn_df, curr_symbol, texts):
    fig = go.Figure()

    # 1. Invested Capital (Area)
    fig.add_trace(go.Scatter(
        x=evolution_df['date'],
        y=evolution_df['flow'],
        fill='tozeroy',
        name=texts['total_invested'],
        line=dict(color='#00FFAA', width=2.5),
        fillcolor='rgba(0, 255, 170, 0.15)'
    ))

    # 2. Monthly Earnings (Bars)
    if not monthly_earn_df.empty:
        fig.add_trace(go.Bar(
            x=monthly_earn_df['month_year'],
            y=monthly_earn_df['operation_value'],
            name=texts['monthly_earnings_title'],
            marker_color='#FFD700',
            opacity=0.65,
            yaxis='y2'
        ))

    fig.update_layout(
        height=480,
        margin=dict(l=10, r=50, t=50, b=10),  # Added top margin for legend
        hovermode="x unified",
        # Legend on the Left
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        yaxis=dict(
            tickprefix=f"{curr_symbol} ",
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)'
        ),
        yaxis2=dict(
            tickprefix=f"{curr_symbol} ",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis=dict(showgrid=False)
    )
    return fig


def plot_sunburst_allocation(portfolio, path_cols, values_col):
    fig = px.sunburst(portfolio, path=path_cols, values=values_col)
    fig.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    return fig


def plot_top_earners(portfolio, ticker_col, earnings_col, curr_symbol):
    df_sorted = portfolio.sort_values(earnings_col, ascending=True).tail(10)
    fig = px.bar(
        df_sorted,
        y=ticker_col,
        x=earnings_col,
        orientation='h',
        color=earnings_col,
        color_continuous_scale='Viridis'
    )
    fig.update_layout(
        height=450,
        xaxis_tickprefix=f"{curr_symbol} ",
        showlegend=False,
        yaxis_title=None,
        margin=dict(l=10, r=40, t=30, b=10)
    )
    return fig
