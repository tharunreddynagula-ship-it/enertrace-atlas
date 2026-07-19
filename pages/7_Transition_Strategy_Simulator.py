from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import (
    PALETTE,
    apply_page_style,
    build_transition_index,
    load_data,
    style_plotly,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Transition Strategy Simulator",
    page_icon="🎯",
    layout="wide",
)

apply_page_style()

# =========================================================
# CONSTANTS AND HELPERS
# =========================================================

WEIGHTS = {
    "renewable_score": 0.35,
    "low_carbon_score": 0.25,
    "progress_score": 0.20,
    "low_fossil_score": 0.20,
}

COMPONENT_LABELS = {
    "renewable_score": "Renewable adoption",
    "low_carbon_score": "Low carbon intensity",
    "progress_score": "Long-term progress",
    "low_fossil_score": "Low fossil dependence",
}

COMPONENT_COLORS = {
    "renewable_score": PALETTE["teal"],
    "low_carbon_score": PALETTE["sky"],
    "progress_score": PALETTE["orange"],
    "low_fossil_score": PALETTE["purple"],
}

RECOMMENDATIONS = {
    "renewable_score": {
        "title": "Accelerate renewable deployment",
        "actions": [
            "Expand utility-scale solar and wind capacity.",
            "Speed up permitting, grid connections, and clean-power procurement.",
            "Pair new renewable capacity with storage and flexible demand.",
        ],
    },
    "low_carbon_score": {
        "title": "Reduce electricity carbon intensity",
        "actions": [
            "Replace high-emission generation with low-carbon electricity.",
            "Strengthen transmission so clean power can reach demand centres.",
            "Use storage, flexibility, and demand response to support a cleaner grid.",
        ],
    },
    "progress_score": {
        "title": "Increase the speed of transition",
        "actions": [
            "Set stable long-term clean-energy targets.",
            "Create a predictable investment and permitting pipeline.",
            "Track annual delivery against measurable transition milestones.",
        ],
    },
    "low_fossil_score": {
        "title": "Lower fossil-fuel dependence",
        "actions": [
            "Develop a managed retirement pathway for fossil generation.",
            "Replace fossil capacity with renewables, storage, and flexible resources.",
            "Align electricity-market incentives with lower-emission generation.",
        ],
    },
}


def classify_tier(
    score: float,
    q25: float,
    q50: float,
    q75: float,
) -> str:
    """Classify a simulated score using today's fixed tier thresholds."""
    if score >= q75:
        return "Global Leader"
    if score >= q50:
        return "Strong Performer"
    if score >= q25:
        return "Emerging Transition"
    return "Transition Challenge"


def next_tier_target(
    score: float,
    q25: float,
    q50: float,
    q75: float,
) -> tuple[str, float | None]:
    """Return the next performance tier and its score threshold."""
    if score < q25:
        return "Emerging Transition", q25
    if score < q50:
        return "Strong Performer", q50
    if score < q75:
        return "Global Leader", q75
    return "Maintain Global Leader status", None


