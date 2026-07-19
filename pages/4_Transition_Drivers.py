from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    PALETTE,
    apply_page_style,
    build_transition_index,
    latest_common_year,
    load_data,
    style_plotly,
)

st.set_page_config(
    page_title="Transition Drivers",
    page_icon="🧭",
    layout="wide",
)

apply_page_style()

with st.spinner("Analysing the drivers of renewable electricity adoption..."):
    df = load_data()
    index_df, index_year = build_transition_index(df)

st.title("🧭 Transition Drivers")
st.caption(
    "Investigate the environmental, economic, and structural factors "
    "associated with renewable electricity adoption."
)

carbon_tab, fossil_tab, wealth_tab, quadrant_tab, comparison_tab = st.tabs(
    [
        "🌱 Carbon Intensity",
        "🏭 Fossil Dependence",
        "💶 Economic Wealth",
        "🧭 Strategic Quadrant",
        "⚖️ Country Comparison",
    ]
)


def prepare_driver_data(metric: str) -> tuple[pd.DataFrame, int]:
    year = latest_common_year(
        df,
        [
            "renewables_share_elec",
            metric,
            "population",
        ],
        coverage_ratio=0.70,
    )

    result = (
        df[df["year"].eq(year)]
        .dropna(
            subset=[
                "renewables_share_elec",
                metric,
                "country",
            ]
        )
        .copy()
    )

    result = result[
        np.isfinite(result["renewables_share_elec"])
        & np.isfinite(result[metric])
    ]

    if metric in {
        "gdp_per_capita",
        "energy_per_capita",
    }:
        result = result[result[metric] > 0]

    return result, year


def relationship_strength(value: float) -> str:
    absolute = abs(value)

    if absolute < 0.20:
        return "very weak"
    if absolute < 0.40:
        return "weak"
    if absolute < 0.60:
        return "moderate"
    return "strong"


