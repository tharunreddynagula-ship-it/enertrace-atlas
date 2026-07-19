from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from utils import (
    PALETTE,
    apply_page_style,
)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Renewable Energy Lab",
    page_icon="⚡",
    layout="wide",
)

apply_page_style()

# =========================================================
# PAGE HEADER
# =========================================================

st.title("⚡ Renewable Energy Lab")
st.caption(
    "Explore how solar, wind, and hydropower convert natural resources "
    "into electricity through animated, interactive visual models."
)

st.info(
    """
Use the controls inside each tab to change the available natural resource.
The animation speed and estimated power output respond to your selections.
These are simplified educational models, not engineering design tools.
"""
)

solar_tab, wind_tab, hydro_tab, compare_tab = st.tabs(
    [
        "☀️ Solar Energy",
        "🌬️ Wind Energy",
        "💧 Hydropower",
        "📊 Compare Technologies",
    ]
)

# =========================================================
# SHARED HELPERS
# =========================================================


def power_badge(
    title: str,
    value: str,
    subtitle: str,
    accent: str,
) -> str:
    return f"""
<div class="power-badge" style="--accent:{accent};">
    <div class="power-badge-label">{title}</div>
    <div class="power-badge-value">{value}</div>
    <div class="power-badge-subtitle">{subtitle}</div>
</div>
"""


def common_visual_css() -> str:
    return """
<style>
.energy-scene {
    position: relative;
    width: 100%;
    min-height: 470px;
    overflow: hidden;
    border-radius: 22px;
    border: 1px solid rgba(56, 189, 248, 0.18);
    background:
        radial-gradient(
            circle at 76% 18%,
            rgba(56, 189, 248, 0.10),
            transparent 28%
        ),
        linear-gradient(
            180deg,
            #071827 0%,
            #082238 62%,
            #071521 100%
        );
    box-shadow: 0 20px 44px rgba(0, 0, 0, 0.28);
}

.scene-title {
    position: absolute;
    top: 20px;
    left: 24px;
    z-index: 10;
    color: #F8FAFC;
    font-size: 20px;
    font-weight: 850;
}

.scene-subtitle {
    position: absolute;
    top: 52px;
    left: 24px;
    z-index: 10;
    color: #94A3B8;
    font-size: 13px;
}

.flow-label {
    position: absolute;
    padding: 7px 11px;
    border-radius: 999px;
    background: rgba(7, 24, 39, 0.82);
    border: 1px solid rgba(125, 211, 252, 0.22);
    color: #E2E8F0;
    font-size: 12px;
    font-weight: 750;
    backdrop-filter: blur(8px);
}

.energy-grid {
    position: absolute;
    right: 38px;
    bottom: 68px;
    width: 76px;
    height: 88px;
}

.grid-pole {
    position: absolute;
    left: 36px;
    top: 10px;
    width: 5px;
    height: 77px;
    border-radius: 4px;
    background: linear-gradient(90deg, #64748B, #E2E8F0, #94A3B8);
}

.grid-arm {
    position: absolute;
    left: 10px;
    top: 22px;
    width: 57px;
    height: 4px;
    border-radius: 5px;
    background: #CBD5E1;
}

.grid-wire-one,
.grid-wire-two {
    position: absolute;
    left: -7px;
    width: 84px;
    height: 2px;
    background: rgba(148, 163, 184, 0.72);
    transform-origin: left center;
}

.grid-wire-one {
    top: 22px;
    transform: rotate(-6deg);
}

.grid-wire-two {
    top: 34px;
    transform: rotate(5deg);
}

.electric-line {
    position: absolute;
    height: 4px;
    border-radius: 999px;
    background:
        repeating-linear-gradient(
            90deg,
            #38BDF8 0 12px,
            rgba(56, 189, 248, 0.18) 12px 24px
        );
    background-size: 48px 100%;
    animation: electricityFlow var(--electric-speed) linear infinite;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.32);
}

@keyframes electricityFlow {
    from { background-position: 0 0; }
    to { background-position: 48px 0; }
}

.power-badge {
    margin-top: 0.6rem;
    padding: 18px 20px;
    border-radius: 16px;
    border: 1px solid color-mix(in srgb, var(--accent) 34%, transparent);
    background:
        linear-gradient(
            145deg,
            rgba(10, 29, 47, 0.98),
            rgba(6, 22, 36, 0.98)
        );
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
}

.power-badge-label {
    color: #94A3B8;
    font-size: 13px;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.power-badge-value {
    margin-top: 5px;
    color: var(--accent);
    font-size: 31px;
    font-weight: 900;
}

.power-badge-subtitle {
    margin-top: 4px;
    color: #CBD5E1;
    font-size: 13px;
    line-height: 1.45;
}

@media (max-width: 780px) {
    .energy-scene {
        min-height: 420px;
    }

    .scene-title {
        font-size: 17px;
    }
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
    }
}
</style>
"""