def simulate_country(
    index_df: pd.DataFrame,
    country: str,
    renewable_increase: float,
    fossil_reduction: float,
    carbon_reduction_pct: float,
    q25: float,
    q50: float,
    q75: float,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """
    Replace one country's current metrics, then recalculate percentile
    component scores, transition index, rank, and performance tier.
    """
    scenario = index_df.copy()
    selected_mask = scenario["country"].eq(country)

    current = scenario.loc[selected_mask].iloc[0].copy()

    simulated_renewable = min(
        100.0,
        float(current["renewables_share_elec"]) + renewable_increase,
    )
    simulated_fossil = max(
        0.0,
        float(current["fossil_share_elec"]) - fossil_reduction,
    )
    simulated_carbon = max(
        0.0,
        float(current["carbon_intensity_elec"])
        * (1 - carbon_reduction_pct / 100),
    )

    scenario.loc[
        selected_mask,
        "renewables_share_elec",
    ] = simulated_renewable

    scenario.loc[
        selected_mask,
        "fossil_share_elec",
    ] = simulated_fossil

    scenario.loc[
        selected_mask,
        "carbon_intensity_elec",
    ] = simulated_carbon

    scenario["renewable_improvement"] = (
        scenario["renewables_share_elec"]
        - scenario["renewable_share_baseline"]
    )

    scenario["renewable_score"] = (
        scenario["renewables_share_elec"]
        .rank(method="average", pct=True)
        * 100
    )

    scenario["low_carbon_score"] = (
        scenario["carbon_intensity_elec"]
        .rank(method="average", pct=True, ascending=False)
        * 100
    )

    scenario["progress_score"] = (
        scenario["renewable_improvement"]
        .rank(method="average", pct=True)
        * 100
    )

    scenario["low_fossil_score"] = (
        scenario["fossil_share_elec"]
        .rank(method="average", pct=True, ascending=False)
        * 100
    )

    scenario["transition_performance_index"] = (
        WEIGHTS["renewable_score"] * scenario["renewable_score"]
        + WEIGHTS["low_carbon_score"] * scenario["low_carbon_score"]
        + WEIGHTS["progress_score"] * scenario["progress_score"]
        + WEIGHTS["low_fossil_score"] * scenario["low_fossil_score"]
    ).round(1)

    scenario = (
        scenario.sort_values(
            [
                "transition_performance_index",
                "renewables_share_elec",
            ],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )

    scenario["global_rank"] = np.arange(
        1,
        len(scenario) + 1,
    )

    scenario["performance_tier"] = scenario[
        "transition_performance_index"
    ].apply(
        lambda value: classify_tier(
            value,
            q25,
            q50,
            q75,
        )
    )

    simulated = scenario[
        scenario["country"].eq(country)
    ].iloc[0].copy()

    return current, simulated, scenario


def signed_places(value: int) -> str:
    if value > 0:
        return f"+{value} places"
    if value < 0:
        return f"{value} places"
    return "No change"


# =========================================================
# DATA
# =========================================================

with st.spinner("Preparing the transition strategy model..."):
    df = load_data()
    index_df, analysis_year = build_transition_index(df)

q25, q50, q75 = index_df[
    "transition_performance_index"
].quantile([0.25, 0.50, 0.75])

country_options = sorted(
    index_df["country"].dropna().unique()
)

default_country = (
    "Germany"
    if "Germany" in country_options
    else country_options[0]
)

# =========================================================
# HEADER
# =========================================================

st.title("🎯 Transition Strategy Simulator")
st.caption(
    "Test how renewable expansion, fossil-fuel reduction, and cleaner "
    "electricity could change a country's transition score, global rank, "
    "and performance tier."
)

st.info(
    f"""
**Decision-support model · Analysis year {analysis_year}**

The simulator recalculates the same four-component Energy Transition
Performance Index used throughout the dashboard. Results are illustrative
scenarios—not forecasts, engineering plans, or official policy rankings.
"""
)

# =========================================================
# COUNTRY AND SCENARIO CONTROLS
# =========================================================

control_col, context_col = st.columns(
    [0.40, 0.60],
    gap="large",
)

with control_col:
    st.subheader("1 · Select a country")

    selected_country = st.selectbox(
        "Country",
        country_options,
        index=country_options.index(default_country),
    )

current_country = index_df[
    index_df["country"].eq(selected_country)
].iloc[0]

with context_col:
    st.subheader("Current position")

    current_cards = st.columns(4)

    current_cards[0].metric(
        "Transition score",
        f"{current_country['transition_performance_index']:.1f}/100",
    )

    current_cards[1].metric(
        "Global rank",
        f"#{int(current_country['global_rank'])}",
    )

    current_cards[2].metric(
        "Renewable share",
        f"{current_country['renewables_share_elec']:.1f}%",
    )

    current_cards[3].metric(
        "Current tier",
        current_country["performance_tier"],
    )

st.divider()
st.subheader("2 · Build a transition scenario")
st.caption(
    "Move the controls to test a hypothetical pathway. "
    "The score and rank update automatically."
)

max_renewable_add = max(
    0.0,
    min(
        60.0,
        100.0 - float(
            current_country["renewables_share_elec"]
        ),
    ),
)

max_fossil_reduction = max(
    0.0,
    min(
        60.0,
        float(current_country["fossil_share_elec"]),
    ),
)

slider_1, slider_2, slider_3 = st.columns(3)

with slider_1:
    if max_renewable_add >= 1.0:
        renewable_increase = st.slider(
            "Increase renewable share",
            min_value=0.0,
            max_value=float(round(max_renewable_add, 1)),
            value=float(
                round(
                    min(15.0, max_renewable_add),
                    1,
                )
            ),
            step=1.0,
            format="+%.0f pp",
            help=(
                "Percentage-point increase in renewable electricity share."
            ),
            key=f"renewable_increase_{selected_country}",
        )
    else:
        renewable_increase = 0.0
        st.metric(
            "Renewable increase available",
            "0 pp",
        )
        st.caption(
            "The country is already at or very close to 100% renewable share."
        )

with slider_2:
    if max_fossil_reduction >= 1.0:
        fossil_reduction = st.slider(
            "Reduce fossil electricity share",
            min_value=0.0,
            max_value=float(round(max_fossil_reduction, 1)),
            value=float(
                round(
                    min(20.0, max_fossil_reduction),
                    1,
                )
            ),
            step=1.0,
            format="-%.0f pp",
            help=(
                "Percentage-point reduction in fossil electricity share."
            ),
            key=f"fossil_reduction_{selected_country}",
        )
    else:
        fossil_reduction = 0.0
        st.metric(
            "Fossil reduction available",
            "0 pp",
        )
        st.caption(
            "The country's recorded fossil-electricity share is already zero."
        )

with slider_3:
    carbon_reduction_pct = st.slider(
        "Reduce carbon intensity",
        min_value=0,
        max_value=80,
        value=25,
        step=5,
        format="-%d%%",
        help=(
            "Relative percentage reduction in electricity carbon intensity."
        ),
        key=f"carbon_reduction_{selected_country}",
    )

current, simulated, scenario_df = simulate_country(
    index_df=index_df,
    country=selected_country,
    renewable_increase=renewable_increase,
    fossil_reduction=fossil_reduction,
    carbon_reduction_pct=float(carbon_reduction_pct),
    q25=float(q25),
    q50=float(q50),
    q75=float(q75),
)

score_change = (
    float(simulated["transition_performance_index"])
    - float(current["transition_performance_index"])
)

rank_gain = (
    int(current["global_rank"])
    - int(simulated["global_rank"])
)

tier_changed = (
    simulated["performance_tier"]
    != current["performance_tier"]
)

# =========================================================
# LIVE RESULT CARDS
# =========================================================

st.divider()
st.subheader("3 · Live scenario result")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Simulated score",
    f"{simulated['transition_performance_index']:.1f}/100",
    f"{score_change:+.1f} points",
)

k2.metric(
    "Simulated global rank",
    f"#{int(simulated['global_rank'])}",
    signed_places(rank_gain),
)

k3.metric(
    "Simulated tier",
    simulated["performance_tier"],
    (
        f"From {current['performance_tier']}"
        if tier_changed
        else "Tier unchanged"
    ),
)

k4.metric(
    "Carbon intensity",
    f"{simulated['carbon_intensity_elec']:.0f} gCO₂/kWh",
    (
        f"-{carbon_reduction_pct}%"
        if carbon_reduction_pct > 0
        else "No reduction"
    ),
    delta_color="inverse",
)

# =========================================================
# GAUGE AND RADAR
# =========================================================

gauge_col, radar_col = st.columns(
    [0.46, 0.54],
    gap="large",
)

with gauge_col:
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=float(
                simulated["transition_performance_index"]
            ),
            number={
                "suffix": "/100",
                "font": {
                    "size": 42,
                    "color": "#142033",
                },
            },
            delta={
                "reference": float(
                    current["transition_performance_index"]
                ),
                "valueformat": ".1f",
                "increasing": {
                    "color": PALETTE["teal"],
                },
                "decreasing": {
                    "color": PALETTE["red"],
                },
            },
            title={
                "text": (
                    f"<b>{selected_country}</b><br>"
                    "<span style='font-size:14px;color:#64748B'>"
                    "Simulated Transition Performance Index"
                    "</span>"
                ),
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#94A3B8",
                },
                "bar": {
                    "color": PALETTE["teal"],
                    "thickness": 0.28,
                },
                "bgcolor": "#F8FAFC",
                "borderwidth": 1,
                "bordercolor": "#DCE5EF",
                "steps": [
                    {
                        "range": [0, float(q25)],
                        "color": "#FEE2E2",
                    },
                    {
                        "range": [float(q25), float(q50)],
                        "color": "#FEF3C7",
                    },
                    {
                        "range": [float(q50), float(q75)],
                        "color": "#DBEAFE",
                    },
                    {
                        "range": [float(q75), 100],
                        "color": "#D1FAE5",
                    },
                ],
                "threshold": {
                    "line": {
                        "color": PALETTE["orange"],
                        "width": 4,
                    },
                    "thickness": 0.75,
                    "value": float(
                        current[
                            "transition_performance_index"
                        ]
                    ),
                },
            },
        )
    )

    gauge.update_layout(
        height=520,
        paper_bgcolor="#FFFFFF",
        margin=dict(
            l=35,
            r=35,
            t=85,
            b=35,
        ),
        font=dict(
            family="Arial",
            color="#334155",
        ),
    )

    st.plotly_chart(
        gauge,
        width="stretch",
        config={"displayModeBar": False},
    )

