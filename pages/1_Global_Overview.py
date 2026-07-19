from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils import (
    PALETTE,
    apply_page_style,
    load_data,
    style_plotly,
    weighted_global_renewable_trend,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Global Overview",
    page_icon="🌍",
    layout="wide",
)

apply_page_style()
# =========================================================
# LOAD DATA
# =========================================================

with st.spinner("Preparing the global energy-transition overview..."):
    df = load_data()
    trend = weighted_global_renewable_trend(df)

# =========================================================
# PAGE HEADER
# =========================================================

st.title("🌍 Global Transition Overview")
st.caption(
    "Track how renewable electricity has grown globally and explore "
    "how adoption has changed across countries from 2000 onward."
)

start_row = trend.iloc[0]
end_row = trend.iloc[-1]
increase = (
    end_row["renewables_share_elec"]
    - start_row["renewables_share_elec"]
)

# =========================================================
# KPI CARDS
# =========================================================

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    f"Renewable share in {int(start_row['year'])}",
    f"{start_row['renewables_share_elec']:.1f}%",
)

k2.metric(
    f"Renewable share in {int(end_row['year'])}",
    f"{end_row['renewables_share_elec']:.1f}%",
)

k3.metric(
    "Long-term increase",
    f"{increase:.1f} pp",
)

k4.metric(
    "Years analysed",
    f"{int(end_row['year'] - start_row['year'] + 1)}",
)

# =========================================================
# GLOBAL TREND
# =========================================================

trend_fig = px.area(
    trend,
    x="year",
    y="renewables_share_elec",
    markers=True,
    title=(
        "Renewables Are Taking a Growing Share "
        "of Global Electricity Generation"
    ),
    labels={
        "year": "Year",
        "renewables_share_elec":
            "Renewable electricity share (%)",
    },
)

trend_fig.update_traces(
    line=dict(
        width=4,
        color=PALETTE["sky"],
    ),
    marker=dict(
        size=6,
        color=PALETTE["teal"],
    ),
    fillcolor="rgba(56, 189, 248, 0.18)",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Renewable electricity share: %{y:.1f}%"
        "<extra></extra>"
    ),
)

trend_fig.update_yaxes(
    ticksuffix="%",
)

style_plotly(
    trend_fig,
    height=540,
    show_legend=False,
)

st.plotly_chart(
    trend_fig,
    width="stretch",
    config={
        "displayModeBar": False,
    },
)

st.info(
    f"""
**Global finding:** Renewable electricity increased from
**{start_row['renewables_share_elec']:.1f}%** in
**{int(start_row['year'])}** to
**{end_row['renewables_share_elec']:.1f}%** in
**{int(end_row['year'])}** — an increase of
**{increase:.1f} percentage points**.
"""
)

# =========================================================
# MAP DATA
# =========================================================

map_df = df[
    df["year"].between(
        int(start_row["year"]),
        int(end_row["year"]),
    )
    & df["iso_code"].notna()
    & df["renewables_share_elec"].notna()
].copy()

map_df["year"] = map_df["year"].astype(int)

latest_map_year = int(
    map_df.groupby("year")["country"]
    .nunique()
    .idxmax()
)

latest = map_df[
    map_df["year"].eq(latest_map_year)
].copy()

# =========================================================
# MAP TABS
# =========================================================

static_tab, animated_tab = st.tabs(
    [
        "🗺️ Current Global Map",
        "▶️ Animated Transition Map",
    ]
)

with static_tab:
    st.subheader(
        f"Renewable Electricity Share Across Countries "
        f"({latest_map_year})"
    )
    st.caption(
        "Hover over a country to see its renewable electricity share."
    )

    static_map = px.choropleth(
        latest,
        locations="iso_code",
        color="renewables_share_elec",
        hover_name="country",
        range_color=(0, 100),
        color_continuous_scale=[
            [0.00, "#071827"],
            [0.25, "#075985"],
            [0.50, "#0EA5E9"],
            [0.75, "#10B981"],
            [1.00, "#22C55E"],
        ],
        labels={
            "renewables_share_elec":
                "Renewable electricity share (%)"
        },
    )

    static_map.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Renewable electricity: %{z:.1f}%"
            "<extra></extra>"
        ),
    )

    static_map.update_layout(
        height=680,
        paper_bgcolor="rgba(7,24,39,0)",
        plot_bgcolor="rgba(7,24,39,0)",
        font=dict(color="#CBD5E1"),
        margin=dict(
            l=0,
            r=0,
            t=20,
            b=0,
        ),
        geo=dict(
            bgcolor="rgba(7,24,39,0)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#64748B",
            showland=True,
            landcolor="#182536",
            showocean=True,
            oceancolor="#07111D",
            showcountries=True,
            countrycolor="rgba(148,163,184,0.35)",
        ),
        coloraxis_colorbar=dict(
            title="Renewable<br>share (%)",
            ticksuffix="%",
        ),
    )

    st.plotly_chart(
        static_map,
        width="stretch",
        config={
            "displayModeBar": False,
        },
    )

with animated_tab:
    st.subheader(
        f"Global Renewable Electricity Transition: "
        f"{int(start_row['year'])}–{int(end_row['year'])}"
    )
    st.caption(
        "Press Play to watch how renewable electricity adoption "
        "changed across the world over time."
    )

    animated_map = px.choropleth(
        map_df,
        locations="iso_code",
        color="renewables_share_elec",
        hover_name="country",
        animation_frame="year",
        range_color=(0, 100),
        color_continuous_scale=[
            [0.00, "#071827"],
            [0.25, "#075985"],
            [0.50, "#0EA5E9"],
            [0.75, "#10B981"],
            [1.00, "#22C55E"],
        ],
        labels={
            "renewables_share_elec":
                "Renewable electricity share (%)"
        },
    )

    animated_map.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Renewable electricity: %{z:.1f}%"
            "<extra></extra>"
        ),
    )

    animated_map.update_layout(
        height=700,
        paper_bgcolor="rgba(7,24,39,0)",
        plot_bgcolor="rgba(7,24,39,0)",
        font=dict(color="#CBD5E1"),
        margin=dict(
            l=0,
            r=0,
            t=20,
            b=30,
        ),
        geo=dict(
            bgcolor="rgba(7,24,39,0)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#64748B",
            showland=True,
            landcolor="#182536",
            showocean=True,
            oceancolor="#07111D",
            showcountries=True,
            countrycolor="rgba(148,163,184,0.35)",
        ),
        coloraxis_colorbar=dict(
            title="Renewable<br>share (%)",
            ticksuffix="%",
        ),
    )

    # Make the Play button more readable in the dark theme.
    animated_map.layout.updatemenus[0].buttons[0].args[1][
        "frame"
    ]["duration"] = 450

    animated_map.layout.updatemenus[0].buttons[0].args[1][
        "transition"
    ]["duration"] = 250

    st.plotly_chart(
        animated_map,
        width="stretch",
        config={
            "displayModeBar": False,
        },
    )

    st.success(
        """
**How to read the animation:** Countries moving from dark blue
toward green are increasing the share of electricity generated
from renewable sources.
"""
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption(
    "Data source: Our World in Data Energy Dataset. "
    "Global trend is weighted by electricity generation."
)
