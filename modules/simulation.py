import datetime

import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

# Jamming mode bandwidth penalty (dB): power spread over wider band → less effective per Hz
THREAT_MODES = {"Barrage": -10, "Spot": 0, "Sweep": -5}

RCS_PRESETS = {
    "Fighter low-observable (F-35A, −15 dBsm)": -15,
    "Legacy fighter (~5 dBsm)": 5,
    "Large aircraft (~15 dBsm)": 15,
    "UAV (~−20 dBsm)": -20,
    "Frigate (~30 dBsm)": 30,
    "Custom": None,
}


@st.cache_data
def compute_js(
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
    radar_freq_ghz: float,
    esm_sensitivity_dbm: float,
    max_range_km: float,
    threat_mode: str,
) -> dict:
    mode_penalty = THREAT_MODES[threat_mode]
    ranges_km = np.linspace(1, max_range_km, 500)
    ranges_m = ranges_km * 1e3

    # Self-screening jammer J/S (Nathanson/Barton):
    # J/S = ERP_J / ERP_R × (4π × R²) / σ
    # In dB: J/S = ERP_J - ERP_R + 10·log10(4π) + 20·log10(R) - RCS + mode_penalty
    # Grows with R: radar return falls as R⁴, jammer signal falls as R² → jamming improves at range
    js_db = (
        jammer_erp_dbw
        + mode_penalty
        - radar_erp_dbw
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(ranges_m)
        - rcs_dbsm
    )

    # Burn-through: J/S = 0 dB → solve analytically for R_bt
    # R_bt(m) = 10^((ERP_R - ERP_J - mode + RCS - 10·log10(4π)) / 20)
    exponent = (
        radar_erp_dbw - jammer_erp_dbw - mode_penalty + rcs_dbsm
        - 10 * np.log10(4 * np.pi)
    ) / 20
    burn_through_km = (10 ** exponent) / 1e3

    # ESM received power: one-way free-space path loss
    wavelength = SPEED_OF_LIGHT / (radar_freq_ghz * 1e9)
    fspl_db = 20 * np.log10(4 * np.pi * ranges_m / wavelength)
    received_jammer_dbm = jammer_erp_dbw + mode_penalty - fspl_db + 30  # +30 dBW→dBm

    # ESM detection range: analytical inversion of FSPL equation
    log_r_esm = (
        jammer_erp_dbw + mode_penalty + 30
        - esm_sensitivity_dbm
        - 20 * np.log10(4 * np.pi / wavelength)
    ) / 20
    esm_detection_km = (10 ** log_r_esm) / 1e3

    return {
        "ranges_km": ranges_km,
        "js_db": js_db,
        "received_jammer_dbm": received_jammer_dbm,
        "burn_through_km": burn_through_km if 0 < burn_through_km <= max_range_km else None,
        "esm_detection_km": esm_detection_km if 0 < esm_detection_km <= max_range_km else None,
        "burn_through_km_raw": burn_through_km,
        "esm_detection_km_raw": esm_detection_km,
    }


@st.cache_data
def compute_monte_carlo(
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
    radar_freq_ghz: float,
    esm_sensitivity_dbm: float,
    max_range_km: float,
    threat_mode: str,
    n_samples: int = 500,
    seed: int = 42,
) -> dict:
    rng = np.random.default_rng(seed)
    mode_penalty = THREAT_MODES[threat_mode]

    # 1-sigma uncertainty: ±3 dB ERP, ±2 dB radar, ±3 dBsm RCS
    j_erp = jammer_erp_dbw + rng.normal(0, 1.5, n_samples)
    r_erp = radar_erp_dbw + rng.normal(0, 1.0, n_samples)
    rcs = rcs_dbsm + rng.normal(0, 1.5, n_samples)

    # Burn-through distribution
    exponents = (r_erp - j_erp - mode_penalty + rcs - 10 * np.log10(4 * np.pi)) / 20
    bt_km = (10 ** exponents) / 1e3

    # J/S curve ensemble
    ranges_km = np.linspace(1, max_range_km, 500)
    ranges_m = ranges_km * 1e3
    js_matrix = (
        j_erp[:, None] + mode_penalty - r_erp[:, None]
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(ranges_m)[None, :]
        - rcs[:, None]
    )

    return {
        "ranges_km": ranges_km,
        "js_p10": np.percentile(js_matrix, 10, axis=0),
        "js_p50": np.percentile(js_matrix, 50, axis=0),
        "js_p90": np.percentile(js_matrix, 90, axis=0),
        "bt_p10": float(np.percentile(bt_km, 10)),
        "bt_p50": float(np.percentile(bt_km, 50)),
        "bt_p90": float(np.percentile(bt_km, 90)),
    }