# =========================================================
# SOLAR ENERGY
# =========================================================

with solar_tab:
    control_col, visual_col = st.columns(
        [0.34, 0.66],
        gap="large",
    )

    with control_col:
        st.subheader("Solar controls")

        irradiance = st.slider(
            "Sunlight intensity (W/m²)",
            min_value=200,
            max_value=1100,
            value=800,
            step=50,
            help="Approximate solar irradiance reaching the panel.",
        )

        panel_area = st.slider(
            "Panel area (m²)",
            min_value=10,
            max_value=250,
            value=100,
            step=10,
        )

        panel_efficiency = st.slider(
            "Panel efficiency (%)",
            min_value=10,
            max_value=30,
            value=20,
            step=1,
        )

        solar_power_kw = (
            panel_area
            * irradiance
            * (panel_efficiency / 100)
            / 1000
        )

        st.html(
            power_badge(
                "Estimated solar output",
                f"{solar_power_kw:,.1f} kW",
                (
                    f"{panel_area} m² of panels at "
                    f"{irradiance} W/m² and {panel_efficiency}% efficiency"
                ),
                PALETTE["orange"],
            )
        )

        st.markdown(
            """
### How it works

1. Sunlight carries energy as photons.
2. Photovoltaic cells release moving electrons.
3. The panel produces direct current (DC).
4. An inverter converts DC into alternating current (AC).
5. The electricity is used locally or delivered to the grid.
"""
        )

    solar_ray_duration = max(
        0.65,
        3.2 - irradiance / 430,
    )
    solar_electric_duration = max(
        0.55,
        2.5 - irradiance / 700,
    )

    solar_html = f"""
{common_visual_css()}
<style>
.solar-scene {{
    --ray-speed: {solar_ray_duration:.2f}s;
    --electric-speed: {solar_electric_duration:.2f}s;
}}

.solar-sun {{
    position: absolute;
    right: 84px;
    top: 84px;
    width: 78px;
    height: 78px;
    border-radius: 50%;
    background:
        radial-gradient(
            circle at 35% 30%,
            #FFF7C2 0%,
            #FACC15 42%,
            #F59E0B 74%,
            #D97706 100%
        );
    box-shadow:
        0 0 25px rgba(250, 204, 21, 0.62),
        0 0 70px rgba(245, 158, 11, 0.24);
    animation: solarPulse 2.8s ease-in-out infinite;
}}

@keyframes solarPulse {{
    0%, 100% {{ transform: scale(1); }}
    50% {{ transform: scale(1.05); }}
}}

.sun-ray {{
    position: absolute;
    top: 155px;
    width: 5px;
    height: 105px;
    border-radius: 999px;
    opacity: 0;
    background: linear-gradient(
        180deg,
        rgba(250, 204, 21, 0),
        rgba(250, 204, 21, 0.94),
        rgba(250, 204, 21, 0)
    );
    transform: rotate(24deg);
    animation: rayTravel var(--ray-speed) linear infinite;
}}

.ray-one {{ right: 158px; animation-delay: 0s; }}
.ray-two {{ right: 205px; animation-delay: -0.42s; }}
.ray-three {{ right: 252px; animation-delay: -0.84s; }}
.ray-four {{ right: 299px; animation-delay: -1.26s; }}

@keyframes rayTravel {{
    0% {{
        opacity: 0;
        transform: translateY(-20px) rotate(24deg);
    }}
    20% {{ opacity: 0.95; }}
    80% {{ opacity: 0.75; }}
    100% {{
        opacity: 0;
        transform: translateY(95px) rotate(24deg);
    }}
}}

.solar-panel {{
    position: absolute;
    left: 94px;
    bottom: 92px;
    width: 230px;
    height: 116px;
    transform: perspective(480px) rotateX(58deg) rotateZ(-7deg);
    border-radius: 8px;
    border: 5px solid #CBD5E1;
    background:
        linear-gradient(
            90deg,
            transparent 32%,
            rgba(255,255,255,0.28) 33% 34%,
            transparent 35% 65%,
            rgba(255,255,255,0.28) 66% 67%,
            transparent 68%
        ),
        linear-gradient(
            0deg,
            transparent 47%,
            rgba(255,255,255,0.28) 48% 50%,
            transparent 51%
        ),
        linear-gradient(135deg, #075985, #0EA5E9 54%, #0369A1);
    box-shadow:
        0 22px 30px rgba(0, 0, 0, 0.34),
        inset 0 0 20px rgba(125, 211, 252, 0.24);
}}

.panel-glint {{
    position: absolute;
    left: 120px;
    bottom: 142px;
    width: 160px;
    height: 5px;
    border-radius: 999px;
    background: rgba(255,255,255,0.72);
    filter: blur(2px);
    transform: rotate(-14deg);
    animation: panelGlint 3s ease-in-out infinite;
}}

@keyframes panelGlint {{
    0%, 100% {{ opacity: 0.15; transform: translateX(-20px) rotate(-14deg); }}
    50% {{ opacity: 0.78; transform: translateX(20px) rotate(-14deg); }}
}}

.solar-inverter {{
    position: absolute;
    left: 390px;
    bottom: 104px;
    width: 78px;
    height: 94px;
    border-radius: 14px;
    background: linear-gradient(145deg, #F8FAFC, #94A3B8);
    border: 1px solid rgba(255,255,255,0.55);
    box-shadow: 0 15px 25px rgba(0,0,0,0.28);
}}

.inverter-screen {{
    position: absolute;
    left: 18px;
    top: 18px;
    width: 42px;
    height: 24px;
    border-radius: 5px;
    background: #052E3B;
    box-shadow: inset 0 0 8px rgba(34,197,94,0.36);
}}

.inverter-light {{
    position: absolute;
    left: 34px;
    bottom: 18px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 10px rgba(34,197,94,0.72);
}}

.solar-cable-one {{
    left: 305px;
    bottom: 132px;
    width: 92px;
}}

.solar-cable-two {{
    left: 464px;
    bottom: 132px;
    width: calc(100% - 590px);
}}

.solar-label-source {{ left: 96px; bottom: 44px; }}
.solar-label-convert {{ left: 380px; bottom: 44px; }}
.solar-label-grid {{ right: 28px; bottom: 25px; }}
</style>

<div class="energy-scene solar-scene">
    <div class="scene-title">Solar photovoltaic conversion</div>
    <div class="scene-subtitle">
        Sunlight → DC electricity → inverter → AC grid electricity
    </div>

    <div class="solar-sun"></div>

    <div class="sun-ray ray-one"></div>
    <div class="sun-ray ray-two"></div>
    <div class="sun-ray ray-three"></div>
    <div class="sun-ray ray-four"></div>

    <div class="solar-panel"></div>
    <div class="panel-glint"></div>

    <div class="solar-inverter">
        <div class="inverter-screen"></div>
        <div class="inverter-light"></div>
    </div>

    <div class="electric-line solar-cable-one"></div>
    <div class="electric-line solar-cable-two"></div>

    <div class="energy-grid">
        <div class="grid-pole"></div>
        <div class="grid-arm"></div>
        <div class="grid-wire-one"></div>
        <div class="grid-wire-two"></div>
    </div>

    <div class="flow-label solar-label-source">1 · Capture sunlight</div>
    <div class="flow-label solar-label-convert">2 · Convert DC to AC</div>
    <div class="flow-label solar-label-grid">3 · Supply the grid</div>
</div>
"""

    with visual_col:
        st.html(solar_html)


