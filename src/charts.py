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


def plot_pie_earnings(df, names_col, values_col, is_usd, title):
    seps = ".," if is_usd else ", "
    fig = px.pie(df, names=names_col, values=values_col, title=title, hole=0.3, template="plotly_dark")
    fig.update_traces(textinfo='percent+label', hovertemplate="%{label}<br>%{value:.2f}")
    fig.update_layout(separators=seps)
    return fig


def plot_bar_earnings_horizontal(df, x_label, y_value, sym, is_usd, title):
    seps = ".," if is_usd else ", "
    df_sorted = df.sort_values(y_value, ascending=True).tail(10)
    fig = px.bar(df_sorted, x=y_value, y=x_label, orientation='h', title=title, template="plotly_dark")
    fig.update_traces(marker_color='#00FFAA', hovertemplate="%{x:.2f}")
    fig.update_layout(separators=seps, xaxis_title=None, yaxis_title=None, xaxis=dict(tickprefix=f"{sym} "))
    return fig
