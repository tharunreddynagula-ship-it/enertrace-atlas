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
    load_data,
    style_plotly,
)

st.set_page_config(
    page_title="Leaders & Technology",
    page_icon="🏆",
    layout="wide",
)

apply_page_style()

with st.spinner("Preparing leaders, improvers, and technology insights..."):
    df = load_data()
    index_df, analysis_year = build_transition_index(df)

st.title("🏆 Leaders & Technology")
st.caption(
    "Identify current renewable leaders, fastest improvers, and the "
    "technologies driving the global electricity transition."
)

# ---------------------------------------------------------
# Shared data
# ---------------------------------------------------------

latest = (
    df[df["year"].eq(analysis_year)]
    .drop_duplicates("country")
    .copy()
)

leader = index_df.iloc[0]
fastest = index_df.loc[index_df["renewable_improvement"].idxmax()]

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Overall transition leader",
    leader["country"],
    f"{leader['transition_performance_index']:.1f}/100",
)

k2.metric(
    "Fastest renewable improver",
    fastest["country"],
    f"+{fastest['renewable_improvement']:.1f} pp",
)

renewable_leader = latest.dropna(
    subset=["renewables_share_elec"]
).nlargest(1, "renewables_share_elec").iloc[0]

k3.metric(
    "Highest renewable share",
    renewable_leader["country"],
    f"{renewable_leader['renewables_share_elec']:.1f}%",
)

technology_columns = [
    "solar_share_elec",
    "wind_share_elec",
    "hydro_share_elec",
]

technology_complete = latest.dropna(
    subset=technology_columns,
    how="all",
)

k4.metric(
    "Countries with technology data",
    f"{technology_complete['country'].nunique()}",
    f"Year {analysis_year}",
    delta_color="off",
)

ranking_tab, progress_tab, technology_tab, mix_tab = st.tabs(
    [
        "🏅 Overall Rankings",
        "⚡ Fastest Improvers",
        "🌬️ Technology Leaders",
        "📊 Technology Mix",
    ]
)

# =========================================================
# TAB 1 — OVERALL RANKINGS
# =========================================================

with ranking_tab:
    st.subheader("Who Leads the Overall Energy Transition?")
    st.caption(
        "The final index combines renewable adoption, low fossil dependence, "
        "low carbon intensity, and long-term progress."
    )

    top_n = st.slider(
        "Number of countries to display",
        min_value=5,
        max_value=20,
        value=15,
        step=5,
        key="leader_top_n",
    )

    top = (
        index_df.head(top_n)
        .sort_values("transition_performance_index")
    )

    fig = px.bar(
        top,
        x="transition_performance_index",
        y="country",
        orientation="h",
        text="transition_performance_index",
        color="transition_performance_index",
        color_continuous_scale=[
            "#60A5FA",
            "#38BDF8",
            "#22C55E",
        ],
        title=f"Top {top_n} Overall Transition Performers ({analysis_year})",
        labels={
            "transition_performance_index":
                "Energy Transition Performance Index",
            "country": "",
        },
        custom_data=[
            "renewables_share_elec",
            "renewable_improvement",
            "fossil_share_elec",
            "carbon_intensity_elec",
        ],
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Index: %{x:.1f}/100<br>"
            "Renewable share: %{customdata[0]:.1f}%<br>"
            "Improvement: %{customdata[1]:+.1f} pp<br>"
            "Fossil share: %{customdata[2]:.1f}%<br>"
            "Carbon intensity: %{customdata[3]:.0f} gCO₂/kWh"
            "<extra></extra>"
        ),
    )

    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(range=[0, 105])
    style_plotly(fig, height=680, show_legend=False)

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.info(
        f"""
**Key finding:** **{leader['country']}** ranks first overall with a
score of **{leader['transition_performance_index']:.1f}/100**.
This confirms that leadership depends on balanced performance, not
renewable share alone.
"""
    )

# =========================================================
# TAB 2 — FASTEST IMPROVERS
# =========================================================