def _make_js_figure(result: dict, mc_result: dict | None, max_range_km: float) -> go.Figure:
    fig = go.Figure()

    if mc_result:
        r = mc_result["ranges_km"]
        fig.add_trace(go.Scatter(
            x=np.concatenate([r, r[::-1]]),
            y=np.concatenate([mc_result["js_p90"], mc_result["js_p10"][::-1]]),
            fill="toself",
            fillcolor="rgba(57, 211, 83, 0.10)",
            line=dict(color="rgba(0,0,0,0)"),
            name="P10–P90 uncertainty band",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=r, y=mc_result["js_p50"],
            mode="lines", name="J/S P50 (MC)",
            line=dict(color="#39d353", width=1.5, dash="dot"),
        ))

    fig.add_trace(go.Scatter(
        x=result["ranges_km"], y=result["js_db"],
        mode="lines", name="J/S (nominal)",
        line=dict(color="#39d353", width=2),
    ))

    shapes, annotations = [], []
    js_min, js_max = float(result["js_db"].min()), float(result["js_db"].max())

    if result["burn_through_km"]:
        bt = result["burn_through_km"]
        shapes.append(dict(type="line", x0=bt, x1=bt, y0=js_min, y1=js_max,
                           line=dict(color="#e3b341", dash="dash", width=1.5)))
        annotations.append(dict(x=bt, y=js_max * 0.9, text="Burn-through",
                                 showarrow=False,
                                 font=dict(color="#e3b341", family="Courier New", size=11)))

    if result["esm_detection_km"]:
        esm = result["esm_detection_km"]
        shapes.append(dict(type="line", x0=esm, x1=esm, y0=js_min, y1=js_max,
                           line=dict(color="#f85149", dash="dash", width=1.5)))
        annotations.append(dict(x=esm, y=js_max * 0.75, text="ESM detection",
                                 showarrow=False,
                                 font=dict(color="#f85149", family="Courier New", size=11)))

    shapes.append(dict(type="line", x0=1, x1=max_range_km, y0=0, y1=0,
                       line=dict(color="#8b949e", dash="dot", width=1)))

    fig.update_layout(
        title=dict(text="Signal Environment — J/S vs Range (self-screening jammer)",
                   font=dict(color="#c9d1d9", family="Courier New")),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        xaxis=dict(title="Range (km)", gridcolor="#21262d", zerolinecolor="#21262d"),
        yaxis=dict(title="J/S (dB)", gridcolor="#21262d", zerolinecolor="#30363d"),
        shapes=shapes, annotations=annotations,
        legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
        margin=dict(l=60, r=20, t=60, b=60),
    )
    return fig


