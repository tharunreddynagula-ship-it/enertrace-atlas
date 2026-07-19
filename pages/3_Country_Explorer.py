from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    PALETTE,
    apply_page_style,
    load_data,
    style_plotly,
)

st.set_page_config(
    page_title="Country Explorer",
    page_icon="🔍",
    layout="wide",
)

apply_page_style()

with st.spinner("Preparing the interactive country explorer..."):
    df = load_data()

st.title("🔍 Country Explorer")
st.caption(
    "Explore one country's transition in depth or compare multiple "
    "countries across renewable adoption, fossil dependence, and "
    "carbon intensity."
)

single_tab, comparison_tab = st.tabs(
    [
        "🔎 Single Country",
        "⚖️ Compare Countries",
    ]
)

countries = sorted(df["country"].dropna().unique())

# =========================================================
# TAB 1 — SINGLE COUNTRY
# =========================================================

with single_tab:
    control_left, control_right = st.columns([1, 2])

    with control_left:
        default_country = (
            "Germany" if "Germany" in countries else countries[0]
        )

        country = st.selectbox(
            "Choose a country",
            countries,
            index=countries.index(default_country),
        )

    country_all = (
        df[df["country"].eq(country)]
        .sort_values("year")
        .copy()
    )

    available_years = sorted(country_all["year"].unique())

    with control_right:
        selected_years = st.slider(
            "Select analysis period",
            min_value=int(min(available_years)),
            max_value=int(max(available_years)),
            value=(
                int(min(available_years)),
                int(max(available_years)),
            ),
        )

    cdf = country_all[
        country_all["year"].between(
            selected_years[0],
            selected_years[1],
        )
    ].copy()

    latest = cdf.dropna(
        subset=[
            "renewables_share_elec",
            "fossil_share_elec",
        ]
    ).tail(1)

    earliest = cdf.dropna(
        subset=["renewables_share_elec"]
    ).head(1)

    if latest.empty:
        st.warning(
            "The selected period does not contain sufficient energy data."
        )
    else:
        latest_row = latest.iloc[0]

        renewable_change = np.nan
        if not earliest.empty:
            renewable_change = (
                latest_row["renewables_share_elec"]
                - earliest.iloc[0]["renewables_share_elec"]
            )

        k1, k2, k3, k4 = st.columns(4)

        k1.metric(
            "Latest available year",
            int(latest_row["year"]),
        )

        k2.metric(
            "Renewable electricity",
            f"{latest_row['renewables_share_elec']:.1f}%",
            (
                f"{renewable_change:+.1f} pp"
                if pd.notna(renewable_change)
                else None
            ),
        )

        k3.metric(
            "Fossil electricity",
            f"{latest_row['fossil_share_elec']:.1f}%",
        )

        carbon_value = latest_row.get(
            "carbon_intensity_elec",
            np.nan,
        )

        k4.metric(
            "Carbon intensity",
            (
                f"{carbon_value:.0f} gCO₂/kWh"
                if pd.notna(carbon_value)
                else "No data"
            ),
        )

        summary_tab, technology_tab, carbon_tab = st.tabs(
            [
                "📈 Transition Trend",
                "🌞 Renewable Mix",
                "🌱 Carbon & Demand",
            ]
        )

        with summary_tab:
            trend = cdf.melt(
                id_vars=["year", "country"],
                value_vars=[
                    "renewables_share_elec",
                    "fossil_share_elec",
                ],
                var_name="Metric",
                value_name="Share",
            )

            trend["Metric"] = trend["Metric"].map(
                {
                    "renewables_share_elec": "Renewables",
                    "fossil_share_elec": "Fossil fuels",
                }
            )

            trend_fig = px.line(
                trend.dropna(),
                x="year",
                y="Share",
                color="Metric",
                markers=True,
                title=f"Electricity Transition Trend — {country}",
                color_discrete_map={
                    "Renewables": PALETTE["sky"],
                    "Fossil fuels": PALETTE["orange"],
                },
                labels={
                    "year": "Year",
                    "Share": "Share of electricity (%)",
                },
            )

            trend_fig.update_traces(
                line=dict(width=4),
                marker=dict(size=6),
            )
            trend_fig.update_yaxes(
                range=[0, 105],
                ticksuffix="%",
            )
            style_plotly(
                trend_fig,
                height=560,
                show_legend=True,
            )

            st.plotly_chart(
                trend_fig,
                width="stretch",
                config={"displayModeBar": False},
            )

        with technology_tab:
            mix_columns = [
                "solar_share_elec",
                "wind_share_elec",
                "hydro_share_elec",
            ]

            mix = cdf.melt(
                id_vars=["year"],
                value_vars=mix_columns,
                var_name="Source",
                value_name="Share",
            )

            mix["Source"] = mix["Source"].map(
                {
                    "solar_share_elec": "Solar",
                    "wind_share_elec": "Wind",
                    "hydro_share_elec": "Hydropower",
                }
            )

            mix_fig = px.area(
                mix.dropna(),
                x="year",
                y="Share",
                color="Source",
                title=f"Renewable Technology Mix — {country}",
                color_discrete_map={
                    "Solar": PALETTE["orange"],
                    "Wind": PALETTE["blue"],
                    "Hydropower": PALETTE["teal"],
                },
                labels={
                    "year": "Year",
                    "Share": "Share of electricity (%)",
                },
            )

            mix_fig.update_yaxes(ticksuffix="%")
            style_plotly(
                mix_fig,
                height=560,
                show_legend=True,
            )

            st.plotly_chart(
                mix_fig,
                width="stretch",
                config={"displayModeBar": False},
            )

        with carbon_tab:
            available_metrics = [
                column
                for column in [
                    "carbon_intensity_elec",
                    "electricity_generation",
                    "population",
                    "gdp",
                ]
                if column in cdf.columns
            ]

            metric_names = {
                "carbon_intensity_elec":
                    "Carbon intensity (gCO₂/kWh)",
                "electricity_generation":
                    "Electricity generation",
                "population":
                    "Population",
                "gdp":
                    "GDP",
            }

            selected_metric = st.selectbox(
                "Select supporting indicator",
                available_metrics,
                format_func=lambda item: metric_names[item],
            )

            support_fig = px.line(
                cdf.dropna(subset=[selected_metric]),
                x="year",
                y=selected_metric,
                markers=True,
                title=(
                    f"{metric_names[selected_metric]} — {country}"
                ),
                labels={
                    "year": "Year",
                    selected_metric:
                        metric_names[selected_metric],
                },
            )

            support_fig.update_traces(
                line=dict(
                    width=4,
                    color=PALETTE["teal"],
                ),
                marker=dict(size=6),
            )

            style_plotly(
                support_fig,
                height=540,
                show_legend=False,
            )

            st.plotly_chart(
                support_fig,
                width="stretch",
                config={"displayModeBar": False},
            )

        # Automatic insight
        latest_renewable = latest_row["renewables_share_elec"]
        latest_fossil = latest_row["fossil_share_elec"]

        if pd.notna(renewable_change):
            direction = (
                "increased" if renewable_change >= 0 else "decreased"
            )
            change_text = (
                f"{direction} by **{abs(renewable_change):.1f} "
                "percentage points**"
            )
        else:
            change_text = "could not be calculated for the period"

        st.info(
            f"""
**Country insight**

Between **{selected_years[0]}** and **{selected_years[1]}**,
renewable electricity in **{country}** {change_text}.

The latest available mix contains
**{latest_renewable:.1f}% renewable electricity** and
**{latest_fossil:.1f}% fossil-fuel electricity**.

This indicates a
**{"stronger clean-energy position" if latest_renewable > latest_fossil else "continued dependence on fossil generation"}**.
"""
        )

        download_columns = [
            column
            for column in [
                "country",
                "year",
                "renewables_share_elec",
                "fossil_share_elec",
                "carbon_intensity_elec",
                "solar_share_elec",
                "wind_share_elec",
                "hydro_share_elec",
                "electricity_generation",
                "population",
                "gdp",
            ]
            if column in cdf.columns
        ]

        st.download_button(
            "⬇️ Download selected country data",
            data=cdf[download_columns].to_csv(index=False),
            file_name=(
                f"{country.lower().replace(' ', '_')}_"
                f"energy_transition.csv"
            ),
            mime="text/csv",
        )

