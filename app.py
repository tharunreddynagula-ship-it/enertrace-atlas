from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from utils import (
    PALETTE,
    apply_page_style,
    build_transition_index,
    find_hero_image,
    load_data,
    style_plotly,
    transition_quadrants,
    weighted_global_renewable_trend,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Global Energy Transition Analytics",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_page_style()

# =========================================================
# LOAD NOTEBOOK-ALIGNED DATA
# =========================================================

with st.spinner("Analysing global energy-transition data..."):
    df = load_data()
    index_df, analysis_year = build_transition_index(df)
    quadrant_df = transition_quadrants(index_df)
    global_trend = weighted_global_renewable_trend(df)

leader = index_df.iloc[0]
fastest = index_df.loc[index_df["renewable_improvement"].idxmax()]
cleanest = index_df.loc[index_df["carbon_intensity_elec"].idxmin()]
median_score = index_df["transition_performance_index"].median()

start_row = global_trend.iloc[0]
end_row = global_trend.iloc[-1]
global_increase = (
    end_row["renewables_share_elec"]
    - start_row["renewables_share_elec"]
)

# =========================================================
# CINEMATIC HERO
# =========================================================

hero_path = find_hero_image()

if hero_path is not None:
    hero_image = base64.b64encode(
        hero_path.read_bytes()
    ).decode("utf-8")
    hero_background = (
        "url('data:image/png;base64,"
        + hero_image
        + "')"
    )
else:
    hero_background = (
        "linear-gradient(125deg, "
        "#123047 0%, #0B4F6C 52%, #065F46 100%)"
    )

hero_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Arial, Helvetica, sans-serif;
}}

@keyframes heroZoom {{
    0% {{
        transform: scale(1);
    }}

    100% {{
        transform: scale(1.07);
    }}
}}

