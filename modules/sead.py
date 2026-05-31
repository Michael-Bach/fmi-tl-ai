import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8
THREAT_MODES = {"Barrage": -10, "Spot": 0, "Sweep": -5}


@st.cache_data
def compute_sead(
    strike_range_km: float,
    jammer_offset_km: float,
    jammer_offset_angle_deg: float,
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_strike_dbsm: float,
    threat_mode: str,
) -> dict:
    mode_penalty = THREAT_MODES[threat_mode]

    # Geometry (radar at origin, strike package on x-axis)
    angle_rad = np.radians(jammer_offset_angle_deg)
    jammer_x = strike_range_km + jammer_offset_km * np.cos(angle_rad)
    jammer_y = jammer_offset_km * np.sin(angle_rad)

    R_t_m = strike_range_km * 1e3
    R_j_m = np.sqrt(jammer_x**2 + jammer_y**2) * 1e3
    R_j_m = max(R_j_m, 1e3)

    # Escort jammer J/S (R_t ≠ R_j):
    # J/S = ERP_J - ERP_R + 10·log10(4π) + 40·log10(R_t) - 20·log10(R_j) - RCS + mode
    js_current = (
        jammer_erp_dbw + mode_penalty
        - radar_erp_dbw
        + 10 * np.log10(4 * np.pi)
        + 40 * np.log10(R_t_m)
        - 20 * np.log10(R_j_m)
        - rcs_strike_dbsm
    )

    # Ingress timeline: strike package closes from 300 km to 10 km
    # Jammer trails directly behind strike package (along ingress axis)
    ingress_ranges_km = np.linspace(300, 10, 300)
    R_t_arr = ingress_ranges_km * 1e3
    # Jammer at fixed trailing offset along track
    R_j_arr = np.clip((ingress_ranges_km + jammer_offset_km) * 1e3, 1e3, None)

    js_timeline = (
        jammer_erp_dbw + mode_penalty
        - radar_erp_dbw
        + 10 * np.log10(4 * np.pi)
        + 40 * np.log10(R_t_arr)
        - 20 * np.log10(R_j_arr)
        - rcs_strike_dbsm
    )

    return {
        "js_current": float(js_current),
        "R_strike_km": strike_range_km,
        "R_jammer_km": float(R_j_m / 1e3),
        "jammer_x": jammer_x,
        "jammer_y": jammer_y,
        "ingress_ranges_km": ingress_ranges_km,
        "js_timeline": js_timeline,
    }