# =========================================================
# WIND ENERGY
# =========================================================

with wind_tab:
    control_col, visual_col = st.columns(
        [0.34, 0.66],
        gap="large",
    )

    with control_col:
        st.subheader("Wind controls")

        wind_speed = st.slider(
            "Wind speed (m/s)",
            min_value=3.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
        )

        rotor_radius = st.slider(
            "Rotor radius (m)",
            min_value=5,
            max_value=60,
            value=20,
            step=5,
        )

        power_coefficient = st.slider(
            "Power coefficient",
            min_value=0.20,
            max_value=0.50,
            value=0.40,
            step=0.01,
            help=(
                "Fraction of available wind power captured by the turbine. "
                "The Betz-limit maximum is about 0.593."
            ),
        )

        air_density = 1.225
        swept_area = math.pi * rotor_radius**2

        wind_power_kw = (
            0.5
            * air_density
            * swept_area
            * wind_speed**3
            * power_coefficient
            / 1000
        )

        st.html(
            power_badge(
                "Estimated wind output",
                f"{wind_power_kw:,.0f} kW",
                (
                    f"{wind_speed:.1f} m/s wind, "
                    f"{rotor_radius} m rotor radius, "
                    f"Cp {power_coefficient:.2f}"
                ),
                PALETTE["sky"],
            )
        )

        st.markdown(
            """
### How it works

1. Moving air pushes the turbine blades.
2. The rotor turns a shaft inside the nacelle.
3. A generator converts mechanical rotation into electricity.
4. Power electronics regulate voltage and frequency.
5. A transformer sends electricity to the grid.
"""
        )

    wind_rotation_duration = max(
        0.55,
        5.4 - wind_speed * 0.24,
    )
    wind_streak_duration = max(
        0.7,
        3.4 - wind_speed * 0.12,
    )
    wind_electric_duration = max(
        0.55,
        2.8 - wind_speed * 0.08,
    )

    wind_html = f"""
{common_visual_css()}
<style>
.wind-scene {{
    --rotor-speed: {wind_rotation_duration:.2f}s;
    --wind-speed: {wind_streak_duration:.2f}s;
    --electric-speed: {wind_electric_duration:.2f}s;
}}

.wind-hill-one,
.wind-hill-two {{
    position: absolute;
    bottom: -45px;
    border-radius: 50% 50% 0 0;
}}

.wind-hill-one {{
    left: -70px;
    width: 480px;
    height: 170px;
    background: linear-gradient(180deg, #065F46, #064E3B);
}}

.wind-hill-two {{
    right: -100px;
    width: 520px;
    height: 190px;
    background: linear-gradient(180deg, #047857, #065F46);
}}

.wind-streak {{
    position: absolute;
    left: -180px;
    width: 180px;
    height: 3px;
    border-radius: 999px;
    opacity: 0;
    background: linear-gradient(
        90deg,
        transparent,
        rgba(186, 230, 253, 0.95),
        transparent
    );
    animation: windTravel var(--wind-speed) linear infinite;
}}

.wind-one {{ top: 132px; animation-delay: 0s; }}
.wind-two {{ top: 188px; animation-delay: -0.7s; }}
.wind-three {{ top: 246px; animation-delay: -1.4s; }}
.wind-four {{ top: 304px; animation-delay: -2.1s; }}

@keyframes windTravel {{
    0% {{
        opacity: 0;
        transform: translateX(0);
    }}
    15% {{ opacity: 0.9; }}
    85% {{ opacity: 0.75; }}
    100% {{
        opacity: 0;
        transform: translateX(900px);
    }}
}}

.main-wind-turbine {{
    position: absolute;
    left: 230px;
    bottom: 85px;
    width: 210px;
    height: 315px;
}}

.wind-tower {{
    position: absolute;
    left: 101px;
    top: 86px;
    width: 12px;
    height: 225px;
    border-radius: 8px 8px 3px 3px;
    background: linear-gradient(90deg, #64748B, #F8FAFC, #94A3B8);
    clip-path: polygon(42% 0, 58% 0, 100% 100%, 0 100%);
    filter: drop-shadow(0 10px 9px rgba(0,0,0,0.30));
}}

.wind-nacelle {{
    position: absolute;
    left: 89px;
    top: 71px;
    width: 42px;
    height: 22px;
    border-radius: 15px 15px 9px 9px;
    background: linear-gradient(180deg, #FFFFFF, #CBD5E1 65%, #64748B);
    box-shadow: 0 4px 8px rgba(0,0,0,0.25);
}}

.wind-rotor {{
    position: absolute;
    left: 108px;
    top: 82px;
    width: 12px;
    height: 12px;
    transform-origin: 0 0;
    animation: windRotor var(--rotor-speed) linear infinite;
}}

@keyframes windRotor {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
}}

.wind-hub {{
    position: absolute;
    left: -8px;
    top: -8px;
    width: 16px;
    height: 16px;
    z-index: 4;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 30%, #FFFFFF, #38BDF8, #075985);
    box-shadow: 0 0 0 4px rgba(56,189,248,0.15);
}}

.wind-blade {{
    position: absolute;
    left: -4px;
    top: -75px;
    width: 8px;
    height: 80px;
    border-radius: 90% 20% 45% 45%;
    transform-origin: 4px 81px;
    background: linear-gradient(90deg, #CBD5E1, #FFFFFF 48%, #94A3B8);
    box-shadow: 0 2px 4px rgba(0,0,0,0.18);
}}

.wind-blade-two {{ transform: rotate(120deg); }}
.wind-blade-three {{ transform: rotate(240deg); }}

.wind-generator {{
    position: absolute;
    left: 97px;
    top: 76px;
    width: 23px;
    height: 12px;
    border-radius: 8px;
    border: 2px solid rgba(34,197,94,0.55);
    box-shadow: 0 0 12px rgba(34,197,94,0.32);
}}

.wind-cable {{
    left: 343px;
    bottom: 119px;
    width: calc(100% - 470px);
}}

.wind-label-source {{ left: 105px; bottom: 34px; }}
.wind-label-convert {{ left: 330px; bottom: 34px; }}
.wind-label-grid {{ right: 28px; bottom: 25px; }}
</style>

<div class="energy-scene wind-scene">
    <div class="scene-title">Wind-turbine electricity generation</div>
    <div class="scene-subtitle">
        Wind kinetic energy → rotor motion → generator → electricity grid
    </div>

    <div class="wind-streak wind-one"></div>
    <div class="wind-streak wind-two"></div>
    <div class="wind-streak wind-three"></div>
    <div class="wind-streak wind-four"></div>

    <div class="wind-hill-one"></div>
    <div class="wind-hill-two"></div>

    <div class="main-wind-turbine">
        <div class="wind-tower"></div>
        <div class="wind-nacelle"></div>
        <div class="wind-generator"></div>

        <div class="wind-rotor">
            <div class="wind-hub"></div>
            <div class="wind-blade wind-blade-one"></div>
            <div class="wind-blade wind-blade-two"></div>
            <div class="wind-blade wind-blade-three"></div>
        </div>
    </div>

    <div class="electric-line wind-cable"></div>

    <div class="energy-grid">
        <div class="grid-pole"></div>
        <div class="grid-arm"></div>
        <div class="grid-wire-one"></div>
        <div class="grid-wire-two"></div>
    </div>

    <div class="flow-label wind-label-source">1 · Capture wind</div>
    <div class="flow-label wind-label-convert">2 · Rotate generator</div>
    <div class="flow-label wind-label-grid">3 · Export power</div>
</div>
"""

    with visual_col:
        st.html(wind_html)