def _generate_brief(params: dict, result: dict, mc_result: dict | None) -> str:
    date = datetime.date.today().isoformat()
    bt = result["burn_through_km_raw"]
    esm = result["esm_detection_km_raw"]
    lines = [
        "# EW Engagement Brief — Signal Environment Analysis",
        f"**Generated:** {date}  |  **Classification:** IKKE-KLASSIFICERET",
        "",
        "## Scenario Parameters",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Jammer ERP | {params['jammer_erp_dbw']} dBW |",
        f"| Radar ERP | {params['radar_erp_dbw']} dBW |",
        f"| Target RCS | {params['rcs_dbsm']} dBsm |",
        f"| Radar frequency | {params['radar_freq_ghz']} GHz |",
        f"| ESM sensitivity | {params['esm_sensitivity_dbm']} dBm |",
        f"| Jamming mode | {params['threat_mode']} |",
        f"| Max range modelled | {params['max_range_km']} km |",
        "",
        "## Key Results",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Burn-through range (nominal) | {bt:.3f} km |",
        f"| ESM detection range | {esm:.1f} km |",
    ]
    if mc_result:
        lines += [
            f"| Burn-through P10 (pessimistic) | {mc_result['bt_p10']:.1f} km |",
            f"| Burn-through P50 (median MC) | {mc_result['bt_p50']:.1f} km |",
            f"| Burn-through P90 (optimistic) | {mc_result['bt_p90']:.1f} km |",
        ]
    lines += [
        "",
        "## Acquisition Relevance",
        "- Burn-through range defines the minimum engagement range at which the radar "
        "can track the target through jamming. Below this range the jammer is ineffective.",
        "- ESM detection range defines when the threat platform detects the jammer emission — "
        "creating a geolocation and targeting opportunity against the jamming platform.",
        "- The P10–P90 uncertainty band reflects realistic ±3 dB ERP and ±3 dBsm RCS "
        "uncertainty. Vendor datasheets report single-point figures only. Acquisition "
        "requirements must be written against the pessimistic (P10) case.",
        "- Low-signature platforms (F-35A, −15 dBsm) require significantly less jammer ERP "
        "to achieve the same burn-through range compared to legacy aircraft.",
        "",
        "## Recommended Next Steps",
        "1. Validate ERP and RCS assumptions against FE threat assessment.",
        "2. Feed burn-through range into kravspecifikation draft as minimum ERP requirement.",
        "3. Cross-check ESM detection range against platform EMCON plan.",
    ]
    return "\n".join(lines)


_CONFIDENCE = {
    "tier": "Medium",
    "basis": "Open-source physics model (Nathanson/Barton). Unclassified parameters.",
    "what_changes": (
        "Access to classified threat ERP and RCS data from FE would move to High confidence. "
        "Hardware-in-the-loop validation against real emitter would confirm model assumptions."
    ),
}