def render():
    st.header("SEAD/DEAD Scenario — Escort Jammer Geometry")
    st.caption(
        "Two-node geometry: escort jammer at offset from the strike package. "
        "J/S uses the full escort equation (R_T ≠ R_J). "
        "Ingress timeline shows J/S evolving as the strike package closes on the threat radar."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**Strike package**")
        strike_range = st.slider("Strike range from radar (km)", 50, 400, 150, 10)
        rcs_strike = st.slider(
            "Strike platform RCS (dBsm)", -20, 15, -15, 1,
            help="F-35A ≈ −15 dBsm · legacy fighter ≈ +5 dBsm · large aircraft ≈ +15 dBsm",
        )

        st.markdown("**Escort jammer**")
        jammer_offset = st.slider("Offset from strike package (km)", 0, 100, 20, 5)
        jammer_angle = st.slider(
            "Offset angle (°)", -90, 90, 0, 5,
            help="0° = directly behind (rearward), 90° = perpendicular (flank)",
        )
        jammer_erp = st.slider("Jammer ERP (dBW)", -10, 60, 30, 1)
        threat_mode = st.selectbox("Jamming mode", list(THREAT_MODES.keys()), index=1)

        st.markdown("**Threat radar**")
        radar_erp = st.slider("Radar ERP (dBW)", 20, 80, 55, 1)

    result = compute_sead(
        strike_range, jammer_offset, jammer_angle,
        jammer_erp, radar_erp, rcs_strike, threat_mode,
    )

    with col_b:
        # Geometry diagram
        fig_geo = go.Figure()
        max_dim = max(result["R_strike_km"], abs(result["jammer_x"]), abs(result["jammer_y"]), 10) * 1.2

        # Radar coverage circle (illustrative — fixed 50 km radius)
        theta = np.linspace(0, 2 * np.pi, 120)
        fig_geo.add_trace(go.Scatter(
            x=50 * np.cos(theta), y=50 * np.sin(theta),
            mode="lines", line=dict(color="#f85149", width=0.5, dash="dot"),
            name="Radar coverage (illustrative)", hoverinfo="skip",
        ))

        fig_geo.add_trace(go.Scatter(
            x=[0], y=[0], mode="markers+text",
            marker=dict(color="#f85149", size=14, symbol="triangle-up"),
            text=["SAM radar"], textposition="bottom center",
            textfont=dict(family="Courier New", color="#f85149", size=10),
            name="Threat radar",
        ))
        fig_geo.add_trace(go.Scatter(
            x=[result["R_strike_km"]], y=[0], mode="markers+text",
            marker=dict(color="#58a6ff", size=12, symbol="diamond"),
            text=["Strike"], textposition="top center",
            textfont=dict(family="Courier New", color="#58a6ff", size=10),
            name="Strike package",
        ))
        fig_geo.add_trace(go.Scatter(
            x=[result["jammer_x"]], y=[result["jammer_y"]], mode="markers+text",
            marker=dict(color="#39d353", size=12, symbol="star"),
            text=["Jammer"], textposition="top right",
            textfont=dict(family="Courier New", color="#39d353", size=10),
            name="Escort jammer",
        ))
        fig_geo.add_trace(go.Scatter(
            x=[0, result["R_strike_km"]], y=[0, 0], mode="lines",
            line=dict(color="#58a6ff", dash="dot", width=1),
            name=f"R_target = {result['R_strike_km']:.0f} km",
        ))
        fig_geo.add_trace(go.Scatter(
            x=[0, result["jammer_x"]], y=[0, result["jammer_y"]], mode="lines",
            line=dict(color="#39d353", dash="dot", width=1),
            name=f"R_jammer = {result['R_jammer_km']:.1f} km",
        ))
        fig_geo.update_layout(
            title=dict(text="Engagement Geometry",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Range (km)", gridcolor="#21262d",
                       range=[-max_dim * 0.1, max_dim]),
            yaxis=dict(title="Cross-range (km)", gridcolor="#21262d",
                       range=[-max_dim * 0.4, max_dim * 0.4], scaleanchor="x"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d", font=dict(size=10)),
            margin=dict(l=60, r=20, t=50, b=50), height=300,
        )
        st.plotly_chart(fig_geo, use_container_width=True)

        # Ingress timeline
        fig_tl = go.Figure()
        js = result["js_timeline"]
        colors = np.where(js >= 0, "#39d353", "#f85149")
        # Plot as a single coloured line via scatter
        fig_tl.add_trace(go.Scatter(
            x=result["ingress_ranges_km"], y=js,
            mode="lines", line=dict(color="#39d353", width=2),
            name="J/S (escort)",
        ))
        fig_tl.add_hline(
            y=0, line=dict(color="#e3b341", dash="dash", width=1.5),
            annotation_text="Burn-through threshold (J/S = 0 dB)",
            annotation_font=dict(color="#e3b341", family="Courier New", size=10),
        )
        fig_tl.update_layout(
            title=dict(text="J/S During Ingress ← strike package closes on radar →",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Strike package range from radar (km)", gridcolor="#21262d",
                       autorange="reversed"),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=260,
        )
        st.plotly_chart(fig_tl, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        js_c = result["js_current"]
        m1.metric("J/S at current geometry (dB)", f"{js_c:.1f}")
        m2.metric("R_jammer (km)", f"{result['R_jammer_km']:.1f}")
        effective = js_c > 0
        m3.metric(
            "Jammer status",
            "EFFECTIVE" if effective else "BURNED THROUGH",
            delta=None,
            help="J/S > 0 dB means jammer power exceeds radar return power",
        )
        if not effective:
            st.warning(
                "J/S < 0 dB: radar return exceeds jammer power at this geometry. "
                "Increase jammer ERP, reduce target RCS, or increase jammer offset range.",
                icon="⚠️",
            )
