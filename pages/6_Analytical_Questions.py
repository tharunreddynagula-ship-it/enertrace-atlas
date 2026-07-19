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
    latest_common_year,
    style_plotly,
    transition_quadrants,
    weighted_global_renewable_trend,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="11 Analytical Questions",
    page_icon="📊",
    layout="wide",
)

apply_page_style()

# =========================================================
# LOAD DATA
# =========================================================

with st.spinner("Calculating live answers to the 11 analytical questions..."):
    df = load_data()
    index_df, analysis_year = build_transition_index(df)
    global_trend = weighted_global_renewable_trend(df)
    quadrant_df = transition_quadrants(index_df)

# =========================================================
# SHARED DATA
# =========================================================

latest = (
    df[df["year"].eq(analysis_year)]
    .drop_duplicates("country")
    .copy()
)

start_row = global_trend.iloc[0]
end_row = global_trend.iloc[-1]

global_increase = (
    end_row["renewables_share_elec"]
    - start_row["renewables_share_elec"]
)

leader = index_df.iloc[0]

fastest = index_df.loc[
    index_df["renewable_improvement"].idxmax()
]

cleanest = index_df.loc[
    index_df["carbon_intensity_elec"].idxmin()
]

median_score = index_df[
    "transition_performance_index"
].median()

# Create GDP per capita when necessary.
if "gdp_per_capita" not in df.columns and {
    "gdp",
    "population",
}.issubset(df.columns):
    df["gdp_per_capita"] = np.where(
        df["population"].gt(0),
        df["gdp"] / df["population"],
        np.nan,
    )

# =========================================================
# HEADER
# =========================================================

st.title("📊 Eleven Live Analytical Questions")
st.caption(
    "Each answer is calculated directly from the dashboard dataset. "
    "Select a question to view the live result, visualization, and interpretation."
)

st.info(
    f"""
**Live analysis scope:** {len(index_df)} countries ·
Baseline year {int(start_row['year'])} ·
Final index year {analysis_year} ·
Data available through {int(df['year'].max())}
"""
)

questions = [
    "Q1 · How has global renewable electricity changed since 2000?",
    "Q2 · Which countries currently lead in renewable electricity?",
    "Q3 · Which countries improved the most since 2000?",
    "Q4 · Where is renewable electricity strongest geographically?",
    "Q5 · Which countries remain most dependent on fossil electricity?",
    "Q6 · Does economic wealth drive renewable electricity adoption?",
    "Q7 · Is renewable electricity associated with lower carbon intensity?",
    "Q8 · Which renewable technologies are driving global change?",
    "Q9 · How do selected countries compare across key transition metrics?",
    "Q10 · Which countries lead, catch up, or fall behind?",
    "Q11 · What is the final combined conclusion of the analysis?",
]

selected_question = st.selectbox(
    "Choose an analytical question",
    questions,
)

question_number = questions.index(selected_question) + 1

st.progress(
    question_number / len(questions),
    text=f"Question {question_number} of {len(questions)}",
)

st.divider()

# =========================================================
# QUESTION 1
# =========================================================