# =========================================================
# HYDROPOWER
# =========================================================

with hydro_tab:
    control_col, visual_col = st.columns(
        [0.34, 0.66],
        gap="large",
    )

    with control_col:
        st.subheader("Hydropower controls")

        water_flow = st.slider(
            "Water flow (m³/s)",
            min_value=0.5,
            max_value=20.0,
            value=5.0,
            step=0.5,
        )

        hydraulic_head = st.slider(
            "Hydraulic head (m)",
            min_value=5,
            max_value=150,
            value=30,
            step=5,
            help="Vertical height difference available to the water.",
        )

        hydro_efficiency = st.slider(
            "Turbine-generator efficiency (%)",
            min_value=60,
            max_value=95,
            value=90,
            step=1,
        )

        water_density = 1000
        gravity = 9.81

        hydro_power_kw = (
            water_density
            * gravity
            * water_flow
            * hydraulic_head
            * (hydro_efficiency / 100)
            / 1000
        )

        st.html(
            power_badge(
                "Estimated hydro output",
                f"{hydro_power_kw:,.0f} kW",
                (
                    f"{water_flow:.1f} m³/s flow, "
                    f"{hydraulic_head} m head, "
                    f"{hydro_efficiency}% efficiency"
                ),
                PALETTE["teal"],
            )
        )

        st.markdown(
            """
### How it works

1. Stored or flowing water has gravitational energy.
2. Water moves through an intake and penstock.
3. The flow spins a hydraulic turbine.
4. The turbine drives an electrical generator.
5. A transformer delivers electricity to the grid.
"""
        )

    hydro_turbine_duration = max(
        0.55,
        4.5 - water_flow * 0.16,
    )
    water_duration = max(
        0.65,
        3.5 - water_flow * 0.10,
    )
    hydro_electric_duration = max(
        0.55,
        2.9 - water_flow * 0.07,
    )

    hydro_html = f"""
{common_visual_css()}
<style>
.hydro-scene {{
    --turbine-speed: {hydro_turbine_duration:.2f}s;
    --water-speed: {water_duration:.2f}s;
    --electric-speed: {hydro_electric_duration:.2f}s;
}}

.hydro-reservoir {{
    position: absolute;
    left: 42px;
    top: 112px;
    width: 245px;
    height: 120px;
    border-radius: 18px 18px 6px 6px;
    overflow: hidden;
    background: linear-gradient(180deg, #0EA5E9, #0369A1);
    border: 1px solid rgba(186,230,253,0.38);
    box-shadow: inset 0 10px 20px rgba(255,255,255,0.10);
}}

.water-surface {{
    position: absolute;
    left: -40px;
    top: -7px;
    width: 340px;
    height: 26px;
    background:
        repeating-radial-gradient(
            ellipse at center,
            rgba(255,255,255,0.58) 0 3px,
            transparent 4px 17px
        );
    animation: waterSurface 3.2s linear infinite;
}}

@keyframes waterSurface {{
    from {{ transform: translateX(0); }}
    to {{ transform: translateX(36px); }}
}}

.hydro-dam {{
    position: absolute;
    left: 280px;
    top: 96px;
    width: 82px;
    height: 258px;
    clip-path: polygon(8% 0, 72% 0, 100% 100%, 0 100%);
    background: linear-gradient(90deg, #64748B, #CBD5E1 46%, #475569);
    box-shadow: 15px 12px 26px rgba(0,0,0,0.30);
}}

.penstock {{
    position: absolute;
    left: 310px;
    top: 190px;
    width: 185px;
    height: 22px;
    border-radius: 999px;
    transform: rotate(27deg);
    transform-origin: left center;
    overflow: hidden;
    border: 3px solid #64748B;
    background: #082F49;
    box-shadow: 0 8px 16px rgba(0,0,0,0.24);
}}

.penstock-water {{
    width: 210px;
    height: 100%;
    background:
        repeating-linear-gradient(
            90deg,
            #38BDF8 0 18px,
            #0EA5E9 18px 36px
        );
    background-size: 72px 100%;
    animation: penstockFlow var(--water-speed) linear infinite;
}}

@keyframes penstockFlow {{
    from {{ background-position: 0 0; }}
    to {{ background-position: 72px 0; }}
}}

.hydro-house {{
    position: absolute;
    left: 445px;
    bottom: 88px;
    width: 132px;
    height: 112px;
    border-radius: 13px 13px 7px 7px;
    background: linear-gradient(145deg, #E2E8F0, #64748B);
    border: 1px solid rgba(255,255,255,0.50);
    box-shadow: 0 16px 26px rgba(0,0,0,0.28);
}}

.hydro-house-roof {{
    position: absolute;
    left: -10px;
    top: -28px;
    width: 152px;
    height: 40px;
    clip-path: polygon(50% 0, 100% 100%, 0 100%);
    background: #334155;
}}

.hydro-turbine {{
    position: absolute;
    left: 37px;
    top: 37px;
    width: 58px;
    height: 58px;
    border-radius: 50%;
    border: 5px solid #075985;
    background: radial-gradient(circle, #38BDF8 0 12%, #0C4A6E 13% 100%);
    animation: hydroSpin var(--turbine-speed) linear infinite;
    box-shadow: 0 0 18px rgba(56,189,248,0.40);
}}

@keyframes hydroSpin {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
}}

.hydro-turbine::before,
.hydro-turbine::after {{
    content: "";
    position: absolute;
    left: 22px;
    top: 3px;
    width: 8px;
    height: 42px;
    border-radius: 999px;
    background: #E0F2FE;
}}

.hydro-turbine::after {{
    transform: rotate(90deg);
}}

.hydro-cable {{
    left: 569px;
    bottom: 133px;
    width: calc(100% - 690px);
}}

.hydro-label-source {{ left: 70px; bottom: 34px; }}
.hydro-label-convert {{ left: 410px; bottom: 34px; }}
.hydro-label-grid {{ right: 28px; bottom: 25px; }}
</style>

<div class="energy-scene hydro-scene">
    <div class="scene-title">Hydroelectric power conversion</div>
    <div class="scene-subtitle">
        Water potential energy → water flow → turbine → generator → grid
    </div>

    <div class="hydro-reservoir">
        <div class="water-surface"></div>
    </div>

    <div class="hydro-dam"></div>

    <div class="penstock">
        <div class="penstock-water"></div>
    </div>

    <div class="hydro-house">
        <div class="hydro-house-roof"></div>
        <div class="hydro-turbine"></div>
    </div>

    <div class="electric-line hydro-cable"></div>

    <div class="energy-grid">
        <div class="grid-pole"></div>
        <div class="grid-arm"></div>
        <div class="grid-wire-one"></div>
        <div class="grid-wire-two"></div>
    </div>

    <div class="flow-label hydro-label-source">1 · Store & release water</div>
    <div class="flow-label hydro-label-convert">2 · Spin the turbine</div>
    <div class="flow-label hydro-label-grid">3 · Deliver electricity</div>
</div>
"""

    with visual_col:
        st.html(hydro_html)


