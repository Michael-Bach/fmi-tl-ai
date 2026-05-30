import numpy as np
import plotly.graph_objects as go
import streamlit as st

THREAT_MODES = ["Barrage", "Spot", "Sweep"]

SPEED_OF_LIGHT = 3e8
THREAT_GAIN_DB = {"Barrage": 0, "Spot": 6, "Sweep": 3}


@st.cache_data
def compute_js_curve(jammer_erp_dbw: float, radar_freq_ghz: float, max_range_km: float, threat_mode: str):
    freq_hz = radar_freq_ghz * 1e9
    wavelength = SPEED_OF_LIGHT / freq_hz
    ranges_km = np.linspace(10, max_range_km, 500)
    ranges_m = ranges_km * 1e3

    # Free-space path loss (dB) = 20*log10(4*pi*R/lambda)
    fspl_db = 20 * np.log10(4 * np.pi * ranges_m / wavelength)

    # Received jammer power (dBm) = ERP(dBW) - FSPL + 30 (dBW→dBm) + mode gain
    mode_gain = THREAT_GAIN_DB[threat_mode]
    received_jammer_dbm = jammer_erp_dbw - fspl_db + 30 + mode_gain

    # J/S (dB): simplified — radar self-protection model where signal ~ -FSPL (one-way)
    # J/S = jammer ERP advantage over radar signal return (two-way FSPL difference)
    radar_signal_db = -2 * fspl_db  # two-way path for radar return (relative)
    jammer_signal_db = jammer_erp_dbw - fspl_db  # one-way jammer path
    js_db = jammer_signal_db - (jammer_erp_dbw + radar_signal_db - jammer_signal_db)

    # Practical J/S: jammer one-way path loss vs radar two-way; normalise at reference range
    ref_range_m = ranges_m[0]
    fspl_ref = 20 * np.log10(4 * np.pi * ref_range_m / wavelength)
    js_db = (jammer_erp_dbw - fspl_db + mode_gain) - (jammer_erp_dbw - 2 * fspl_db)
    js_db = fspl_db - mode_gain  # J/S decreases with range: closer = stronger jammer

    # Conventional model: J/S(dB) = EIRP_J - EIRP_R + G_R - FSPL_one_way + FSPL_two_way - other terms
    # Simplified to: J/S(R) = K - 20*log10(R), where K is set by sliders
    K = jammer_erp_dbw + mode_gain + 40  # arbitrary normalisation constant
    js_db = K - 20 * np.log10(ranges_m)

    # Burn-through range: J/S = 0 dB
    burn_through_km = None
    crossings = np.where(np.diff(np.sign(js_db)))[0]
    if len(crossings) > 0:
        idx = crossings[0]
        r0, r1 = ranges_km[idx], ranges_km[idx + 1]
        j0, j1 = js_db[idx], js_db[idx + 1]
        burn_through_km = r0 + (r1 - r0) * (-j0) / (j1 - j0)
    else:
        burn_through_km = max_range_km if js_db[-1] < 0 else None

    # ESM detection range: received jammer power exceeds ESM sensitivity
    esm_detection_km = None
    return ranges_km, js_db, received_jammer_dbm, burn_through_km, esm_detection_km


@st.cache_data
def compute_esm_range(jammer_erp_dbw: float, radar_freq_ghz: float, esm_sensitivity_dbm: float,
                      max_range_km: float, threat_mode: str):
    freq_hz = radar_freq_ghz * 1e9
    wavelength = SPEED_OF_LIGHT / freq_hz
    ranges_km = np.linspace(10, max_range_km, 500)
    ranges_m = ranges_km * 1e3
    mode_gain = THREAT_GAIN_DB[threat_mode]
    fspl_db = 20 * np.log10(4 * np.pi * ranges_m / wavelength)
    received_jammer_dbm = jammer_erp_dbw - fspl_db + 30 + mode_gain

    esm_detection_km = None
    crossings = np.where(np.diff(np.sign(received_jammer_dbm - esm_sensitivity_dbm)))[0]
    if len(crossings) > 0:
        idx = crossings[0]
        r0, r1 = ranges_km[idx], ranges_km[idx + 1]
        p0 = received_jammer_dbm[idx] - esm_sensitivity_dbm
        p1 = received_jammer_dbm[idx + 1] - esm_sensitivity_dbm
        esm_detection_km = r0 + (r1 - r0) * (-p0) / (p1 - p0)

    return esm_detection_km


def render():
    st.header("Signal Environment Simulator")

    col_ctrl, col_chart = st.columns([1, 2])

    with col_ctrl:
        st.markdown("**Parameters**")
        jammer_erp = st.slider("Jammer ERP (dBW)", min_value=-10, max_value=60, value=20, step=1)
        radar_freq = st.slider("Radar frequency (GHz)", min_value=1, max_value=18, value=10, step=1)
        esm_sensitivity = st.slider("ESM sensitivity (dBm)", min_value=-100, max_value=-40, value=-70, step=1)
        max_range = st.slider("Max range (km)", min_value=10, max_value=500, value=150, step=10)
        threat_mode = st.selectbox("Threat mode", options=THREAT_MODES, index=0)

    ranges_km, js_db, _, burn_through_km, _ = compute_js_curve(
        jammer_erp, radar_freq, max_range, threat_mode
    )
    esm_detection_km = compute_esm_range(jammer_erp, radar_freq, esm_sensitivity, max_range, threat_mode)

    js_at_max = float(js_db[-1])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=ranges_km,
        y=js_db,
        mode="lines",
        name="J/S (dB)",
        line=dict(color="#39d353", width=2),
    ))

    shapes = []
    annotations = []

    if burn_through_km is not None and 10 <= burn_through_km <= max_range:
        shapes.append(dict(
            type="line", x0=burn_through_km, x1=burn_through_km,
            y0=min(js_db), y1=max(js_db),
            line=dict(color="#e3b341", dash="dash", width=1.5),
        ))
        annotations.append(dict(
            x=burn_through_km, y=max(js_db) * 0.9,
            text="Burn-through", showarrow=False,
            font=dict(color="#e3b341", family="Courier New", size=11),
        ))

    if esm_detection_km is not None and 10 <= esm_detection_km <= max_range:
        shapes.append(dict(
            type="line", x0=esm_detection_km, x1=esm_detection_km,
            y0=min(js_db), y1=max(js_db),
            line=dict(color="#f85149", dash="dash", width=1.5),
        ))
        annotations.append(dict(
            x=esm_detection_km, y=max(js_db) * 0.75,
            text="ESM detection", showarrow=False,
            font=dict(color="#f85149", family="Courier New", size=11),
        ))

    fig.update_layout(
        title=dict(text="Signal Environment — J/S vs Range", font=dict(color="#c9d1d9", family="Courier New")),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        xaxis=dict(
            title="Range (km)",
            gridcolor="#21262d",
            zerolinecolor="#21262d",
        ),
        yaxis=dict(
            title="J/S (dB)",
            gridcolor="#21262d",
            zerolinecolor="#30363d",
            zerolinewidth=1,
        ),
        shapes=shapes,
        annotations=annotations,
        legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
        margin=dict(l=60, r=20, t=60, b=60),
    )

    with col_chart:
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Burn-through range (km)", f"{burn_through_km:.1f}" if burn_through_km else "Beyond range")
        m2.metric("ESM detection range (km)", f"{esm_detection_km:.1f}" if esm_detection_km else "Beyond range")
        m3.metric("J/S at max range (dB)", f"{js_at_max:.1f}")