if question_number == 1:
    st.header(
        "Q1 · How has global renewable electricity changed since 2000?"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        f"Renewable share in {int(start_row['year'])}",
        f"{start_row['renewables_share_elec']:.1f}%",
    )

    c2.metric(
        f"Renewable share in {int(end_row['year'])}",
        f"{end_row['renewables_share_elec']:.1f}%",
    )

    c3.metric(
        "Long-term increase",
        f"{global_increase:.1f} pp",
    )

    fig = px.area(
        global_trend,
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

    fig.update_traces(
        line=dict(
            color=PALETTE["sky"],
            width=4,
        ),
        marker=dict(
            size=6,
            color=PALETTE["teal"],
        ),
        fillcolor="rgba(56, 189, 248, 0.18)",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Renewable share: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    fig.update_yaxes(ticksuffix="%")
    style_plotly(
        fig,
        height=600,
        show_legend=False,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Answer:** Global renewable electricity increased from
**{start_row['renewables_share_elec']:.1f}%** in
**{int(start_row['year'])}** to
**{end_row['renewables_share_elec']:.1f}%** in
**{int(end_row['year'])}**. This is a gain of
**{global_increase:.1f} percentage points**.
"""
    )

# =========================================================
# QUESTION 2
# =========================================================

elif question_number == 2:
    st.header(
        "Q2 · Which countries currently lead in renewable electricity?"
    )

    leaders = (
        latest.dropna(subset=["renewables_share_elec"])
        .nlargest(15, "renewables_share_elec")
        .sort_values("renewables_share_elec")
    )

    top_country = leaders.iloc[-1]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Current renewable leader",
        top_country["country"],
        f"{top_country['renewables_share_elec']:.1f}%",
    )

    c2.metric(
        "Countries above 75%",
        int(
            latest["renewables_share_elec"]
            .ge(75)
            .sum()
        ),
    )

    c3.metric(
        "Analysis year",
        analysis_year,
    )

    fig = px.bar(
        leaders,
        x="renewables_share_elec",
        y="country",
        orientation="h",
        text="renewables_share_elec",
        title=(
            f"Renewable Leaders Generate Most Electricity "
            f"from Clean Sources ({analysis_year})"
        ),
        labels={
            "renewables_share_elec":
                "Renewable electricity share (%)",
            "country": "",
        },
    )

    fig.update_traces(
        marker_color=PALETTE["teal"],
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_xaxes(
        range=[0, 105],
        ticksuffix="%",
    )

    style_plotly(
        fig,
        height=670,
        show_legend=False,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Answer:** **{top_country['country']}** records the highest renewable
electricity share in the selected analysis year at
**{top_country['renewables_share_elec']:.1f}%**.
High current renewable share identifies leadership today, but it does
not by itself measure how quickly a country improved.
"""
    )

# =========================================================
# QUESTION 3
# =========================================================

elif question_number == 3:
    st.header(
        "Q3 · Which countries improved the most since 2000?"
    )

    improvers = (
        index_df.nlargest(
            15,
            "renewable_improvement",
        )
        .sort_values("renewable_improvement")
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Fastest improver",
        fastest["country"],
        f"+{fastest['renewable_improvement']:.1f} pp",
    )

    c2.metric(
        "Renewable share in 2000",
        f"{fastest['renewable_share_baseline']:.1f}%",
    )

    c3.metric(
        f"Renewable share in {analysis_year}",
        f"{fastest['renewables_share_elec']:.1f}%",
    )

    fig = px.bar(
        improvers,
        x="renewable_improvement",
        y="country",
        orientation="h",
        text="renewable_improvement",
        title=(
            f"The Fastest Transitions Added the Most Renewable Share "
            f"(2000–{analysis_year})"
        ),
        labels={
            "renewable_improvement":
                "Increase in renewable share (percentage points)",
            "country": "",
        },
    )

    fig.update_traces(
        marker_color=PALETTE["orange"],
        texttemplate="+%{text:.1f} pp",
        textposition="outside",
        cliponaxis=False,
    )

    style_plotly(
        fig,
        height=670,
        show_legend=False,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Answer:** **{fastest['country']}** achieved the largest improvement,
raising its renewable electricity share by
**{fastest['renewable_improvement']:.1f} percentage points** between
2000 and {analysis_year}.
"""
    )

# =========================================================
# QUESTION 4
# =========================================================

elif question_number == 4:
    st.header(
        "Q4 · Where is renewable electricity strongest geographically?"
    )

    map_data = latest.dropna(
        subset=[
            "iso_code",
            "renewables_share_elec",
        ]
    ).copy()

    top_five = map_data.nlargest(
        5,
        "renewables_share_elec",
    )

    st.metric(
        "Countries mapped",
        map_data["country"].nunique(),
    )

    fig = px.choropleth(
        map_data,
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
        title=(
            f"Renewable Electricity Leadership Is Unevenly Distributed "
            f"Across the World ({analysis_year})"
        ),
        labels={
            "renewables_share_elec":
                "Renewable electricity share (%)",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Renewable electricity: %{z:.1f}%"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=700,
        paper_bgcolor="rgba(7,24,39,0)",
        plot_bgcolor="rgba(7,24,39,0)",
        font=dict(color="#CBD5E1"),
        margin=dict(l=0, r=0, t=70, b=0),
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
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    leaders_text = ", ".join(
        f"{row.country} ({row.renewables_share_elec:.1f}%)"
        for row in top_five.itertuples()
    )

    st.success(
        f"""
**Answer:** Renewable leadership is geographically uneven. The five
highest recorded shares in {analysis_year} are:
**{leaders_text}**.
"""
    )

# =========================================================
# QUESTION 5
# =========================================================

elif question_number == 5:
    st.header(
        "Q5 · Which countries remain most dependent on fossil electricity?"
    )

    fossil_lag = (
        latest.dropna(subset=["fossil_share_elec"])
        .nlargest(15, "fossil_share_elec")
        .sort_values("fossil_share_elec")
    )

    most_dependent = fossil_lag.iloc[-1]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Highest fossil dependence",
        most_dependent["country"],
        f"{most_dependent['fossil_share_elec']:.1f}%",
    )

    c2.metric(
        "Countries above 75% fossil",
        int(
            latest["fossil_share_elec"]
            .ge(75)
            .sum()
        ),
    )

    c3.metric(
        "Analysis year",
        analysis_year,
    )

    fig = px.bar(
        fossil_lag,
        x="fossil_share_elec",
        y="country",
        orientation="h",
        text="fossil_share_elec",
        title=(
            f"The Greatest Transition Challenge Remains "
            f"Heavy Fossil Dependence ({analysis_year})"
        ),
        labels={
            "fossil_share_elec":
                "Fossil electricity share (%)",
            "country": "",
        },
    )

    fig.update_traces(
        marker_color=PALETTE["orange"],
        texttemplate="%{text:.1f}%",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_xaxes(
        range=[0, 105],
        ticksuffix="%",
    )

    style_plotly(
        fig,
        height=670,
        show_legend=False,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.warning(
        f"""
**Answer:** **{most_dependent['country']}** has the highest recorded
fossil-electricity share at
**{most_dependent['fossil_share_elec']:.1f}%**.
These countries face the largest structural transition challenge.
"""
    )

# =========================================================
# QUESTION 6
# =========================================================

elif question_number == 6:
    st.header(
        "Q6 · Does economic wealth drive renewable electricity adoption?"
    )

    # GDP data often finish earlier than the final transition-index year.
    # Use the latest year with strong common coverage instead of forcing 2024.
    try:
        wealth_year = latest_common_year(
            df,
            [
                "gdp_per_capita",
                "renewables_share_elec",
            ],
            coverage_ratio=0.60,
        )
    except ValueError:
        wealth_year = None

    if wealth_year is None:
        st.warning(
            "No year contains sufficient GDP-per-capita and renewable "
            "electricity data for this analysis."
        )
    else:
        wealth_data = (
            df[df["year"].eq(wealth_year)]
            .dropna(
                subset=[
                    "gdp_per_capita",
                    "renewables_share_elec",
                    "country",
                ]
            )
            .copy()
        )

        wealth_data = wealth_data[
            wealth_data["gdp_per_capita"].gt(0)
            & np.isfinite(wealth_data["gdp_per_capita"])
            & np.isfinite(wealth_data["renewables_share_elec"])
        ].copy()

        if (
            len(wealth_data) < 3
            or wealth_data["gdp_per_capita"].nunique() < 2
            or wealth_data["renewables_share_elec"].nunique() < 2
        ):
            st.warning(
                f"Only {len(wealth_data)} usable country observations are "
                f"available for {wealth_year}. At least three varied "
                "observations are required for correlation and trend analysis."
            )

            if not wealth_data.empty:
                st.dataframe(
                    wealth_data[
                        [
                            "country",
                            "gdp_per_capita",
                            "renewables_share_elec",
                        ]
                    ].sort_values(
                        "gdp_per_capita",
                        ascending=False,
                    ),
                    width="stretch",
                    hide_index=True,
                )
        else:
            wealth_data["log_gdp_per_capita"] = np.log10(
                wealth_data["gdp_per_capita"]
            )

            correlation = wealth_data[
                [
                    "log_gdp_per_capita",
                    "renewables_share_elec",
                ]
            ].corr().iloc[0, 1]

            slope, intercept = np.polyfit(
                wealth_data["log_gdp_per_capita"].to_numpy(),
                wealth_data["renewables_share_elec"].to_numpy(),
                1,
            )

            trend_x_log = np.linspace(
                wealth_data["log_gdp_per_capita"].min(),
                wealth_data["log_gdp_per_capita"].max(),
                150,
            )

            trend_x = 10 ** trend_x_log
            trend_y = slope * trend_x_log + intercept

            relationship = (
                "Very weak"
                if abs(correlation) < 0.20
                else "Weak"
                if abs(correlation) < 0.40
                else "Moderate"
                if abs(correlation) < 0.60
                else "Strong"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Analysis year",
                wealth_year,
            )

            c2.metric(
                "Countries included",
                len(wealth_data),
            )

            c3.metric(
                "Correlation",
                f"{correlation:.2f}",
            )

            c4.metric(
                "Relationship",
                relationship,
            )

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=wealth_data["gdp_per_capita"],
                    y=wealth_data["renewables_share_elec"],
                    mode="markers",
                    text=wealth_data["country"],
                    marker=dict(
                        size=10,
                        color=wealth_data["renewables_share_elec"],
                        colorscale=[
                            [0.00, "#64748B"],
                            [0.50, "#38BDF8"],
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
                        "GDP per capita: %{x:,.0f}<br>"
                        "Renewable share: %{y:.1f}%"
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

            fig.update_layout(
                title=(
                    "Economic Wealth Alone Does Not Guarantee "
                    f"Renewable Leadership ({wealth_year})"
                ),
            )

            fig.update_xaxes(
                title="GDP per capita",
                type="log",
            )

            fig.update_yaxes(
                title="Renewable electricity share (%)",
                range=[0, 105],
                ticksuffix="%",
            )

            style_plotly(
                fig,
                height=670,
                show_legend=True,
            )

            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
            )

            direction = "positive" if correlation >= 0 else "negative"

            st.info(
                f"""
**Answer:** Using the latest year with strong common coverage
(**{wealth_year}**), the correlation between log GDP per capita and
renewable electricity share is **{correlation:.2f}**. This is a
**{relationship.lower()} {direction} relationship**.

Economic wealth alone does not explain renewable adoption. Natural
resources, energy policy, grid infrastructure, financing, and
long-term investment also influence transition performance.
"""
            )

# =========================================================
# QUESTION 7
# =========================================================

elif question_number == 7:
    st.header(
        "Q7 · Is renewable electricity associated with lower carbon intensity?"
    )

    carbon_data = latest.dropna(
        subset=[
            "renewables_share_elec",
            "carbon_intensity_elec",
            "country",
        ]
    ).copy()

    correlation = carbon_data[
        [
            "renewables_share_elec",
            "carbon_intensity_elec",
        ]
    ].corr().iloc[0, 1]

    slope, intercept = np.polyfit(
        carbon_data["renewables_share_elec"],
        carbon_data["carbon_intensity_elec"],
        1,
    )

    trend_x = np.linspace(
        carbon_data["renewables_share_elec"].min(),
        carbon_data["renewables_share_elec"].max(),
        150,
    )

    trend_y = slope * trend_x + intercept

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Countries included",
        len(carbon_data),
    )

    c2.metric(
        "Correlation",
        f"{correlation:.2f}",
    )

    c3.metric(
        "Cleanest electricity",
        cleanest["country"],
        f"{cleanest['carbon_intensity_elec']:.0f} gCO₂/kWh",
        delta_color="off",
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=carbon_data["renewables_share_elec"],
            y=carbon_data["carbon_intensity_elec"],
            mode="markers",
            text=carbon_data["country"],
            marker=dict(
                size=10,
                color=carbon_data["renewables_share_elec"],
                colorscale=[
                    [0.00, "#64748B"],
                    [0.50, "#38BDF8"],
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
                "Carbon intensity: %{y:.0f} gCO₂/kWh"
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

    fig.update_layout(
        title=(
            "Higher Renewable Electricity Is Generally "
            "Associated with Lower Carbon Intensity"
        ),
    )

    fig.update_xaxes(
        title="Renewable electricity share (%)",
        range=[0, 105],
        ticksuffix="%",
    )

    fig.update_yaxes(
        title="Carbon intensity (gCO₂/kWh)",
    )

    style_plotly(
        fig,
        height=670,
        show_legend=True,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Answer:** The correlation is **{correlation:.2f}**.
The negative relationship shows that countries with larger renewable
electricity shares generally produce less carbon per unit of electricity.
"""
    )

# =========================================================
# QUESTION 8
# =========================================================

elif question_number == 8:
    st.header(
        "Q8 · Which renewable technologies are driving global change?"
    )

    technology_columns = {
        "Solar": "solar_share_elec",
        "Wind": "wind_share_elec",
        "Hydropower": "hydro_share_elec",
    }

    technology_rows = []

    for year, year_data in df.groupby("year"):
        generation = year_data[
            "electricity_generation"
        ]

        for technology, column in technology_columns.items():
            usable = year_data[
                generation.gt(0)
                & year_data[column].notna()
            ]

            if usable.empty:
                continue

            weighted_share = (
                (
                    usable["electricity_generation"]
                    * usable[column]
                    / 100
                ).sum()
                / usable["electricity_generation"].sum()
                * 100
            )

            technology_rows.append(
                {
                    "year": int(year),
                    "Technology": technology,
                    "Weighted global share": weighted_share,
                }
            )

    technology_trend = pd.DataFrame(
        technology_rows
    )

    start_tech = (
        technology_trend[
            technology_trend["year"].eq(
                technology_trend["year"].min()
            )
        ]
        .set_index("Technology")[
            "Weighted global share"
        ]
    )

    end_tech = (
        technology_trend[
            technology_trend["year"].eq(
                technology_trend["year"].max()
            )
        ]
        .set_index("Technology")[
            "Weighted global share"
        ]
    )

    technology_change = (
        end_tech.subtract(
            start_tech,
            fill_value=np.nan,
        )
        .sort_values(
            ascending=False
        )
    )

    fastest_technology = technology_change.index[0]
    fastest_technology_change = technology_change.iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Fastest-growing technology",
        fastest_technology,
        f"+{fastest_technology_change:.1f} pp",
    )

    c2.metric(
        "Technologies compared",
        len(technology_columns),
    )

    c3.metric(
        "Latest technology year",
        int(technology_trend["year"].max()),
    )

    fig = px.line(
        technology_trend,
        x="year",
        y="Weighted global share",
        color="Technology",
        markers=True,
        title=(
            "Solar and Wind Are Reshaping the Renewable Technology Mix"
        ),
        labels={
            "year": "Year",
            "Weighted global share":
                "Weighted global electricity share (%)",
        },
        color_discrete_map={
            "Solar": PALETTE["orange"],
            "Wind": PALETTE["blue"],
            "Hydropower": PALETTE["teal"],
        },
    )

    fig.update_traces(
        line=dict(width=4),
        marker=dict(size=5),
    )

    fig.update_yaxes(ticksuffix="%")

    style_plotly(
        fig,
        height=650,
        show_legend=True,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )

    st.success(
        f"""
**Answer:** **{fastest_technology}** shows the largest increase in the
weighted global electricity mix, rising by approximately
**{fastest_technology_change:.1f} percentage points** over the
available period. Hydropower remains an established source, while
solar and wind represent the newer direction of growth.
"""
    )

# =========================================================
# QUESTION 9
# =========================================================

elif question_number == 9:
    st.header(
        "Q9 · How do selected countries compare across key transition metrics?"
    )

    countries = sorted(
        index_df["country"]
        .dropna()
        .unique()
    )

    defaults = [
        country
        for country in [
            "Germany",
            "Denmark",
            "India",
            "China",
        ]
        if country in countries
    ]

    selected_countries = st.multiselect(
        "Choose between 2 and 6 countries",
        countries,
        default=defaults,
        max_selections=6,
    )

    if len(selected_countries) < 2:
        st.warning(
            "Select at least two countries to display the comparison."
        )
    else:
        comparison = index_df[
            index_df["country"].isin(
                selected_countries
            )
        ].copy()

        metric_long = comparison.melt(
            id_vars="country",
            value_vars=[
                "renewables_share_elec",
                "fossil_share_elec",
                "carbon_intensity_elec",
                "transition_performance_index",
            ],
            var_name="Metric",
            value_name="Value",
        )

        metric_long["Metric"] = metric_long["Metric"].map(
            {
                "renewables_share_elec":
                    "Renewable share (%)",
                "fossil_share_elec":
                    "Fossil share (%)",
                "carbon_intensity_elec":
                    "Carbon intensity",
                "transition_performance_index":
                    "Transition index",
            }
        )

        fig = px.bar(
            metric_long,
            x="country",
            y="Value",
            color="country",
            facet_col="Metric",
            facet_col_wrap=2,
            title=(
                f"Selected Countries Reveal Different Transition Strengths "
                f"({analysis_year})"
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
            height=720,
            show_legend=False,
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False},
        )

        best = comparison.loc[
            comparison[
                "transition_performance_index"
            ].idxmax()
        ]

        st.success(
            f"""
**Answer:** Among the selected countries,
**{best['country']}** has the strongest combined transition score at
**{best['transition_performance_index']:.1f}/100**.
The visual also shows whether this advantage comes from renewable
adoption, lower fossil dependence, or cleaner electricity.
"""
        )

# =========================================================
# QUESTION 10
# =========================================================

elif question_number == 10:
    st.header(
        "Q10 · Which countries lead, catch up, or fall behind?"
    )

    renewable_median = quadrant_df[
        "renewables_share_elec"
    ].median()

    progress_median = quadrant_df[
        "renewable_improvement"
    ].median()

    colors = {
        "Leaders": PALETTE["teal"],
        "Catching Up": PALETTE["orange"],
        "Established but Slower": PALETTE["blue"],
        "Falling Behind": PALETTE["red"],
    }

    group_counts = (
        quadrant_df[
            "strategic_position"
        ]
        .value_counts()
        .reindex(
            colors.keys(),
            fill_value=0,
        )
    )

    c1, c2, c3, c4 = st.columns(4)

    for column, group_name in zip(
        [c1, c2, c3, c4],
        colors.keys(),
    ):
        column.metric(
            group_name,
            int(group_counts[group_name]),
        )

    fig = px.scatter(
        quadrant_df,
        x="renewable_improvement",
        y="renewables_share_elec",
        color="strategic_position",
        hover_name="country",
        color_discrete_map=colors,
        title=(
            "Current Renewable Position and Long-Term Progress "
            "Create Four Strategic Groups"
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

    fig.update_traces(
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

    fig.add_vline(
        x=progress_median,
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    fig.add_hline(
        y=renewable_median,
        line_dash="dot",
        line_color=PALETTE["grey"],
    )

    fig.update_yaxes(
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

    st.info(
        """
**Answer:** Leaders combine a strong current renewable position with
above-median long-term progress. Catching-up countries are improving
quickly but have not yet reached the leading renewable share. Falling
behind countries remain below both medians.
"""
    )

# =========================================================
# QUESTION 11
# =========================================================

else:
    st.header(
        "Q11 · What is the final combined conclusion of the analysis?"
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
        .reset_index()
    )

    tier_counts.columns = [
        "Performance tier",
        "Countries",
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Overall leader",
        leader["country"],
        f"{leader['transition_performance_index']:.1f}/100",
    )

    c2.metric(
        "Fastest improver",
        fastest["country"],
        f"+{fastest['renewable_improvement']:.1f} pp",
    )

    c3.metric(
        "Cleanest electricity",
        cleanest["country"],
        f"{cleanest['carbon_intensity_elec']:.0f} gCO₂/kWh",
        delta_color="off",
    )

    c4.metric(
        "Median transition score",
        f"{median_score:.1f}/100",
    )

    top10 = (
        index_df.head(10)
        .sort_values(
            "transition_performance_index"
        )
    )

    left, right = st.columns(
        [1.35, 0.85],
        gap="large",
    )

    with left:
        fig_rank = px.bar(
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
            title=(
                "The Final Index Rewards Balanced Transition Performance"
            ),
            labels={
                "transition_performance_index":
                    "Transition Performance Index",
                "country": "",
            },
        )

        fig_rank.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
            cliponaxis=False,
        )

        fig_rank.update_layout(
            coloraxis_showscale=False,
        )

        fig_rank.update_xaxes(
            range=[0, 105],
        )

        style_plotly(
            fig_rank,
            height=590,
            show_legend=False,
        )

        st.plotly_chart(
            fig_rank,
            width="stretch",
            config={"displayModeBar": False},
        )

    with right:
        fig_tiers = px.bar(
            tier_counts,
            x="Countries",
            y="Performance tier",
            orientation="h",
            text="Countries",
            title="Most Countries Still Face Transition Challenges",
            labels={
                "Countries": "Number of countries",
                "Performance tier": "",
            },
            color="Performance tier",
            color_discrete_map={
                "Global Leader": PALETTE["teal"],
                "Strong Performer": PALETTE["blue"],
                "Emerging Transition": PALETTE["orange"],
                "Transition Challenge": PALETTE["red"],
            },
        )

        fig_tiers.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        style_plotly(
            fig_tiers,
            height=590,
            show_legend=False,
        )

        st.plotly_chart(
            fig_tiers,
            width="stretch",
            config={"displayModeBar": False},
        )

    st.success(
        f"""
**Final answer:** Global renewable electricity is growing, but country
performance remains highly unequal. **{leader['country']}** leads the
combined index with **{leader['transition_performance_index']:.1f}/100**,
while the median country scores **{median_score:.1f}/100**.

The strongest transitions combine four factors:

- high renewable electricity adoption,
- low fossil-fuel dependence,
- low electricity carbon intensity, and
- meaningful improvement since 2000.
"""
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Data source: Our World in Data Energy Dataset. "
    "All answers update automatically when the underlying CSV changes. "
    "The Energy Transition Performance Index is a custom academic metric."
)