# =========================================================
# COMPARISON TAB
# =========================================================

with compare_tab:
    st.subheader("How the Three Technologies Differ")
    st.caption(
        "All three produce electricity without direct fuel combustion, "
        "but they capture different natural energy flows."
    )

    comparison = pd.DataFrame(
        {
            "Technology": [
                "Solar photovoltaic",
                "Wind turbine",
                "Hydropower",
            ],
            "Natural input": [
                "Sunlight",
                "Moving air",
                "Flowing or falling water",
            ],
            "Primary conversion": [
                "Photons move electrons in semiconductor cells",
                "Wind rotates blades and generator shaft",
                "Water spins a hydraulic turbine",
            ],
            "Electrical stage": [
                "DC power converted to AC by inverter",
                "Generator produces AC electricity",
                "Generator produces AC electricity",
            ],
            "Main variability": [
                "Daylight and cloud cover",
                "Wind-speed changes",
                "Water availability and reservoir operation",
            ],
            "Typical strength": [
                "Modular and suitable from rooftops to utility scale",
                "High output in strong-wind locations",
                "Stable, controllable output where geography permits",
            ],
        }
    )

    st.dataframe(
        comparison,
        width="stretch",
        hide_index=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### ☀️ Solar")
        st.write(
            "Few moving parts, scalable installation, and direct "
            "conversion of light into electricity."
        )

    with c2:
        st.markdown("### 🌬️ Wind")
        st.write(
            "Output rises strongly with wind speed because available "
            "wind power is proportional to the cube of velocity."
        )

    with c3:
        st.markdown("### 💧 Hydro")
        st.write(
            "Can offer controllable generation and storage, but depends "
            "strongly on suitable geography and water systems."
        )

    st.warning(
        """
**Important interpretation:** The best electricity system normally uses
a portfolio of technologies. Solar, wind, hydro, storage, transmission,
and demand management can complement one another.
"""
    )

st.divider()
st.caption(
    "Educational visualisation created for the Global Energy Transition "
    "Analytics dashboard. Power estimates are simplified approximations."
)
