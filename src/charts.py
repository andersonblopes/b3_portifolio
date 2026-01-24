import plotly.express as px
import plotly.graph_objects as go


def plot_evolution(evolution_df, curr_symbol):
    fig = px.area(evolution_df, x='date', y='flow')
    fig.update_traces(line_color='#00FFAA', fillcolor='rgba(0, 255, 170, 0.1)')
    fig.update_layout(height=350, yaxis_tickprefix=f"{curr_symbol} ", yaxis_title=None, xaxis_title=None)
    return fig


def plot_monthly_earnings(monthly_earn_df, curr_symbol):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_earn_df['month_year'], y=monthly_earn_df['operation_value'], marker_color='#FFD700',
                         opacity=0.8))
    avg_val = monthly_earn_df['operation_value'].mean()
    fig.add_trace(go.Scatter(x=monthly_earn_df['month_year'], y=[avg_val] * len(monthly_earn_df), mode='lines',
                             line=dict(color='white', width=2, dash='dot')))
    fig.update_layout(height=350, yaxis_tickprefix=f"{curr_symbol} ", showlegend=False, xaxis_title=None)
    return fig


def plot_sunburst_allocation(portfolio, path_cols, values_col):
    fig = px.sunburst(portfolio, path=path_cols, values=values_col)
    fig.update_layout(height=450)
    return fig


def plot_top_earners(portfolio, ticker_col, earnings_col, curr_symbol):
    df_sorted = portfolio.sort_values(earnings_col, ascending=True).tail(10)
    fig = px.bar(df_sorted, y=ticker_col, x=earnings_col, orientation='h', color=earnings_col,
                 color_continuous_scale='Viridis')
    fig.update_layout(height=450, xaxis_tickprefix=f"{curr_symbol} ", showlegend=False, yaxis_title=None)
    return fig