@keyframes fadeUp {{
    from {{
        opacity: 0;
        transform: translateY(24px);
    }}

    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

@keyframes badgeReveal {{
    from {{
        opacity: 0;
        transform: translateY(10px);
    }}

    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.hero {{
    position: relative;
    width: 100%;
    height: 420px;
    overflow: hidden;
    border-radius: 24px;
    background: #07111D;
    border: 1px solid rgba(56, 189, 248, 0.24);
    box-shadow: 0 24px 55px rgba(0, 0, 0, 0.36);
}}

.hero-background {{
    position: absolute;
    inset: -3%;
    background-image:
        linear-gradient(
            90deg,
            rgba(2, 10, 20, 0.98) 0%,
            rgba(2, 12, 23, 0.88) 40%,
            rgba(2, 12, 23, 0.38) 72%,
            rgba(2, 12, 23, 0.12) 100%
        ),
        {hero_background};
    background-size: cover;
    background-position: center;
    animation: heroZoom 18s ease-in-out infinite alternate;
    will-change: transform;
}}

.hero-overlay {{
    position: absolute;
    inset: 0;
    background:
        radial-gradient(
            circle at 80% 25%,
            rgba(56, 189, 248, 0.10),
            transparent 28%
        );
    pointer-events: none;
}}

.content {{
    position: relative;
    z-index: 2;
    width: 64%;
    padding: 48px 46px;
    animation: fadeUp 1.05s ease-out both;
}}

.eyebrow {{
    color: #38BDF8;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 14px;
}}

.title {{
    color: white;
    font-size: 55px;
    line-height: 1.03;
    font-weight: 900;
    letter-spacing: -2px;
    margin-bottom: 18px;
}}

.accent {{
    background: linear-gradient(90deg, #38BDF8, #34D399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.subtitle {{
    color: #E2E8F0;
    font-size: 18px;
    line-height: 1.65;
    max-width: 720px;
    margin-bottom: 25px;
}}

.badge {{
    display: inline-block;
    padding: 9px 14px;
    margin-right: 8px;
    margin-bottom: 8px;
    border-radius: 999px;
    color: #E0F2FE;
    font-size: 14px;
    font-weight: 700;
    background: rgba(5, 20, 33, 0.78);
    border: 1px solid rgba(56, 189, 248, 0.35);
    backdrop-filter: blur(7px);
    animation: badgeReveal 0.65s ease-out both;
}}

.badge:nth-of-type(1) {{
    animation-delay: 0.35s;
}}

.badge:nth-of-type(2) {{
    animation-delay: 0.50s;
}}

.badge:nth-of-type(3) {{
    animation-delay: 0.65s;
}}

@media (max-width: 850px) {{
    .content {{
        width: 92%;
        padding: 34px 26px;
    }}

    .title {{
        font-size: 40px;
    }}
}}

@media (prefers-reduced-motion: reduce) {{
    .hero-background,
    .content,
    .badge {{
        animation: none !important;
    }}
}}
</style>
</head>
<body>
<div class="hero">
    <div class="hero-background"></div>
    <div class="hero-overlay"></div>

    <div class="content">
        <div class="eyebrow">
            Global Clean-Energy Intelligence
        </div>

        <div class="title">
            Global Energy<br>
            <span class="accent">Transition Analytics</span>
        </div>

        <div class="subtitle">
            Who is leading, who is falling behind, and why?
            Explore renewable adoption, fossil dependence,
            carbon intensity and long-term progress since 2000.
        </div>

        <span class="badge">
            🌍 {len(index_df)} countries
        </span>

        <span class="badge">
            📅 Final index year {analysis_year}
        </span>

        <span class="badge">
            📊 11 analytical questions
        </span>
    </div>
</div>
</body>
</html>
"""

components.html(
    hero_html,
    height=440,
    scrolling=False,
)

if hero_path is None:
    st.caption(
        "Add images/wind_farm_hero.png to display the cinematic "
        "wind-farm background."
    )

# =========================================================
# CURATED MULTI-TAB EXECUTIVE DASHBOARD
# =========================================================

overview_tab, leaders_tab, strategy_tab, method_tab = st.tabs(
    [
        "📌 Executive Summary",
        "🏆 Leaders & Progress",
        "🧭 Strategic Position",
        "🧪 Methodology",
    ]
)

# ---------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY
# ---------------------------------------------------------

with overview_tab:
    st.subheader("Executive Overview")
    st.caption(
        "A curated summary of the strongest findings from the "
        "11-question analysis notebook."
    )

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Countries evaluated",
        f"{len(index_df)}",
        help=(
            "Countries with complete baseline and final-year data "
            "for all four index components."
        ),
    )

    k2.metric(
        "Overall leader",
        leader["country"],
        f"{leader['transition_performance_index']:.1f}/100",
    )

    k3.metric(
        "Fastest improver",
        fastest["country"],
        f"+{fastest['renewable_improvement']:.1f} pp",
    )

    k4.metric(
        "Cleanest electricity",
        cleanest["country"],
        f"{cleanest['carbon_intensity_elec']:.0f} gCO₂/kWh",
        delta_color="off",
    )

    col_left, col_right = st.columns(
        [1.1, 1],
        gap="large",
    )

    with col_left:
        trend_fig = px.line(
            global_trend,
            x="year",
            y="renewables_share_elec",
            markers=True,
            title=(
                "Global Renewable Electricity Share Has "
                "Accelerated Since 2000"
            ),
            labels={
                "year": "Year",
                "renewables_share_elec":
                    "Renewable electricity share (%)",
            },
        )

        trend_fig.update_traces(
            line=dict(
                color=PALETTE["sky"],
                width=4,
            ),
            marker=dict(
                size=6,
                color=PALETTE["teal"],
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Renewable share: %{y:.1f}%"
                "<extra></extra>"
            ),
        )

        trend_fig.update_yaxes(ticksuffix="%")
        style_plotly(
            trend_fig,
            height=500,
            show_legend=False,
        )

        st.plotly_chart(
            trend_fig,
            width="stretch",
            config={"displayModeBar": False},
        )

    with col_right:
        top10 = (
            index_df.head(10)
            .sort_values(
                "transition_performance_index",
                ascending=True,
            )
        )

        rank_fig = px.bar(
            top10,
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
            title="Top 10 Overall Transition Performers",
            labels={
                "transition_performance_index":
                    "Transition Performance Index",
                "country": "",
            },
            custom_data=[
                "renewables_share_elec",
                "renewable_improvement",
                "fossil_share_elec",
                "carbon_intensity_elec",
            ],
        )

        rank_fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
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

        rank_fig.update_layout(
            coloraxis_showscale=False,
        )
        rank_fig.update_xaxes(range=[0, 105])
        style_plotly(
            rank_fig,
            height=500,
            show_legend=False,
        )

        st.plotly_chart(
            rank_fig,
            width="stretch",
            config={"displayModeBar": False},
        )

    st.info(
        f"""
**Main conclusion**

Global renewable electricity increased from
**{start_row['renewables_share_elec']:.1f}%** in
**{int(start_row['year'])}** to
**{end_row['renewables_share_elec']:.1f}%** in
**{int(end_row['year'])}**, a rise of
**{global_increase:.1f} percentage points**.

However, national progress remains uneven.
**{leader['country']}** leads the final composite ranking,
while the median country scores only
**{median_score:.1f}/100**.
"""
    )

# ---------------------------------------------------------
# TAB 2: LEADERS AND PROGRESS
# ---------------------------------------------------------

with leaders_tab:
    st.subheader("Current Leadership vs Long-Term Progress")
    st.caption(
        "This section separates countries that are already clean "
        "from countries that are improving rapidly."
    )

    left, right = st.columns(2, gap="large")

    with left:
        renewable_leaders = (
            index_df.nlargest(
                15,
                "renewables_share_elec",
            )
            .sort_values(
                "renewables_share_elec"
            )
        )

        renewable_fig = px.bar(
            renewable_leaders,
            x="renewables_share_elec",
            y="country",
            orientation="h",
            text="renewables_share_elec",
            title=(
                f"Highest Renewable Electricity Shares "
                f"({analysis_year})"
            ),
            labels={
                "renewables_share_elec":
                    "Renewable electricity share (%)",
                "country": "",
            },
        )

        renewable_fig.update_traces(
            marker_color=PALETTE["teal"],
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        renewable_fig.update_xaxes(
            range=[0, 105],
            ticksuffix="%",
        )
        style_plotly(
            renewable_fig,
            height=610,
            show_legend=False,
        )

        st.plotly_chart(
            renewable_fig,
            width="stretch",
            config={"displayModeBar": False},
        )

    with right:
        improvers = (
            index_df.nlargest(
                15,
                "renewable_improvement",
            )
            .sort_values(
                "renewable_improvement"
            )
        )

        improvement_fig = px.bar(
            improvers,
            x="renewable_improvement",
            y="country",
            orientation="h",
            text="renewable_improvement",
            title=(
                f"Biggest Renewable Improvements "
                f"(2000–{analysis_year})"
            ),
            labels={
                "renewable_improvement":
                    "Increase in renewable share (pp)",
                "country": "",
            },
        )

        improvement_fig.update_traces(
            marker_color=PALETTE["orange"],
            texttemplate="+%{text:.1f} pp",
            textposition="outside",
            cliponaxis=False,
        )
        style_plotly(
            improvement_fig,
            height=610,
            show_legend=False,
        )

        st.plotly_chart(
            improvement_fig,
            width="stretch",
            config={"displayModeBar": False},
        )

    st.success(
        f"""
**Key distinction:** A country can be a current renewable leader
without having improved rapidly, while another country may still
have a moderate renewable share but be catching up quickly.
The fastest improver is **{fastest['country']}**
with **+{fastest['renewable_improvement']:.1f} percentage points**.
"""
    )

# ---------------------------------------------------------
# TAB 3: STRATEGIC POSITION
# ---------------------------------------------------------

with strategy_tab:
    st.subheader("Which Countries Lead, Catch Up, or Fall Behind?")
    st.caption(
        "Countries are positioned using current renewable share "
        "and improvement since 2000, matching the notebook's "
        "strategic quadrant analysis."
    )

    renewable_median = quadrant_df[
        "renewables_share_elec"
    ].median()

    progress_median = quadrant_df[
        "renewable_improvement"
    ].median()

    position_colors = {
        "Leaders": PALETTE["teal"],
        "Catching Up": PALETTE["orange"],
        "Established but Slower": PALETTE["blue"],
        "Falling Behind": PALETTE["red"],
    }

    quadrant_fig = px.scatter(
        quadrant_df,
        x="renewable_improvement",
        y="renewables_share_elec",
        color="strategic_position",
        hover_name="country",
        color_discrete_map=position_colors,
        title=(
            "Current Renewable Position vs Long-Term Progress"
        ),
        labels={
            "renewable_improvement":
                "Renewable improvement since 2000 (pp)",
            "renewables_share_elec":
                "Current renewable electricity share (%)",
            "strategic_position":
                "Strategic position",
        },
        custom_data=[
            "transition_performance_index",
            "carbon_intensity_elec",
            "fossil_share_elec",
        ],
    )

    quadrant_fig.update_traces(
        marker=dict(
            size=10,
            opacity=0.78,
            line=dict(
                color="white",
                width=0.7,
            ),
        ),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Improvement: %{x:+.1f} pp<br>"
            "Current renewable share: %{y:.1f}%<br>"
            "Transition index: %{customdata[0]:.1f}/100<br>"
            "Carbon intensity: %{customdata[1]:.0f} gCO₂/kWh<br>"
            "Fossil share: %{customdata[2]:.1f}%"
            "<extra></extra>"
        ),
    )

    quadrant_fig.add_vline(
        x=progress_median,
        line_dash="dot",
        line_color=PALETTE["grey"],
    )
    quadrant_fig.add_hline(
        y=renewable_median,
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    quadrant_fig.update_yaxes(
        range=[0, 105],
        ticksuffix="%",
    )
    style_plotly(
        quadrant_fig,
        height=680,
        show_legend=True,
    )

    st.plotly_chart(
        quadrant_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    tier_counts = (
        index_df["performance_tier"]
        .value_counts()
        .reindex(
            [
                "Global Leader",
                "Strong Performer",
                "Emerging Transition",
                "Transition Challenge",
            ],
            fill_value=0,
        )
    )

    t1, t2, t3, t4 = st.columns(4)

    t1.metric(
        "Global Leaders",
        int(tier_counts["Global Leader"]),
    )
    t2.metric(
        "Strong Performers",
        int(tier_counts["Strong Performer"]),
    )
    t3.metric(
        "Emerging Transitions",
        int(tier_counts["Emerging Transition"]),
    )
    t4.metric(
        "Transition Challenges",
        int(tier_counts["Transition Challenge"]),
    )

# ---------------------------------------------------------
# TAB 4: METHODOLOGY
# ---------------------------------------------------------

with method_tab:
    st.subheader("Transparent Scoring Methodology")

    st.markdown(
        """
The final index is a **custom analytical framework** created for
this project. It is not an official international ranking.

Each component is converted into a percentile score from 0 to 100.
The four components are then combined using the notebook's final
weights:
"""
    )

    weight_data = {
        "Component": [
            "Renewable electricity share",
            "Low electricity carbon intensity",
            "Renewable progress since 2000",
            "Low fossil-fuel dependence",
        ],
        "Weight": [35, 25, 20, 20],
    }

    weight_fig = px.bar(
        weight_data,
        x="Weight",
        y="Component",
        orientation="h",
        text="Weight",
        title="What Drives the Final Transition Score?",
        labels={
            "Weight": "Weight (%)",
            "Component": "",
        },
        color="Component",
        color_discrete_sequence=[
            PALETTE["blue"],
            PALETTE["teal"],
            PALETTE["orange"],
            PALETTE["purple"],
        ],
    )

    weight_fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
    )
    weight_fig.update_xaxes(
        range=[0, 40],
        ticksuffix="%",
    )
    style_plotly(
        weight_fig,
        height=470,
        show_legend=False,
    )

    st.plotly_chart(
        weight_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.markdown(
        f"""
### Why the analysis year is {analysis_year}

The raw dataset extends to 2025, but several indicators have
incomplete 2025 country coverage. The dashboard therefore selects
the latest year that maintains strong international coverage for
renewable share, fossil share and carbon intensity.

### Baseline

Long-term progress is measured from **2000** to
**{analysis_year}**.

### Interpretation

A high score requires more than a high renewable share. Strong
performers must also combine:

- lower fossil-fuel dependence,
- lower electricity carbon intensity, and
- meaningful long-term improvement.
"""
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption(
    "Data source: Our World in Data Energy Dataset. "
    "Dashboard methodology follows the uploaded analysis notebook. "
    "The Energy Transition Performance Index is a custom project metric."
)