def driver_scatter(
    data: pd.DataFrame,
    metric: str,
    metric_name: str,
    year: int,
    *,
    log_y: bool = False,
) -> tuple[go.Figure, float]:
    correlation = data[
        [
            "renewables_share_elec",
            metric,
        ]
    ].corr().iloc[0, 1]

    x = data["renewables_share_elec"].to_numpy()
    y = data[metric].to_numpy()

    if log_y:
        fitted = np.log10(y)
        slope, intercept = np.polyfit(x, fitted, 1)
        trend_x = np.linspace(x.min(), x.max(), 150)
        trend_y = 10 ** (slope * trend_x + intercept)
    else:
        slope, intercept = np.polyfit(x, y, 1)
        trend_x = np.linspace(x.min(), x.max(), 150)
        trend_y = slope * trend_x + intercept

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["renewables_share_elec"],
            y=data[metric],
            mode="markers",
            text=data["country"],
            customdata=np.column_stack(
                [
                    data["population"].fillna(0) / 1_000_000,
                ]
            ),
            marker=dict(
                size=10,
                color=data["renewables_share_elec"],
                colorscale=[
                    [0.00, "#64748B"],
                    [0.45, "#38BDF8"],
                    [1.00, "#22C55E"],
                ],
                opacity=0.80,
                line=dict(
                    color="white",
                    width=0.7,
                ),
                colorbar=dict(
                    title="Renewable<br>share",
                    ticksuffix="%",
                ),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Renewable share: %{x:.1f}%<br>"
                f"{metric_name}: "
                "%{y:,.1f}<br>"
                "Population: %{customdata[0]:,.1f} million"
                "<extra></extra>"
            ),
            name="Countries",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=trend_x,
            y=trend_y,
            mode="lines",
            line=dict(
                color=PALETTE["orange"],
                width=3,
                dash="dash",
            ),
            hoverinfo="skip",
            name="Estimated trend",
        )
    )

    fig.add_vline(
        x=data["renewables_share_elec"].median(),
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    fig.add_hline(
        y=data[metric].median(),
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    fig.update_layout(
        title=f"Renewable Electricity vs {metric_name} ({year})",
    )

    fig.update_xaxes(
        title="Renewable electricity share (%)",
        ticksuffix="%",
        range=[0, 105],
    )

    fig.update_yaxes(
        title=metric_name,
        type="log" if log_y else "linear",
    )

    style_plotly(
        fig,
        height=670,
        show_legend=True,
    )

    return fig, correlation


# =========================================================
# CARBON TAB
# =========================================================

with carbon_tab:
    carbon_df, carbon_year = prepare_driver_data(
        "carbon_intensity_elec"
    )

    fig, correlation = driver_scatter(
        carbon_df,
        "carbon_intensity_elec",
        "Electricity carbon intensity (gCO₂/kWh)",
        carbon_year,
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("Countries included", len(carbon_df))
    k2.metric("Correlation", f"{correlation:.2f}")
    k3.metric("Relationship", relationship_strength(correlation).title())

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.info(
        f"""
**Key finding:** The relationship is
**{relationship_strength(correlation)} and
{"negative" if correlation < 0 else "positive"}**
(correlation = **{correlation:.2f}**).

Countries with larger renewable electricity shares generally have
lower carbon intensity, supporting the environmental value of
renewable deployment.
"""
    )

# =========================================================
# FOSSIL TAB
# =========================================================

with fossil_tab:
    fossil_df, fossil_year = prepare_driver_data(
        "fossil_share_elec"
    )

    fig, correlation = driver_scatter(
        fossil_df,
        "fossil_share_elec",
        "Fossil electricity share (%)",
        fossil_year,
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("Countries included", len(fossil_df))
    k2.metric("Correlation", f"{correlation:.2f}")
    k3.metric("Relationship", relationship_strength(correlation).title())

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Policy insight:** The
**{relationship_strength(correlation)} negative relationship**
shows that renewable electricity is associated with lower fossil
dependence. The transition succeeds when renewables replace fossil
generation rather than simply being added on top of it.
"""
    )

# =========================================================
# WEALTH TAB
# =========================================================

with wealth_tab:
    if "gdp_per_capita" not in df.columns:
        st.error(
            "GDP per capita is unavailable. Confirm that utils.py "
            "creates it from GDP and population."
        )
    else:
        wealth_df, wealth_year = prepare_driver_data(
            "gdp_per_capita"
        )

        fig, correlation = driver_scatter(
            wealth_df,
            "gdp_per_capita",
            "GDP per capita",
            wealth_year,
            log_y=True,
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("Countries included", len(wealth_df))
        k2.metric("Correlation", f"{correlation:.2f}")
        k3.metric(
            "Relationship",
            relationship_strength(correlation).title(),
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )

        st.info(
            f"""
**Economic insight:** The relationship is
**{relationship_strength(correlation)}**
(correlation = **{correlation:.2f}**).

Economic wealth alone does not guarantee renewable leadership.
Natural resources, energy policy, grid infrastructure, and long-term
investment also influence transition success.
"""
        )

# =========================================================
# QUADRANT TAB
# =========================================================

with quadrant_tab:
    quadrant_data = index_df.copy()

    renewable_median = quadrant_data[
        "renewables_share_elec"
    ].median()

    carbon_median = quadrant_data[
        "carbon_intensity_elec"
    ].median()

    quadrant_data["transition_group"] = np.select(
        [
            quadrant_data["renewables_share_elec"].ge(
                renewable_median
            )
            & quadrant_data["carbon_intensity_elec"].lt(
                carbon_median
            ),

            quadrant_data["renewables_share_elec"].ge(
                renewable_median
            )
            & quadrant_data["carbon_intensity_elec"].ge(
                carbon_median
            ),

            quadrant_data["renewables_share_elec"].lt(
                renewable_median
            )
            & quadrant_data["carbon_intensity_elec"].lt(
                carbon_median
            ),
        ],
        [
            "Transition Leaders",
            "Renewable Growth, Carbon Challenge",
            "Low-Renewable, Lower-Carbon Mix",
        ],
        default="Transition Laggards",
    )

    quadrant_colors = {
        "Transition Leaders": PALETTE["teal"],
        "Renewable Growth, Carbon Challenge": PALETTE["orange"],
        "Low-Renewable, Lower-Carbon Mix": PALETTE["blue"],
        "Transition Laggards": PALETTE["red"],
    }

    fig = px.scatter(
        quadrant_data,
        x="renewables_share_elec",
        y="carbon_intensity_elec",
        color="transition_group",
        hover_name="country",
        color_discrete_map=quadrant_colors,
        title=(
            "Strategic Energy-Transition Position "
            f"({index_year})"
        ),
        labels={
            "renewables_share_elec":
                "Renewable electricity share (%)",
            "carbon_intensity_elec":
                "Carbon intensity (gCO₂/kWh)",
            "transition_group":
                "Transition group",
        },
        custom_data=[
            "renewable_improvement",
            "fossil_share_elec",
            "transition_performance_index",
        ],
    )

    fig.update_traces(
        marker=dict(
            size=11,
            opacity=0.80,
            line=dict(color="white", width=0.7),
        ),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Renewable share: %{x:.1f}%<br>"
            "Carbon intensity: %{y:.0f} gCO₂/kWh<br>"
            "Improvement: %{customdata[0]:+.1f} pp<br>"
            "Fossil share: %{customdata[1]:.1f}%<br>"
            "Transition index: %{customdata[2]:.1f}/100"
            "<extra></extra>"
        ),
    )

    fig.add_vline(
        x=renewable_median,
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    fig.add_hline(
        y=carbon_median,
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    fig.update_xaxes(
        range=[0, 105],
        ticksuffix="%",
    )

    style_plotly(
        fig,
        height=700,
        show_legend=True,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    group_counts = (
        quadrant_data["transition_group"]
        .value_counts()
        .reindex(
            list(quadrant_colors.keys()),
            fill_value=0,
        )
    )

    q1, q2, q3, q4 = st.columns(4)

    for column, group_name in zip(
        [q1, q2, q3, q4],
        quadrant_colors.keys(),
    ):
        column.metric(
            group_name,
            int(group_counts[group_name]),
        )

    st.info(
        """
**Decision insight:** Strong transition leaders combine high
renewable electricity with low carbon intensity. Countries in the
laggard quadrant require the most urgent policy and infrastructure
support.
"""
    )

# =========================================================
# COMPARISON TAB
# =========================================================

with comparison_tab:
    countries = sorted(df["country"].dropna().unique())

    defaults = [
        country
        for country in [
            "Germany",
            "India",
            "China",
            "United States",
            "Denmark",
        ]
        if country in countries
    ]

    selected = st.multiselect(
        "Select between 2 and 6 countries",
        countries,
        default=defaults,
        max_selections=6,
    )

    if len(selected) < 2:
        st.warning("Select at least two countries.")
    else:
        comparison_df = df[
            df["country"].isin(selected)
        ].copy()

        coverage = (
            comparison_df.dropna(
                subset=[
                    "renewables_share_elec",
                    "fossil_share_elec",
                    "carbon_intensity_elec",
                ]
            )
            .groupby("year")["country"]
            .nunique()
        )

        common_years = coverage[
            coverage.eq(len(selected))
        ].index.tolist()

        comparison_year = (
            int(max(common_years))
            if common_years
            else int(comparison_df["year"].max())
        )

        current = comparison_df[
            comparison_df["year"].eq(comparison_year)
        ].dropna(
            subset=[
                "renewables_share_elec",
                "fossil_share_elec",
                "carbon_intensity_elec",
            ]
        )

        metric_long = current.melt(
            id_vars="country",
            value_vars=[
                "renewables_share_elec",
                "fossil_share_elec",
                "carbon_intensity_elec",
            ],
            var_name="Metric",
            value_name="Value",
        )

        metric_long["Metric"] = metric_long["Metric"].map(
            {
                "renewables_share_elec": "Renewable share",
                "fossil_share_elec": "Fossil share",
                "carbon_intensity_elec": "Carbon intensity",
            }
        )

        fig = px.bar(
            metric_long,
            x="country",
            y="Value",
            color="country",
            facet_col="Metric",
            facet_col_wrap=3,
            title=(
                f"Selected-Country Transition Comparison "
                f"({comparison_year})"
            ),
            labels={
                "country": "",
                "Value": "Value",
            },
        )

        fig.for_each_annotation(
            lambda annotation: annotation.update(
                text=annotation.text.split("=")[-1]
            )
        )
        fig.update_layout(showlegend=False)

        style_plotly(
            fig,
            height=520,
            show_legend=False,
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )

        st.dataframe(
            current[
                [
                    "country",
                    "renewables_share_elec",
                    "fossil_share_elec",
                    "carbon_intensity_elec",
                ]
            ]
            .sort_values(
                "renewables_share_elec",
                ascending=False,
            )
            .rename(
                columns={
                    "country": "Country",
                    "renewables_share_elec":
                        "Renewable Share (%)",
                    "fossil_share_elec":
                        "Fossil Share (%)",
                    "carbon_intensity_elec":
                        "Carbon Intensity",
                }
            ),
            width="stretch",
            hide_index=True,
        )

st.divider()
st.caption(
    "Correlation describes association, not direct causation. "
    "Data source: Our World in Data Energy Dataset."
)