# =========================================================
# TAB 2 — COUNTRY COMPARISON
# =========================================================

with comparison_tab:
    default_comparison = [
        country
        for country in [
            "Germany",
            "India",
            "China",
            "United States",
        ]
        if country in countries
    ]

    selected_countries = st.multiselect(
        "Select between 2 and 6 countries",
        countries,
        default=default_comparison,
        max_selections=6,
    )

    if len(selected_countries) < 2:
        st.warning("Select at least two countries for comparison.")
    else:
        comparison_data = df[
            df["country"].isin(selected_countries)
        ].copy()

        common_year_counts = (
            comparison_data.dropna(
                subset=[
                    "renewables_share_elec",
                    "fossil_share_elec",
                    "carbon_intensity_elec",
                ]
            )
            .groupby("year")["country"]
            .nunique()
        )

        common_years = common_year_counts[
            common_year_counts.eq(len(selected_countries))
        ].index.tolist()

        if common_years:
            comparison_year = int(max(common_years))
        else:
            comparison_year = int(
                comparison_data["year"].max()
            )

        current = comparison_data[
            comparison_data["year"].eq(comparison_year)
        ].dropna(
            subset=[
                "renewables_share_elec",
                "fossil_share_elec",
            ]
        )

        st.caption(
            f"Comparison year: {comparison_year}. "
            "The dashboard uses the latest year with strong common coverage."
        )

        trend_metric = st.radio(
            "Trend to compare",
            [
                "Renewable electricity",
                "Fossil electricity",
                "Carbon intensity",
            ],
            horizontal=True,
        )

        metric_map = {
            "Renewable electricity": "renewables_share_elec",
            "Fossil electricity": "fossil_share_elec",
            "Carbon intensity": "carbon_intensity_elec",
        }

        trend_column = metric_map[trend_metric]

        comparison_fig = px.line(
            comparison_data.dropna(subset=[trend_column]),
            x="year",
            y=trend_column,
            color="country",
            markers=True,
            title=f"{trend_metric} Comparison",
            labels={
                "year": "Year",
                trend_column: trend_metric,
                "country": "Country",
            },
        )

        comparison_fig.update_traces(
            line=dict(width=3),
            marker=dict(size=5),
        )

        if trend_column != "carbon_intensity_elec":
            comparison_fig.update_yaxes(ticksuffix="%")

        style_plotly(
            comparison_fig,
            height=570,
            show_legend=True,
        )

        st.plotly_chart(
            comparison_fig,
            width="stretch",
            config={"displayModeBar": False},
        )

        st.subheader("Latest Common-Year Scorecards")

        long_current = current.melt(
            id_vars=["country"],
            value_vars=[
                "renewables_share_elec",
                "fossil_share_elec",
                "carbon_intensity_elec",
            ],
            var_name="Metric",
            value_name="Value",
        )

        long_current["Metric"] = long_current["Metric"].map(
            {
                "renewables_share_elec": "Renewable share",
                "fossil_share_elec": "Fossil share",
                "carbon_intensity_elec": "Carbon intensity",
            }
        )

        score_fig = px.bar(
            long_current,
            x="country",
            y="Value",
            color="country",
            facet_col="Metric",
            facet_col_wrap=3,
            title=(
                f"Multi-Metric Country Comparison ({comparison_year})"
            ),
            labels={
                "country": "",
                "Value": "Value",
            },
        )

        score_fig.for_each_annotation(
            lambda annotation: annotation.update(
                text=annotation.text.split("=")[-1]
            )
        )

        score_fig.update_layout(
            showlegend=False,
        )
        style_plotly(
            score_fig,
            height=500,
            show_legend=False,
        )

        st.plotly_chart(
            score_fig,
            width="stretch",
            config={"displayModeBar": False},
        )

        best_renewable = current.loc[
            current["renewables_share_elec"].idxmax()
        ]

        lowest_carbon_data = current.dropna(
            subset=["carbon_intensity_elec"]
        )

        if not lowest_carbon_data.empty:
            cleanest_comparison = lowest_carbon_data.loc[
                lowest_carbon_data[
                    "carbon_intensity_elec"
                ].idxmin()
            ]

            cleanest_text = (
                f"**{cleanest_comparison['country']}** has the "
                "lowest carbon intensity among the selected countries."
            )
        else:
            cleanest_text = (
                "Carbon-intensity data are incomplete for this comparison."
            )

        st.success(
            f"""
**Comparison insight:** **{best_renewable['country']}** has the highest
renewable electricity share among the selected countries at
**{best_renewable['renewables_share_elec']:.1f}%**.
{cleanest_text}
"""
        )

st.divider()
st.caption(
    "Data source: Our World in Data Energy Dataset. "
    "Country insights depend on available annual observations."
)