def _render_confidence():
    tier_color = {"High": "#39d353", "Medium": "#e3b341", "Low": "#f85149"}
    t = _CONFIDENCE["tier"]
    st.markdown(
        f"<div style='border-left: 3px solid {tier_color[t]}; padding: 6px 12px; margin-top: 8px;'>"
        f"<small><b style='color:{tier_color[t]}'>ANALYTIC CONFIDENCE: {t.upper()}</b><br>"
        f"{_CONFIDENCE['basis']}<br>"
        f"<i>What would change it:</i> {_CONFIDENCE['what_changes']}</small>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render():
    briefing = st.session_state.get("briefing_mode", False)
    st.header("Signal Environment Simulator")

    if briefing:
        # Briefing mode: restore last known params from session or use defaults
        p = st.session_state.get("sim_params", {})
        jammer_erp = p.get("jammer_erp_dbw", 20)
        radar_erp = p.get("radar_erp_dbw", 50)
        rcs_dbsm = p.get("rcs_dbsm", -15.0)
        radar_freq = p.get("radar_freq_ghz", 10)
        esm_sensitivity = p.get("esm_sensitivity_dbm", -70)
        max_range = p.get("max_range_km", 150)
        threat_mode = p.get("threat_mode", "Spot")
        show_mc = True

        result = compute_js(jammer_erp, radar_erp, rcs_dbsm, radar_freq,
                            esm_sensitivity, max_range, threat_mode)
        mc_result = compute_monte_carlo(jammer_erp, radar_erp, rcs_dbsm, radar_freq,
                                        esm_sensitivity, max_range, threat_mode)

        st.plotly_chart(_make_js_figure(result, mc_result, max_range), use_container_width=True)
        bt = result["burn_through_km_raw"]
        esm_d = result["esm_detection_km_raw"]
        bt_label = f"{bt:.1f} km" if bt >= 0.5 else "Effective at all ranges"
        m1, m2, m3 = st.columns(3)
        m1.metric("Burn-through range", bt_label)
        m2.metric("ESM detection range", f"{esm_d:.1f} km" if esm_d < max_range else f">{max_range} km")
        m3.metric("J/S at max range", f"{result['js_db'][-1]:.1f} dB")
        if mc_result:
            st.caption(
                f"MC burn-through — P10: {mc_result['bt_p10']:.1f} km · "
                f"P50: {mc_result['bt_p50']:.1f} km · "
                f"P90: {mc_result['bt_p90']:.1f} km"
            )
        _render_confidence()
        return

    col_ctrl, col_chart = st.columns([1, 2])

    with col_ctrl:
        st.markdown("**Platform & Radar**")
        rcs_choice = st.selectbox("Target RCS preset", list(RCS_PRESETS.keys()), index=0)
        rcs_dbsm = (
            float(RCS_PRESETS[rcs_choice])
            if RCS_PRESETS[rcs_choice] is not None
            else st.slider("Target RCS (dBsm)", min_value=-30, max_value=40, value=5, step=1)
        )
        if RCS_PRESETS[rcs_choice] is not None:
            st.caption(f"RCS = {rcs_dbsm} dBsm")

        radar_erp = st.slider("Radar ERP (dBW)", min_value=20, max_value=80, value=50, step=1)
        radar_freq = st.slider("Radar frequency (GHz)", min_value=1, max_value=18, value=10, step=1)

        st.markdown("**Jammer**")
        jammer_erp = st.slider("Jammer ERP (dBW)", min_value=-10, max_value=60, value=20, step=1)
        threat_mode = st.selectbox("Jamming mode", list(THREAT_MODES.keys()), index=1)
        st.caption({
            "Barrage": "Barrage: −10 dB bandwidth penalty, harder for ESM to classify",
            "Spot": "Spot: maximum J/S, concentrated on radar frequency",
            "Sweep": "Sweep: −5 dB penalty, sweeps across band",
        }[threat_mode])

        st.markdown("**ESM & Range**")
        esm_sensitivity = st.slider("ESM sensitivity (dBm)", min_value=-100, max_value=-40,
                                    value=-70, step=1)
        max_range = st.slider("Max range (km)", min_value=10, max_value=500, value=150, step=10)
        show_mc = st.checkbox("Monte Carlo uncertainty bands (N=500)", value=True)

    result = compute_js(jammer_erp, radar_erp, rcs_dbsm, radar_freq,
                        esm_sensitivity, max_range, threat_mode)
    mc_result = (
        compute_monte_carlo(jammer_erp, radar_erp, rcs_dbsm, radar_freq,
                            esm_sensitivity, max_range, threat_mode)
        if show_mc else None
    )

    with col_chart:
        st.plotly_chart(_make_js_figure(result, mc_result, max_range), use_container_width=True)

        m1, m2, m3 = st.columns(3)
        bt = result["burn_through_km_raw"]
        esm_d = result["esm_detection_km_raw"]
        bt_label = f"{bt:.1f}" if bt >= 0.5 else "< 0.5 km (all-range)"
        m1.metric("Burn-through (km)", bt_label,
                  help="Range below which the radar tracks through jamming. "
                       "< 0.5 km = jammer effective at all practical ranges.")
        m2.metric("ESM detection (km)",
                  f"{esm_d:.1f}" if esm_d < max_range else f">{max_range} km")
        m3.metric("J/S at max range (dB)", f"{result['js_db'][-1]:.1f}")

        if show_mc and mc_result:
            st.caption(
                f"MC burn-through — P10: {mc_result['bt_p10']:.1f} km · "
                f"P50: {mc_result['bt_p50']:.1f} km · "
                f"P90: {mc_result['bt_p90']:.1f} km"
            )

        params = dict(
            jammer_erp_dbw=jammer_erp, radar_erp_dbw=radar_erp, rcs_dbsm=rcs_dbsm,
            radar_freq_ghz=radar_freq, esm_sensitivity_dbm=esm_sensitivity,
            max_range_km=max_range, threat_mode=threat_mode,
        )
        st.session_state["sim_params"] = params
        _render_confidence()
        brief_md = _generate_brief(params, result, mc_result)
        st.download_button(
            "Download decision brief (.md)",
            data=brief_md,
            file_name=f"ew_brief_{datetime.date.today().isoformat()}.md",
            mime="text/markdown",
        )
