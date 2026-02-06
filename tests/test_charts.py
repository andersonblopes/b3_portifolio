import pandas as pd
import plotly.graph_objects as go

import src.charts as charts


def test_plot_evolution_returns_figure_with_expected_layout():
    ev_df = pd.DataFrame({"date": pd.to_datetime(["2026-02-01", "2026-02-02"]), "flow": [1.0, 2.0]})
    fig = charts.plot_evolution(ev_df, sym="$", is_usd=True, title="t")
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.tickprefix == "$ "
    assert fig.layout.separators == ".,"


def test_plot_allocation_pie_has_hole_and_separators():
    df = pd.DataFrame({"kind": ["A", "B"], "val": [1, 2]})
    fig = charts.plot_allocation(df, names_col="kind", val_col="val", is_usd=False, title="t")
    assert isinstance(fig, go.Figure)
    assert fig.data[0].hole == 0.4
    assert fig.layout.separators == ", "


def test_plot_earnings_evolution_tickprefix():
    earn_df = pd.DataFrame({"month_year": ["2026-02"], "val": [10.0]})
    fig = charts.plot_earnings_evolution(earn_df, sym="€", is_usd=False, title="t")
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.tickprefix == "€ "


def test_plot_bar_earnings_horizontal_limits_to_10_and_is_horizontal():
    df = pd.DataFrame({"name": [f"a{i}" for i in range(20)], "val": list(range(20))})
    fig = charts.plot_bar_earnings_horizontal(df, x_label="name", y_value="val", sym="R$", is_usd=False, title="t")
    assert isinstance(fig, go.Figure)
    assert fig.data[0].orientation == "h"
    # x is values, y is labels
    assert len(fig.data[0].y) == 10
