from __future__ import annotations

from pathlib import Path
from typing import Iterable
from textwrap import dedent

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


DATA_PATHS = (
    Path("data/energy_clean.csv"),
    Path("energy_clean.csv"),
)

HERO_IMAGE_PATHS = (
    Path("images/wind_farm_hero.png"),
    Path("image/wind_farm_hero.png"),
    Path("assets/wind_farm_hero.png"),
)

PALETTE = {
    "navy": "#0B1F33",
    "blue": "#0072B2",
    "sky": "#38BDF8",
    "teal": "#009E73",
    "green": "#22C55E",
    "orange": "#E69F00",
    "purple": "#CC79A7",
    "red": "#D55E00",
    "grey": "#94A3B8",
    "light_grey": "#CBD5E1",
    "white": "#F8FAFC",
}


def _first_existing_path(paths: Iterable[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    expected = ", ".join(str(path) for path in paths)
    raise FileNotFoundError(
        f"Required file was not found. Expected one of: {expected}"
    )


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load the cleaned country-year energy dataset."""
    path = _first_existing_path(DATA_PATHS)
    df = pd.read_csv(path)

    required = {
        "country",
        "year",
        "iso_code",
        "population",
        "renewables_share_elec",
        "fossil_share_elec",
        "carbon_intensity_elec",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(
            "The cleaned dataset is missing required columns: "
            + ", ".join(missing)
        )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["country", "year"]).copy()
    df["year"] = df["year"].astype(int)

    numeric_columns = [
        column
        for column in df.columns
        if column not in {"country", "iso_code"}
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if "gdp_per_capita" not in df.columns:
        if {"gdp", "population"}.issubset(df.columns):
            df["gdp_per_capita"] = np.where(
                df["population"].gt(0),
                df["gdp"] / df["population"],
                np.nan,
            )

    return df.sort_values(["country", "year"]).reset_index(drop=True)


def find_hero_image() -> Path | None:
    """Return the first available hero image path."""
    for path in HERO_IMAGE_PATHS:
        if path.exists():
            return path
    return None


def latest_common_year(
    df: pd.DataFrame,
    columns: list[str],
    coverage_ratio: float = 0.75,
) -> int:
    """
    Select the latest year with strong international coverage.

    The notebook uses 2024 for the final index because 2025 has
    incomplete coverage for several required indicators.
    """
    usable = df.dropna(subset=columns)
    coverage = usable.groupby("year")["country"].nunique()

    if coverage.empty:
        raise ValueError(
            "No year has complete data for: " + ", ".join(columns)
        )

    threshold = coverage.max() * coverage_ratio
    eligible = coverage[coverage >= threshold]

    if eligible.empty:
        return int(coverage.idxmax())

    return int(eligible.index.max())


def weighted_global_renewable_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the global renewable electricity share weighted by
    electricity generation, matching the notebook's global trend logic.
    """
    required = [
        "year",
        "electricity_generation",
        "renewables_share_elec",
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            "Global trend requires: " + ", ".join(missing)
        )

    trend = df.dropna(subset=required).copy()
    trend = trend[trend["electricity_generation"] > 0]

    trend["renewable_generation"] = (
        trend["electricity_generation"]
        * trend["renewables_share_elec"]
        / 100
    )

    result = (
        trend.groupby("year", as_index=False)
        .agg(
            renewable_generation=(
                "renewable_generation",
                "sum",
            ),
            total_generation=(
                "electricity_generation",
                "sum",
            ),
        )
    )

    result["renewables_share_elec"] = (
        result["renewable_generation"]
        / result["total_generation"]
        * 100
    )

    return result.sort_values("year").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def build_transition_index(
    df: pd.DataFrame,
    baseline_year: int = 2000,
) -> tuple[pd.DataFrame, int]:
    """
    Reproduce the notebook's final Energy Transition Performance Index.

    Weights:
    - Current renewable electricity share: 35%
    - Low carbon intensity: 25%
    - Renewable improvement since 2000: 20%
    - Low fossil-fuel dependence: 20%
    """
    required_current = [
        "renewables_share_elec",
        "fossil_share_elec",
        "carbon_intensity_elec",
    ]

    analysis_year = latest_common_year(
        df,
        required_current,
        coverage_ratio=0.75,
    )

    baseline = (
        df.loc[
            df["year"].eq(baseline_year),
            ["country", "renewables_share_elec"],
        ]
        .dropna()
        .rename(
            columns={
                "renewables_share_elec":
                    "renewable_share_baseline"
            }
        )
    )

    current_columns = [
        "country",
        "iso_code",
        "population",
        "renewables_share_elec",
        "fossil_share_elec",
        "carbon_intensity_elec",
    ]

    current = (
        df.loc[df["year"].eq(analysis_year), current_columns]
        .drop_duplicates("country")
    )

    index_df = (
        current.merge(
            baseline,
            on="country",
            how="inner",
            validate="one_to_one",
        )
        .dropna(
            subset=[
                "renewables_share_elec",
                "fossil_share_elec",
                "carbon_intensity_elec",
                "renewable_share_baseline",
            ]
        )
        .copy()
    )

    index_df["renewable_improvement"] = (
        index_df["renewables_share_elec"]
        - index_df["renewable_share_baseline"]
    )

    # Percentile scores from 0 to 100.
    index_df["renewable_score"] = (
        index_df["renewables_share_elec"]
        .rank(method="average", pct=True)
        * 100
    )

    index_df["low_carbon_score"] = (
        index_df["carbon_intensity_elec"]
        .rank(method="average", pct=True, ascending=False)
        * 100
    )

    index_df["progress_score"] = (
        index_df["renewable_improvement"]
        .rank(method="average", pct=True)
        * 100
    )

    index_df["low_fossil_score"] = (
        index_df["fossil_share_elec"]
        .rank(method="average", pct=True, ascending=False)
        * 100
    )

    index_df["transition_performance_index"] = (
        0.35 * index_df["renewable_score"]
        + 0.25 * index_df["low_carbon_score"]
        + 0.20 * index_df["progress_score"]
        + 0.20 * index_df["low_fossil_score"]
    ).round(1)

    index_df = (
        index_df.sort_values(
            [
                "transition_performance_index",
                "renewables_share_elec",
            ],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )

    index_df["global_rank"] = np.arange(1, len(index_df) + 1)

    # Quartile-based performance tiers from the notebook conclusion.
    q25, q50, q75 = index_df[
        "transition_performance_index"
    ].quantile([0.25, 0.50, 0.75])

    index_df["performance_tier"] = np.select(
        [
            index_df["transition_performance_index"].ge(q75),
            index_df["transition_performance_index"].ge(q50),
            index_df["transition_performance_index"].ge(q25),
        ],
        [
            "Global Leader",
            "Strong Performer",
            "Emerging Transition",
        ],
        default="Transition Challenge",
    )

    return index_df, analysis_year


def transition_quadrants(index_df: pd.DataFrame) -> pd.DataFrame:
    """Classify countries by current position and long-term progress."""
    result = index_df.copy()

    renewable_median = result["renewables_share_elec"].median()
    progress_median = result["renewable_improvement"].median()

    result["strategic_position"] = np.select(
        [
            result["renewables_share_elec"].ge(renewable_median)
            & result["renewable_improvement"].ge(progress_median),

            result["renewables_share_elec"].lt(renewable_median)
            & result["renewable_improvement"].ge(progress_median),

            result["renewables_share_elec"].ge(renewable_median)
            & result["renewable_improvement"].lt(progress_median),
        ],
        [
            "Leaders",
            "Catching Up",
            "Established but Slower",
        ],
        default="Falling Behind",
    )

    return result


def apply_page_style() -> None:
    """Apply a consistent, CVD-safe, professional dashboard theme."""
    st.markdown(
        """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 80% 5%,
            rgba(0, 114, 178, 0.10),
            transparent 25%
        ),
        linear-gradient(
            180deg,
            #07111D 0%,
            #081522 55%,
            #06101B 100%
        );
}

.block-container {
    max-width: 1500px;
    padding-top: 1.25rem;
    padding-bottom: 3rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #071827 0%,
            #06131F 100%
        );
    border-right: 1px solid rgba(56, 189, 248, 0.15);
}

section[data-testid="stSidebar"] a {
    border-radius: 10px;
    margin-bottom: 6px;
}

@keyframes cardReveal {
    from {
        opacity: 0;
        transform: translateY(18px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes chartReveal {
    from {
        opacity: 0;
        transform: translateY(12px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

div[data-testid="stMetric"] {
    min-height: 140px;
    padding: 18px 20px;
    border-radius: 16px;
    background:
        linear-gradient(
            145deg,
            rgba(10, 29, 47, 0.98),
            rgba(6, 22, 36, 0.98)
        );
    border: 1px solid rgba(56, 189, 248, 0.16);
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.24);
    animation: cardReveal 0.8s ease-out both;
    transition:
        transform 0.25s ease,
        border-color 0.25s ease,
        box-shadow 0.25s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    border-color: rgba(56, 189, 248, 0.34);
    box-shadow: 0 18px 38px rgba(0, 0, 0, 0.30);
}

div[data-testid="stMetricLabel"] p {
    color: #94A3B8 !important;
    font-weight: 700 !important;
}

div[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-weight: 850 !important;
}

div[data-testid="stMetricDelta"] {
    font-weight: 750 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background:
        linear-gradient(
            145deg,
            rgba(10, 29, 47, 0.96),
            rgba(6, 22, 36, 0.98)
        );
    border: 1px solid rgba(148, 163, 184, 0.14) !important;
    border-radius: 16px !important;
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.20);
}

div[data-testid="stPlotlyChart"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(56, 189, 248, 0.13);
    background: rgba(7, 24, 39, 0.72);
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.20);
    animation: chartReveal 0.9s ease-out both;
}

button[data-baseweb="tab"] {
    font-weight: 750;
}

details[data-testid="stExpander"] {
    background: rgba(7, 24, 39, 0.78);
    border: 1px solid rgba(56, 189, 248, 0.13);
    border-radius: 13px;
}

h1, h2, h3 {
    color: #F8FAFC;
}

p, li {
    line-height: 1.6;
}

@media (prefers-reduced-motion: reduce) {
    div[data-testid="stMetric"],
    div[data-testid="stPlotlyChart"] {
        animation: none !important;
        transition: none !important;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )


def style_plotly(
    fig: go.Figure,
    *,
    height: int = 560,
    show_legend: bool = True,
) -> go.Figure:
    """Apply the shared dark Plotly style."""
    fig.update_layout(
        height=height,
        template=None,
        paper_bgcolor="rgba(7,24,39,0)",
        plot_bgcolor="rgba(7,24,39,0)",
        font=dict(
            family="Arial",
            size=12,
            color=PALETTE["light_grey"],
        ),
        title=dict(
            x=0.02,
            xanchor="left",
            font=dict(
                size=18,
                color=PALETTE["white"],
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            visible=show_legend,
        ),
        margin=dict(l=35, r=35, t=80, b=55),
        hoverlabel=dict(
            bgcolor="#0B1F31",
            bordercolor=PALETTE["sky"],
            font_color=PALETTE["white"],
        ),
    )

    fig.update_xaxes(
        gridcolor="rgba(148,163,184,0.14)",
        linecolor="rgba(148,163,184,0.25)",
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.14)",
        linecolor="rgba(148,163,184,0.25)",
        zeroline=False,
    )

    return fig

def render_top_turbine() -> None:
    """
    Render a compact professional wind-turbine indicator at the top-right
    of every dashboard page.
    """
    turbine_html = """
<style>
@keyframes professionalTurbineSpin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.energy-turbine-badge {
    position: fixed;
    top: 76px;
    right: 96px;
    width: 58px;
    height: 58px;
    z-index: 999;
    pointer-events: none;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 16px;
    background:
        linear-gradient(
            145deg,
            rgba(7, 24, 39, 0.82),
            rgba(8, 21, 34, 0.66)
        );

    border: 1px solid rgba(125, 211, 252, 0.22);

    box-shadow:
        0 10px 26px rgba(0, 0, 0, 0.24),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);

    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.energy-turbine-icon {
    position: relative;
    width: 34px;
    height: 40px;
}

.energy-turbine-tower {
    position: absolute;
    left: 15px;
    top: 16px;
    width: 4px;
    height: 24px;
    border-radius: 3px 3px 1px 1px;

    background:
        linear-gradient(
            90deg,
            #64748B 0%,
            #E2E8F0 45%,
            #94A3B8 100%
        );

    clip-path: polygon(42% 0, 58% 0, 100% 100%, 0 100%);
}

.energy-turbine-head {
    position: absolute;
    left: 12px;
    top: 12px;
    width: 10px;
    height: 6px;
    border-radius: 6px;

    background:
        linear-gradient(
            180deg,
            #F8FAFC 0%,
            #CBD5E1 100%
        );

    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.22);
}

.energy-turbine-rotor {
    position: absolute;
    left: 17px;
    top: 15px;
    width: 6px;
    height: 6px;

    transform-origin: 0 0;
    animation: professionalTurbineSpin 5.2s linear infinite;
}

.energy-turbine-hub {
    position: absolute;
    left: -4px;
    top: -4px;
    width: 8px;
    height: 8px;
    z-index: 3;
    border-radius: 50%;

    background:
        radial-gradient(
            circle at 35% 30%,
            #E0F2FE 0%,
            #38BDF8 42%,
            #0369A1 100%
        );

    box-shadow:
        0 0 0 2px rgba(56, 189, 248, 0.12),
        0 1px 3px rgba(0, 0, 0, 0.28);
}

.energy-turbine-blade {
    position: absolute;
    left: -1.6px;
    top: -15px;
    width: 3.2px;
    height: 17px;

    border-radius: 90% 30% 44% 44%;
    transform-origin: 1.6px 18px;

    background:
        linear-gradient(
            90deg,
            #CBD5E1 0%,
            #FFFFFF 52%,
            #94A3B8 100%
        );

    opacity: 0.96;
}

.energy-blade-two {
    transform: rotate(120deg);
}

.energy-blade-three {
    transform: rotate(240deg);
}

.energy-turbine-status {
    position: absolute;
    right: 7px;
    bottom: 7px;
    width: 6px;
    height: 6px;
    border-radius: 50%;

    background: #22C55E;

    box-shadow:
        0 0 0 3px rgba(34, 197, 94, 0.10),
        0 0 8px rgba(34, 197, 94, 0.34);
}

@media (max-width: 900px) {
    .energy-turbine-badge {
        top: 72px;
        right: 58px;
        transform: scale(0.90);
        transform-origin: top right;
    }
}

@media (max-width: 620px) {
    .energy-turbine-badge {
        display: none;
    }
}

@media (prefers-reduced-motion: reduce) {
    .energy-turbine-rotor {
        animation: none !important;
    }
}
</style>

<div class="energy-turbine-badge" aria-hidden="true">
    <div class="energy-turbine-icon">
        <div class="energy-turbine-tower"></div>
        <div class="energy-turbine-head"></div>

        <div class="energy-turbine-rotor">
            <div class="energy-turbine-hub"></div>
            <div class="energy-turbine-blade energy-blade-one"></div>
            <div class="energy-turbine-blade energy-blade-two"></div>
            <div class="energy-turbine-blade energy-blade-three"></div>
        </div>
    </div>

    <div class="energy-turbine-status"></div>
</div>
"""

    st.html(turbine_html)