with radar_col:
    radar_categories = [
        COMPONENT_LABELS[key]
        for key in WEIGHTS
    ]

    current_component_values = [
        float(current[key])
        for key in WEIGHTS
    ]

    simulated_component_values = [
        float(simulated[key])
        for key in WEIGHTS
    ]

    radar = go.Figure()

    radar.add_trace(
        go.Scatterpolar(
            r=current_component_values
            + [current_component_values[0]],
            theta=radar_categories
            + [radar_categories[0]],
            fill="toself",
            name="Current",
            line=dict(
                color=PALETTE["grey"],
                width=3,
            ),
            fillcolor="rgba(148,163,184,0.16)",
            hovertemplate=(
                "<b>%{theta}</b><br>"
                "Current score: %{r:.1f}/100"
                "<extra></extra>"
            ),
        )
    )

    radar.add_trace(
        go.Scatterpolar(
            r=simulated_component_values
            + [simulated_component_values[0]],
            theta=radar_categories
            + [radar_categories[0]],
            fill="toself",
            name="Simulated",
            line=dict(
                color=PALETTE["teal"],
                width=4,
            ),
            fillcolor="rgba(0,158,115,0.18)",
            hovertemplate=(
                "<b>%{theta}</b><br>"
                "Simulated score: %{r:.1f}/100"
                "<extra></extra>"
            ),
        )
    )

    radar.update_layout(
        title=dict(
            text="How the Scenario Changes the Four Index Components",
            x=0.02,
            xanchor="left",
        ),
        height=520,
        paper_bgcolor="#FFFFFF",
        font=dict(
            family="Arial",
            color="#334155",
        ),
        margin=dict(
            l=55,
            r=55,
            t=95,
            b=55,
        ),
        polar=dict(
            bgcolor="#FFFFFF",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#DCE5EF",
                linecolor="#CBD5E1",
                tickfont=dict(color="#64748B"),
            ),
            angularaxis=dict(
                gridcolor="#DCE5EF",
                linecolor="#CBD5E1",
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0,
        ),
    )

    st.plotly_chart(
        radar,
        width="stretch",
        config={"displayModeBar": False},
    )

