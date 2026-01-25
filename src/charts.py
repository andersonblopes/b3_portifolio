import plotly.express as px


def plot_evolution(ev_df, sym, is_usd, title):
    # Definir separador: USD "." | BRL ","
    seps = ".," if is_usd else ", "

    fig = px.area(ev_df, x='date', y='flow', title=title, template="plotly_dark")
    fig.update_traces(
        line_color='#00FFAA',
        fillcolor='rgba(0, 255, 170, 0.2)',
        hovertemplate=f"%{{y:.2f}}"  # O separador global do layout cuidará do resto
    )
    fig.update_layout(
        separators=seps,
        yaxis_title=None,
        xaxis_title=None,
        yaxis=dict(tickprefix=f"{sym} ", tickformat=".2f")
    )
    return fig


def plot_allocation(portfolio, type_col, val_col, is_usd, title):
    seps = ".," if is_usd else ", "
    fig = px.pie(portfolio, names=type_col, values=val_col, title=title, hole=0.4, template="plotly_dark")
    fig.update_traces(
        textinfo='percent+label',
        hovertemplate=f"%{{label}}<br>%{{value:.2f}}",
        marker=dict(line=dict(color='#000', width=1))
    )
    fig.update_layout(separators=seps)
    return fig