with progress_tab:
    st.subheader("Which Countries Improved the Most Since 2000?")
    st.caption(
        "This view measures the change in renewable electricity share "
        f"between 2000 and {analysis_year}."
    )

    top_n_progress = st.slider(
        "Number of improvers to display",
        min_value=10,
        max_value=30,
        value=15,
        step=5,
        key="progress_top_n",
    )

    improvers = (
        index_df.nlargest(
            top_n_progress,
            "renewable_improvement",
        )
        .sort_values("renewable_improvement")
    )

    fig = px.bar(
        improvers,
        x="renewable_improvement",
        y="country",
        orientation="h",
        text="renewable_improvement",
        title=(
            f"Top {top_n_progress} Renewable Electricity Improvements "
            f"(2000–{analysis_year})"
        ),
        labels={
            "renewable_improvement":
                "Increase in renewable electricity share (percentage points)",
            "country": "",
        },
        custom_data=[
            "renewable_share_baseline",
            "renewables_share_elec",
            "transition_performance_index",
        ],
    )

    fig.update_traces(
        marker_color=PALETTE["orange"],
        texttemplate="+%{text:.1f} pp",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Improvement: %{x:+.1f} pp<br>"
            "Renewable share in 2000: %{customdata[0]:.1f}%<br>"
            f"Renewable share in {analysis_year}: "
            "%{customdata[1]:.1f}%<br>"
            "Overall transition index: %{customdata[2]:.1f}/100"
            "<extra></extra>"
        ),
    )

    style_plotly(fig, height=680, show_legend=False)

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Key finding:** **{fastest['country']}** recorded the largest increase,
adding **{fastest['renewable_improvement']:.1f} percentage points**
to its renewable electricity share.
"""
    )

# =========================================================
# TAB 3 — TECHNOLOGY LEADERS
# =========================================================

with technology_tab:
    st.subheader("Which Countries Lead in Solar, Wind, and Hydropower?")
    st.caption(
        "Technology leadership differs by geography, infrastructure, "
        "natural resources, and policy."
    )

    source_options = {
        "Solar": "solar_share_elec",
        "Wind": "wind_share_elec",
        "Hydropower": "hydro_share_elec",
    }

    source_name = st.radio(
        "Select renewable technology",
        list(source_options.keys()),
        horizontal=True,
    )

    source_column = source_options[source_name]

    source_data = (
        latest.dropna(subset=[source_column])
        .nlargest(15, source_column)
        .sort_values(source_column)
    )

    source_colors = {
        "Solar": PALETTE["orange"],
        "Wind": PALETTE["blue"],
        "Hydropower": PALETTE["teal"],
    }

    source_fig = px.bar(
        source_data,
        x=source_column,
        y="country",
        orientation="h",
        text=source_column,
        title=f"Top {source_name} Electricity Leaders ({analysis_year})",
        labels={
            source_column: f"{source_name} share of electricity (%)",
            "country": "",
        },
        custom_data=[
            "renewables_share_elec",
            "fossil_share_elec",
        ],
    )

    source_fig.update_traces(
        marker_color=source_colors[source_name],
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"{source_name} share: "
            "%{x:.1f}%<br>"
            "Total renewable share: %{customdata[0]:.1f}%<br>"
            "Fossil share: %{customdata[1]:.1f}%"
            "<extra></extra>"
        ),
    )

    source_fig.update_xaxes(ticksuffix="%")
    style_plotly(source_fig, height=680, show_legend=False)

    st.plotly_chart(
        source_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    top_source = source_data.iloc[-1]

    st.info(
        f"""
**Technology insight:** **{top_source['country']}** has the highest
recorded **{source_name.lower()} electricity share** in the selected
analysis year at **{top_source[source_column]:.1f}%**.
"""
    )

# =========================================================
# TAB 4 — TECHNOLOGY MIX
# =========================================================

with mix_tab:
    st.subheader("How Is the Renewable Technology Mix Changing?")
    st.caption(
        "Compare global average solar, wind, and hydropower shares "
        "over time."
    )

    technology_trend = (
        df.groupby("year", as_index=False)[technology_columns]
        .mean(numeric_only=True)
        .rename(
            columns={
                "solar_share_elec": "Solar",
                "wind_share_elec": "Wind",
                "hydro_share_elec": "Hydropower",
            }
        )
    )

    technology_long = technology_trend.melt(
        id_vars="year",
        var_name="Technology",
        value_name="Average share",
    ).dropna()

    animated = st.toggle(
        "Animate technology growth",
        value=True,
    )

    if animated:
        animation_df = technology_long.copy()
        animation_df["frame_year"] = animation_df["year"]

        mix_fig = px.bar(
            animation_df,
            x="Technology",
            y="Average share",
            color="Technology",
            animation_frame="frame_year",
            range_y=[
                0,
                max(
                    1,
                    float(animation_df["Average share"].max()) * 1.20,
                ),
            ],
            title="Average Renewable Technology Shares Over Time",
            labels={
                "Average share": "Average electricity share (%)",
            },
            color_discrete_map={
                "Solar": PALETTE["orange"],
                "Wind": PALETTE["blue"],
                "Hydropower": PALETTE["teal"],
            },
        )

        mix_fig.update_traces(
            texttemplate="%{y:.1f}%",
            textposition="outside",
        )

        mix_fig.update_layout(
            height=620,
            paper_bgcolor="rgba(7,24,39,0)",
            plot_bgcolor="rgba(7,24,39,0)",
            font=dict(color=PALETTE["light_grey"]),
            showlegend=False,
            margin=dict(l=35, r=35, t=80, b=60),
        )
        mix_fig.update_yaxes(ticksuffix="%")

        if mix_fig.layout.updatemenus:
            mix_fig.layout.updatemenus[0].buttons[0].args[1][
                "frame"
            ]["duration"] = 500
            mix_fig.layout.updatemenus[0].buttons[0].args[1][
                "transition"
            ]["duration"] = 250

    else:
        mix_fig = px.area(
            technology_long,
            x="year",
            y="Average share",
            color="Technology",
            title="Average Renewable Technology Shares Over Time",
            labels={
                "year": "Year",
                "Average share": "Average electricity share (%)",
            },
            color_discrete_map={
                "Solar": PALETTE["orange"],
                "Wind": PALETTE["blue"],
                "Hydropower": PALETTE["teal"],
            },
        )

        mix_fig.update_yaxes(ticksuffix="%")
        style_plotly(mix_fig, height=620, show_legend=True)

    st.plotly_chart(
        mix_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.info(
        """
**Why this matters:** Hydropower remains an important established
technology, while solar and wind reveal the newer direction of the
global electricity transition.
"""
    )

# =========================================================
# DOWNLOAD
# =========================================================

st.divider()

download_columns = [
    "global_rank",
    "country",
    "transition_performance_index",
    "performance_tier",
    "renewables_share_elec",
    "renewable_improvement",
    "fossil_share_elec",
    "carbon_intensity_elec",
]

st.download_button(
    "⬇️ Download transition rankings",
    data=index_df[download_columns].to_csv(index=False),
    file_name=f"energy_transition_rankings_{analysis_year}.csv",
    mime="text/csv",
)

st.caption(
    "Data source: Our World in Data Energy Dataset. "
    "The final ranking is a custom project index."
)
