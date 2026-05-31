"""
Sensor performance modelling — the "Sensor" in "EW og Sensor".

Tab 1: Radar detection performance
  - Radar Range Equation: detection range vs. target RCS
  - Probability of detection vs. SNR at fixed Pfa
  - ROC curve (Pd vs Pfa) at different SNR values

Tab 2: ESM / passive sensor performance
  - ESM intercept range vs. emitter ERP and frequency
  - Bearing accuracy vs. baseline length (interferometry)
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import ncx2 as _ncx2

def marcumq(m, a, b):
    """Marcum Q_m(a, b) via noncentral chi-squared CDF (scipy 1.x compatible)."""
    return float(1.0 - _ncx2.cdf(b ** 2, df=2 * m, nc=a ** 2))

SPEED_OF_LIGHT = 3e8


# ---------------------------------------------------------------------------
# Radar Range Equation (Swerling 0 / nonfluctuating target)
# ---------------------------------------------------------------------------

@st.cache_data
def compute_detection_range(
    pt_dbw: float,       # transmit power
    gt_db: float,        # transmit gain
    gr_db: float,        # receive gain
    freq_ghz: float,     # radar frequency
    rcs_range_dbsm: tuple,  # (min, max) RCS range for sweep
    noise_fig_db: float, # noise figure
    bandwidth_mhz: float,# receiver bandwidth
    pfa: float,          # false alarm probability
    pd_target: float,    # target Pd
) -> dict:
    wavelength = SPEED_OF_LIGHT / (freq_ghz * 1e9)
    T0 = 290  # standard noise temperature K
    k_boltzmann = 1.38e-23

    # Noise power: Pn = k*T0*B*NF
    nf_lin   = 10 ** (noise_fig_db / 10)
    bw_hz    = bandwidth_mhz * 1e6
    pn_w     = k_boltzmann * T0 * bw_hz * nf_lin
    pn_dbw   = 10 * np.log10(pn_w)

    # Detection threshold from Pfa (Swerling 0: threshold ~ -log(Pfa) × noise variance)
    # Neyman-Pearson: threshold_linear = -log(Pfa) × pn_w
    snr_min_db = _snr_for_pd(pd_target, pfa)

    rcs_dbsm_arr = np.linspace(rcs_range_dbsm[0], rcs_range_dbsm[1], 200)
    rcs_m2_arr   = 10 ** (rcs_dbsm_arr / 10)

    pt_w = 10 ** (pt_dbw / 10)
    gt   = 10 ** (gt_db / 10)
    gr   = 10 ** (gr_db / 10)

    # R_det: solve R^4 = Pt*Gt*Gr*λ²*σ / ((4π)³ * Pn * SNR_min)
    numerator   = pt_w * gt * gr * wavelength**2 * rcs_m2_arr
    denominator = (4 * np.pi)**3 * pn_w * (10 ** (snr_min_db / 10))
    r_det_m     = (numerator / denominator) ** 0.25
    r_det_km    = r_det_m / 1e3

    return {
        "rcs_dbsm":   rcs_dbsm_arr,
        "r_det_km":   r_det_km,
        "snr_min_db": snr_min_db,
        "pn_dbw":     pn_dbw,
    }


def _snr_for_pd(pd: float, pfa: float, tol: float = 1e-3) -> float:
    """Binary search for SNR (dB) achieving given Pd at given Pfa (Swerling 0)."""
    lo, hi = -10.0, 40.0
    for _ in range(40):
        mid_db = (lo + hi) / 2
        mid_lin = 10 ** (mid_db / 10)
        a = np.sqrt(2 * mid_lin)
        b = np.sqrt(-2 * np.log(pfa)) if pfa > 0 else 6.0
        pd_est = float(marcumq(1, a, b))
        if pd_est > pd:
            hi = mid_db
        else:
            lo = mid_db
    return (lo + hi) / 2


@st.cache_data
def compute_roc(snr_db_values: tuple, pfa_range: tuple) -> dict:
    """ROC curves for several SNR values."""
    pfas = np.logspace(pfa_range[0], pfa_range[1], 200)
    curves = {}
    for snr_db in snr_db_values:
        snr_lin = 10 ** (snr_db / 10)
        a = np.sqrt(2 * snr_lin)
        pds = np.array([
            float(marcumq(1, a, np.sqrt(-2 * np.log(max(pfa, 1e-12)))))
            for pfa in pfas
        ])
        curves[f"SNR = {snr_db} dB"] = pds
    return {"pfas": pfas, "curves": curves}


@st.cache_data
def compute_pd_vs_snr(pfa: float, snr_range: tuple) -> dict:
    snr_db = np.linspace(snr_range[0], snr_range[1], 200)
    snr_lin = 10 ** (snr_db / 10)
    b = np.sqrt(-2 * np.log(max(pfa, 1e-12)))
    pds = np.array([float(marcumq(1, np.sqrt(2 * s), b)) for s in snr_lin])
    return {"snr_db": snr_db, "pd": pds}


def _render_radar_tab():
    st.subheader("Radar Detection Performance — Radar Range Equation")
    st.caption(
        "Detection range vs. target RCS, ROC curve, and Pd vs. SNR. "
        "Swerling 0 (non-fluctuating target). Marcum Q-function based detection model."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown("**Radar parameters**")
        pt_dbw  = st.slider("Transmit power (dBW)", 10, 80, 50, 1)
        gt_db   = st.slider("Transmit gain (dB)", 20, 50, 35, 1)
        gr_db   = st.slider("Receive gain (dB)", 20, 50, 35, 1)
        freq    = st.slider("Frequency (GHz)", 1, 18, 10, 1)
        nf_db   = st.slider("Noise figure (dB)", 1, 15, 5, 1)
        bw_mhz  = st.slider("Bandwidth (MHz)", 0.1, 100.0, 1.0, 0.1)
        pfa     = st.select_slider("False alarm prob (Pfa)",
                                    options=[1e-8, 1e-7, 1e-6, 1e-5, 1e-4],
                                    value=1e-6)
        pd_tgt  = st.slider("Required Pd", 0.5, 0.99, 0.9, 0.01)

    res = compute_detection_range(
        pt_dbw, gt_db, gr_db, freq, (-20, 20), nf_db, bw_mhz, pfa, pd_tgt,
    )

    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=res["rcs_dbsm"], y=res["r_det_km"],
            mode="lines", line=dict(color="#39d353", width=2),
            name=f"Detection range (Pd={pd_tgt:.0%}, Pfa={pfa:.0e})",
        ))
        for rcs_label, rcs_val, color in [
            ("F-35A (−15 dBsm)", -15, "#58a6ff"),
            ("Legacy fighter (+5 dBsm)", 5, "#e3b341"),
            ("Large aircraft (+15 dBsm)", 15, "#f85149"),
        ]:
            r_at_rcs = float(np.interp(rcs_val, res["rcs_dbsm"], res["r_det_km"]))
            fig.add_vline(x=rcs_val, line=dict(color=color, dash="dot", width=1))
            fig.add_annotation(x=rcs_val, y=max(res["r_det_km"]) * 0.85,
                                text=f"{rcs_label}<br>{r_at_rcs:.0f} km",
                                showarrow=False,
                                font=dict(color=color, family="Courier New", size=9))
        fig.update_layout(
            title=dict(text="Detection Range vs. Target RCS",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Target RCS (dBsm)", gridcolor="#21262d"),
            yaxis=dict(title="Detection range (km)", gridcolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50), height=280,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ROC curves
        roc = compute_roc((-5, 0, 5, 10, 15), (-8, -1))
        fig_roc = go.Figure()
        colors = ["#8b949e", "#d2a8ff", "#e3b341", "#58a6ff", "#39d353"]
        for (label, pds), color in zip(roc["curves"].items(), colors):
            fig_roc.add_trace(go.Scatter(
                x=roc["pfas"], y=pds,
                mode="lines", name=label,
                line=dict(color=color, width=1.5),
            ))
        fig_roc.add_vline(x=pfa, line=dict(color="#f85149", dash="dot"),
                          annotation_text=f"Pfa={pfa:.0e}",
                          annotation_font=dict(color="#f85149", family="Courier New", size=9))
        fig_roc.update_layout(
            title=dict(text="ROC Curves — Pd vs Pfa (Swerling 0)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="False alarm probability (Pfa)", gridcolor="#21262d",
                       type="log"),
            yaxis=dict(title="Probability of detection (Pd)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d", font=dict(size=9)),
            margin=dict(l=60, r=20, t=50, b=50), height=240,
        )
        st.plotly_chart(fig_roc, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        r_f35 = float(np.interp(-15, res["rcs_dbsm"], res["r_det_km"]))
        r_leg = float(np.interp(5,   res["rcs_dbsm"], res["r_det_km"]))
        m1.metric("Detection range F-35A (km)", f"{r_f35:.0f}")
        m2.metric("Detection range legacy (km)", f"{r_leg:.0f}")
        m3.metric("Required SNR (dB)", f"{res['snr_min_db']:.1f}")


# ---------------------------------------------------------------------------
# ESM performance tab
# ---------------------------------------------------------------------------

@st.cache_data
def compute_esm_intercept(
    emitter_erp_dbw: float,
    freq_ghz: float,
    esm_sensitivity_dbm: float,
    max_range_km: float,
) -> dict:
    wavelength = SPEED_OF_LIGHT / (freq_ghz * 1e9)
    ranges_km = np.linspace(1, max_range_km, 400)
    ranges_m  = ranges_km * 1e3
    fspl_db   = 20 * np.log10(4 * np.pi * ranges_m / wavelength)
    rx_dbm    = emitter_erp_dbw - fspl_db + 30

    log_r = (emitter_erp_dbw + 30 - esm_sensitivity_dbm
             - 20 * np.log10(4 * np.pi / wavelength)) / 20
    intercept_km = (10 ** log_r) / 1e3

    return {
        "ranges_km":     ranges_km,
        "rx_dbm":        rx_dbm,
        "intercept_km":  float(intercept_km),
        "sensitivity":   esm_sensitivity_dbm,
    }


def _render_esm_tab():
    st.subheader("ESM / Passive Sensor — Intercept Performance")
    st.caption(
        "Received power at ESM receiver vs. range. "
        "Intercept range where received power crosses ESM sensitivity threshold."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        erp_dbw  = st.slider("Emitter ERP (dBW)", -10, 60, 30, 1, key="esm_erp")
        freq     = st.slider("Frequency (GHz)", 1, 18, 10, 1, key="esm_freq")
        sens_dbm = st.slider("ESM sensitivity (dBm)", -110, -40, -80, 2)
        max_r    = st.slider("Max range (km)", 10, 500, 200, 10, key="esm_mr")

    res = compute_esm_intercept(erp_dbw, freq, sens_dbm, max_r)

    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=res["ranges_km"], y=res["rx_dbm"],
            mode="lines", line=dict(color="#39d353", width=2),
            name="Received power (dBm)",
        ))
        fig.add_hline(y=sens_dbm, line=dict(color="#f85149", dash="dash"),
                      annotation_text=f"ESM sensitivity ({sens_dbm} dBm)",
                      annotation_font=dict(color="#f85149", family="Courier New", size=10))
        if 0 < res["intercept_km"] < max_r:
            fig.add_vline(x=res["intercept_km"],
                          line=dict(color="#e3b341", dash="dash", width=1.5),
                          annotation_text=f"Intercept {res['intercept_km']:.1f} km",
                          annotation_font=dict(color="#e3b341", family="Courier New", size=10))
        fig.update_layout(
            title=dict(text="ESM Received Power vs. Range",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Range (km)", gridcolor="#21262d"),
            yaxis=dict(title="Received power (dBm)", gridcolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50), height=300,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.metric("ESM intercept range (km)",
                  f"{res['intercept_km']:.1f}" if res["intercept_km"] < max_r else f">{max_r}")


def render():
    rt1, rt2 = st.tabs(["📡 Radar Detection", "👂 ESM Intercept"])
    with rt1:
        _render_radar_tab()
    with rt2:
        _render_esm_tab()