# =========================================================
# COMPONENT CONTRIBUTIONS AND RANKING NEIGHBOURHOOD
# =========================================================

contribution_col, rank_col = st.columns(
    [0.52, 0.48],
    gap="large",
)

with contribution_col:
    contribution_rows = []

    for component, weight in WEIGHTS.items():
        current_contribution = (
            float(current[component]) * weight
        )
        simulated_contribution = (
            float(simulated[component]) * weight
        )

        contribution_rows.append(
            {
                "Component": COMPONENT_LABELS[component],
                "Current contribution": current_contribution,
                "Simulated contribution": simulated_contribution,
                "Change": (
                    simulated_contribution
                    - current_contribution
                ),
                "Color": COMPONENT_COLORS[component],
            }
        )

    contribution_df = pd.DataFrame(
        contribution_rows
    )

    contribution_fig = go.Figure()

    contribution_fig.add_trace(
        go.Bar(
            y=contribution_df["Component"],
            x=contribution_df["Current contribution"],
            orientation="h",
            name="Current",
            marker_color="#CBD5E1",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Current weighted contribution: %{x:.1f} points"
                "<extra></extra>"
            ),
        )
    )

    contribution_fig.add_trace(
        go.Bar(
            y=contribution_df["Component"],
            x=contribution_df["Simulated contribution"],
            orientation="h",
            name="Simulated",
            marker_color=[
                COMPONENT_COLORS[key]
                for key in WEIGHTS
            ],
            text=contribution_df["Simulated contribution"],
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Simulated weighted contribution: %{x:.1f} points"
                "<extra></extra>"
            ),
        )
    )

    contribution_fig.update_layout(
        title=(
            "Which Components Create the Score Improvement?"
        ),
        barmode="group",
    )

    contribution_fig.update_xaxes(
        title="Weighted contribution to final index",
        range=[0, 40],
    )

    contribution_fig.update_yaxes(
        title="",
        categoryorder="array",
        categoryarray=list(
            reversed(
                contribution_df["Component"].tolist()
            )
        ),
    )

    style_plotly(
        contribution_fig,
        height=570,
        show_legend=True,
    )

    st.plotly_chart(
        contribution_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

with rank_col:
    simulated_rank = int(
        simulated["global_rank"]
    )

    rank_window = scenario_df[
        scenario_df["global_rank"].between(
            max(1, simulated_rank - 4),
            min(
                len(scenario_df),
                simulated_rank + 4,
            ),
        )
    ].copy()

    rank_window = rank_window.sort_values(
        "transition_performance_index"
    )

    rank_colors = [
        (
            PALETTE["orange"]
            if country == selected_country
            else PALETTE["blue"]
        )
        for country in rank_window["country"]
    ]

    rank_fig = go.Figure(
        go.Bar(
            x=rank_window[
                "transition_performance_index"
            ],
            y=rank_window["country"],
            orientation="h",
            marker_color=rank_colors,
            text=rank_window["global_rank"],
            texttemplate="Rank #%{text}",
            textposition="outside",
            cliponaxis=False,
            customdata=np.column_stack(
                [
                    rank_window["global_rank"],
                    rank_window["performance_tier"],
                    rank_window[
                        "renewables_share_elec"
                    ],
                ]
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Transition score: %{x:.1f}/100<br>"
                "Global rank: #%{customdata[0]}<br>"
                "Tier: %{customdata[1]}<br>"
                "Renewable share: %{customdata[2]:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    rank_fig.update_layout(
        title=(
            "Simulated Position Among Nearby Countries"
        ),
    )

    score_min = max(
        0,
        rank_window[
            "transition_performance_index"
        ].min() - 8,
    )

    score_max = min(
        105,
        rank_window[
            "transition_performance_index"
        ].max() + 12,
    )

    rank_fig.update_xaxes(
        title="Transition Performance Index",
        range=[score_min, score_max],
    )

    rank_fig.update_yaxes(title="")

    style_plotly(
        rank_fig,
        height=570,
        show_legend=False,
    )

    st.plotly_chart(
        rank_fig,
        width="stretch",
        config={"displayModeBar": False},
    )

# =========================================================
# STRATEGIC PRIORITY ENGINE
# =========================================================

weighted_headroom = {
    component: (
        (100 - float(simulated[component]))
        * weight
    )
    for component, weight in WEIGHTS.items()
}

priority_component = max(
    weighted_headroom,
    key=weighted_headroom.get,
)

priority = RECOMMENDATIONS[
    priority_component
]

target_tier, target_score = next_tier_target(
    float(simulated["transition_performance_index"]),
    float(q25),
    float(q50),
    float(q75),
)

leader_benchmark = (
    index_df[
        index_df["performance_tier"].eq(
            "Global Leader"
        )
    ][
        [
            "renewables_share_elec",
            "fossil_share_elec",
            "carbon_intensity_elec",
            "renewable_improvement",
        ]
    ]
    .median()
)

st.divider()
st.subheader("4 · Strategic recommendation")

if score_change > 0:
    st.success(
        f"""
### Scenario impact for {selected_country}

Under this scenario, the transition score rises from
**{current['transition_performance_index']:.1f}** to
**{simulated['transition_performance_index']:.1f}**.

The global position moves from
**rank #{int(current['global_rank'])}** to
**rank #{int(simulated['global_rank'])}**
({signed_places(rank_gain)}), and the performance tier is
**{simulated['performance_tier']}**.
"""
    )
else:
    st.warning(
        """
The selected controls do not yet create a measurable score improvement.
Increase at least one transition lever to test a stronger scenario.
"""
    )

priority_col, target_col = st.columns(
    [0.58, 0.42],
    gap="large",
)

with priority_col:
    st.markdown(
        f"""
### Primary remaining priority: {priority['title']}

The simulator identifies this as the largest remaining weighted gap in
the four-component transition index.

**Recommended actions**

1. {priority['actions'][0]}
2. {priority['actions'][1]}
3. {priority['actions'][2]}
"""
    )

with target_col:
    if target_score is None:
        st.metric(
            "Next strategic objective",
            target_tier,
        )
        st.write(
            "The country is already above the current Global Leader "
            "threshold. The priority is maintaining balanced performance."
        )
    else:
        score_gap = max(
            0.0,
            float(target_score)
            - float(
                simulated[
                    "transition_performance_index"
                ]
            ),
        )

        st.metric(
            "Next performance target",
            target_tier,
            f"{score_gap:.1f} index points needed",
            delta_color="off",
        )

        st.progress(
            min(
                1.0,
                float(
                    simulated[
                        "transition_performance_index"
                    ]
                )
                / float(target_score),
            ),
            text=(
                f"{simulated['transition_performance_index']:.1f} "
                f"of {target_score:.1f} points"
            ),
        )

st.subheader("Scenario metrics versus current Global Leader benchmark")

benchmark_table = pd.DataFrame(
    {
        "Metric": [
            "Renewable electricity share (%)",
            "Fossil electricity share (%)",
            "Carbon intensity (gCO₂/kWh)",
            "Renewable improvement since 2000 (pp)",
        ],
        "Current": [
            current["renewables_share_elec"],
            current["fossil_share_elec"],
            current["carbon_intensity_elec"],
            current["renewable_improvement"],
        ],
        "Simulated": [
            simulated["renewables_share_elec"],
            simulated["fossil_share_elec"],
            simulated["carbon_intensity_elec"],
            simulated["renewable_improvement"],
        ],
        "Global Leader median": [
            leader_benchmark["renewables_share_elec"],
            leader_benchmark["fossil_share_elec"],
            leader_benchmark["carbon_intensity_elec"],
            leader_benchmark["renewable_improvement"],
        ],
        "Preferred direction": [
            "Higher",
            "Lower",
            "Lower",
            "Higher",
        ],
    }
).round(1)

st.dataframe(
    benchmark_table,
    width="stretch",
    hide_index=True,
)

# =========================================================
# DOWNLOAD
# =========================================================

scenario_download = pd.DataFrame(
    [
        {
            "country": selected_country,
            "analysis_year": analysis_year,
            "current_transition_score":
                current["transition_performance_index"],
            "simulated_transition_score":
                simulated["transition_performance_index"],
            "score_change": score_change,
            "current_global_rank":
                current["global_rank"],
            "simulated_global_rank":
                simulated["global_rank"],
            "rank_places_gained": rank_gain,
            "current_performance_tier":
                current["performance_tier"],
            "simulated_performance_tier":
                simulated["performance_tier"],
            "renewable_share_current":
                current["renewables_share_elec"],
            "renewable_share_simulated":
                simulated["renewables_share_elec"],
            "fossil_share_current":
                current["fossil_share_elec"],
            "fossil_share_simulated":
                simulated["fossil_share_elec"],
            "carbon_intensity_current":
                current["carbon_intensity_elec"],
            "carbon_intensity_simulated":
                simulated["carbon_intensity_elec"],
            "primary_remaining_priority":
                priority["title"],
        }
    ]
)

st.download_button(
    "⬇️ Download this scenario",
    data=scenario_download.to_csv(index=False),
    file_name=(
        selected_country.lower()
        .replace(" ", "_")
        + "_transition_scenario.csv"
    ),
    mime="text/csv",
    width="stretch",
)

# =========================================================
# METHODOLOGY
# =========================================================

with st.expander(
    "Methodology: How does the simulator calculate the result?"
):
    st.markdown(
        f"""
The simulator starts with the dashboard's {analysis_year} transition
dataset and changes only the selected country's three scenario metrics.

It then recalculates percentile scores across all evaluated countries:

- Renewable electricity share: **35%**
- Low electricity carbon intensity: **25%**
- Renewable improvement since 2000: **20%**
- Low fossil-fuel dependence: **20%**

Global rank is recalculated after the scenario. Performance-tier
thresholds remain fixed at today's quartiles so the current and simulated
tiers are directly comparable.

Current tier thresholds:

- Global Leader: **{q75:.1f} or above**
- Strong Performer: **{q50:.1f} to below {q75:.1f}**
- Emerging Transition: **{q25:.1f} to below {q50:.1f}**
- Transition Challenge: **below {q25:.1f}**

This is an educational decision-support simulation. It does not estimate
cost, construction time, electricity demand, grid reliability, political
feasibility, or future market conditions.
"""
    )

st.divider()
st.caption(
    "Data source: Our World in Data Energy Dataset. "
    "Scenario results use a custom academic transition index and should "
    "not be interpreted as official forecasts or country rankings."
)
