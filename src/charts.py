import plotly.express as px


def plot_evolution(ev_df, sym, is_usd, title):
    seps = ".," if is_usd else ", "
    fig = px.area(ev_df, x='date', y='flow', title=title, template="plotly_dark")
    fig.update_traces(line_color='#00FFAA', fillcolor='rgba(0, 255, 170, 0.2)', hovertemplate="%{y:.2f}")
    fig.update_layout(separators=seps, yaxis_title=None, xaxis_title=None, yaxis=dict(tickprefix=f"{sym} "))
    return fig


def plot_allocation(portfolio, type_col, val_col, is_usd, title):
    seps = ".," if is_usd else ", "
    fig = px.pie(portfolio, names=type_col, values=val_col, title=title, hole=0.4, template="plotly_dark")
    fig.update_traces(textinfo='percent+label', hovertemplate="%{label}<br>%{value:.2f}")
    fig.update_layout(separators=seps)
    return fig


def plot_earnings_evolution(earn_df, sym, is_usd, title):
    seps = ".," if is_usd else ", "
    fig = px.bar(earn_df, x='month_year', y='val', title=title, template="plotly_dark")
    fig.update_traces(marker_color='#FFD700', hovertemplate="%{y:.2f}")
    fig.update_layout(separators=seps, yaxis_title=None, xaxis_title=None, yaxis=dict(tickprefix=f"{sym} "))
    return fig
