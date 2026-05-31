"""
Electronic Order of Battle + EMCON deconfliction planner.

Renders a 2D tactical picture: threat emitters with detection range circles,
friendly emitters with ESM exposure zones, EMCON state toggle.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

# Threat emitters (notional Baltic/OSINT-level data)
DEFAULT_THREAT_EMITTERS = [
    {"id": "T-1", "name": "S-400 Gravestone (X-band FC)", "x_km": 0,   "y_km": 0,
     "freq_ghz": 10, "erp_dbw": 58, "function": "Fire control",
     "esm_sensitivity_dbm": -75, "detection_range_km": 180},
    {"id": "T-2", "name": "S-400 Big Bird (VHF acquisition)", "x_km": 10, "y_km": -5,
     "freq_ghz": 0.3, "erp_dbw": 65, "function": "Acquisition",
     "esm_sensitivity_dbm": -80, "detection_range_km": 300},
    {"id": "T-3", "name": "Nebo-M (UHF ABM radar)", "x_km": -20, "y_km": 15,
     "freq_ghz": 0.6, "erp_dbw": 62, "function": "ABM search",
     "esm_sensitivity_dbm": -78, "detection_range_km": 350},
]

# Friendly emitters
DEFAULT_FRIENDLY_EMITTERS = [
    {"id": "F-1", "name": "F-35A AN/APG-81 (X-band)", "erp_dbw": 35,
     "freq_ghz": 10, "emcon_state_off": 2, "function": "Airborne radar"},
    {"id": "F-2", "name": "MADL datalink (Ku-band)", "erp_dbw": 15,
     "freq_ghz": 15, "emcon_state_off": 2, "function": "Datalink"},
    {"id": "F-3", "name": "IFF transponder (L-band)", "erp_dbw": 10,
     "freq_ghz": 1.0, "emcon_state_off": 2, "function": "IFF"},
    {"id": "F-4", "name": "Self-protection jammer (multi-band)", "erp_dbw": 25,
     "freq_ghz": 10, "emcon_state_off": 0, "function": "EW — always on"},
]

EMCON_LABELS = {0: "EMCON 0 — Unrestricted", 1: "EMCON 1 — Essential only", 2: "EMCON 2 — Silent"}


def _esm_detection_range_km(erp_dbw: float, freq_ghz: float, esm_sensitivity_dbm: float) -> float:
    wavelength = SPEED_OF_LIGHT / (freq_ghz * 1e9)
    # P_received(dBm) = ERP - FSPL + 30; solve for R where P_received = sensitivity
    log_r = (erp_dbw + 30 - esm_sensitivity_dbm - 20 * np.log10(4 * np.pi / wavelength)) / 20
    return float(10 ** log_r / 1e3)


def _circle(cx, cy, r_km, n=120):
    theta = np.linspace(0, 2 * np.pi, n)
    return cx + r_km * np.cos(theta), cy + r_km * np.sin(theta)


def render():
    st.header("Electronic Order of Battle — Threat Picture & EMCON Planner")
    st.caption(
        "Threat emitters with detection and engagement range circles. "
        "Friendly emitters with ESM exposure under each EMCON state. "
        "Shows which friendly emitters are detectable at which ingress ranges."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        emcon = st.select_slider(
            "EMCON state",
            options=[0, 1, 2],
            value=1,
            format_func=lambda v: EMCON_LABELS[v],
        )
        platform_x = st.slider("Platform X (km)", -100, 300, 150, 5,
                                help="Friendly platform position (x-axis)")
        platform_y = st.slider("Platform Y (km)", -150, 150, 0, 5)

        st.markdown("**Active friendly emitters under selected EMCON:**")
        active_friendly = [
            f for f in DEFAULT_FRIENDLY_EMITTERS
            if f["emcon_state_off"] > emcon
        ]
        if not active_friendly:
            st.caption("All emitters silenced.")
        for f in active_friendly:
            st.caption(f"📡 {f['name']}")

    with col_b:
        fig = go.Figure()
        all_x, all_y = [platform_x], [platform_y]

        # Threat emitters
        for t in DEFAULT_THREAT_EMITTERS:
            all_x.append(t["x_km"])
            all_y.append(t["y_km"])

            cx, cy = _circle(t["x_km"], t["y_km"], t["detection_range_km"])
            fig.add_trace(go.Scatter(
                x=cx, y=cy, mode="lines",
                line=dict(color="rgba(248,81,73,0.25)", width=1),
                showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=[t["x_km"]], y=[t["y_km"]],
                mode="markers+text",
                marker=dict(color="#f85149", size=10, symbol="triangle-up"),
                text=[t["id"]], textposition="top center",
                textfont=dict(family="Courier New", color="#f85149", size=9),
                name=f"{t['id']} {t['name'][:25]}",
                hovertemplate=(
                    f"<b>{t['name']}</b><br>"
                    f"Function: {t['function']}<br>"
                    f"ERP: {t['erp_dbw']} dBW · Freq: {t['freq_ghz']} GHz<br>"
                    f"Detection range: {t['detection_range_km']} km"
                    "<extra></extra>"
                ),
            ))

        # Friendly emitter ESM exposure circles
        for fe in active_friendly:
            for t in DEFAULT_THREAT_EMITTERS:
                esm_r = _esm_detection_range_km(fe["erp_dbw"], fe["freq_ghz"],
                                                 t["esm_sensitivity_dbm"])
                if esm_r > 5:
                    cx, cy = _circle(platform_x, platform_y, esm_r)
                    fig.add_trace(go.Scatter(
                        x=cx, y=cy, mode="lines",
                        line=dict(color="rgba(57,211,83,0.20)", width=1, dash="dot"),
                        showlegend=False, hoverinfo="skip",
                    ))

        # Platform marker
        fig.add_trace(go.Scatter(
            x=[platform_x], y=[platform_y],
            mode="markers+text",
            marker=dict(color="#58a6ff", size=14, symbol="star"),
            text=["Platform"], textposition="top right",
            textfont=dict(family="Courier New", color="#58a6ff", size=10),
            name="Friendly platform",
        ))

        # Check which threats can detect the platform
        detections = []
        for t in DEFAULT_THREAT_EMITTERS:
            dist = np.sqrt((platform_x - t["x_km"])**2 + (platform_y - t["y_km"])**2)
            if dist <= t["detection_range_km"]:
                detections.append(t)

        # Check which friendly emitters are detectable by threat ESM
        exposures = []
        for fe in active_friendly:
            for t in DEFAULT_THREAT_EMITTERS:
                esm_r = _esm_detection_range_km(fe["erp_dbw"], fe["freq_ghz"],
                                                 t["esm_sensitivity_dbm"])
                dist = np.sqrt((platform_x - t["x_km"])**2 + (platform_y - t["y_km"])**2)
                if dist <= esm_r:
                    exposures.append((fe, t, dist))

        pad = 50
        x_range = [min(all_x) - pad, max(all_x) + pad]
        y_range = [min(all_y) - pad, max(all_y) + pad]

        fig.update_layout(
            title=dict(text=f"EOB — {EMCON_LABELS[emcon]}",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="East (km)", gridcolor="#21262d",
                       range=x_range, scaleanchor="y"),
            yaxis=dict(title="North (km)", gridcolor="#21262d", range=y_range),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d",
                        font=dict(family="Courier New", size=9)),
            margin=dict(l=60, r=20, t=60, b=50),
            height=460,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Exposure summary
        m1, m2, m3 = st.columns(3)
        m1.metric("Active friendly emitters", len(active_friendly))
        m2.metric("Threat radars with platform in range", len(detections))
        m3.metric("ESM intercept exposures", len(exposures))

        if detections:
            st.warning(
                "Platform is within detection range of: "
                + ", ".join(t["name"] for t in detections),
                icon="⚠️",
            )

        if exposures:
            st.error(
                "ESM intercept risk under current EMCON: "
                + "; ".join(f"{e[0]['name']} detectable by {e[1]['id']} at {e[2]:.0f} km"
                            for e in exposures),
                icon="📡",
            )
        elif active_friendly:
            st.success(
                f"No ESM intercept exposure at current position under {EMCON_LABELS[emcon]}.",
            )

        with st.expander("EMCON planning rationale"):
            st.markdown(
                "JEMSO planning requires knowing which friendly emitters create detectable "
                "signatures against threat ESM before entering the engagement zone. "
                "This tool maps the exposure geometry at mission planning time — "
                "reducing the risk of ESM-triggered targeting against the strike package."
            )
