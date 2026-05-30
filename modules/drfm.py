"""
DRFM (Digital Radio Frequency Memory) deception jamming simulation.

Three jamming techniques: RGPO (range gate pull-off), VGPO (velocity gate
pull-off), FTG (false target generation / range-Doppler flooding).
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)


@st.cache_data
def simulate_rgpo(
    true_range_km: float,
    gate_width_km: float,
    ramp_rate_km_s: float,
    jsr_db: float,
    t_total_s: float = 10.0,
    dt_s: float = 0.05,
) -> dict:
    t = np.arange(0, t_total_s, dt_s)
    n = len(t)
    jsr = 10 ** (jsr_db / 10)
    drfm_sep = np.minimum(ramp_rate_km_s * t, 30.0)
    tracker = np.zeros(n)
    tracker[0] = true_range_km
    tau = 0.3  # range tracker time constant (s)
    gate_break_idx = None

    for i in range(1, n):
        sep = drfm_sep[i]
        in_gate = sep < gate_width_km
        if in_gate:
            # Power centroid: skin echo (weight=1 at 0) + DRFM (weight=JSR at sep)
            centroid_offset = (jsr * sep) / (1 + jsr)
        else:
            if jsr > 1.0 and tracker[i - 1] > true_range_km + gate_width_km * 0.4:
                centroid_offset = sep     # tracker already pulled, follows DRFM
            else:
                centroid_offset = 0.0    # tracker snaps back to skin echo
        target_r = true_range_km + centroid_offset
        tracker[i] = tracker[i - 1] + (target_r - tracker[i - 1]) * dt_s / tau
        if gate_break_idx is None and abs(tracker[i] - true_range_km) > gate_width_km * 0.8:
            gate_break_idx = i

    error = tracker - true_range_km
    return {
        "t": t,
        "true_range": np.full(n, true_range_km),
        "drfm_range": true_range_km + drfm_sep,
        "tracker": tracker,
        "error": error,
        "break_time": float(t[gate_break_idx]) if gate_break_idx else None,
        "break_error": float(error[gate_break_idx]) if gate_break_idx else None,
    }


@st.cache_data
def simulate_vgpo(
    true_vel_ms: float,
    gate_ms: float,
    ramp_ms_s: float,
    jsr_db: float,
    t_total_s: float = 8.0,
    dt_s: float = 0.05,
) -> dict:
    t = np.arange(0, t_total_s, dt_s)
    n = len(t)
    jsr = 10 ** (jsr_db / 10)
    drfm_sep = np.minimum(ramp_ms_s * t, 300.0)
    tracker = np.zeros(n)
    tracker[0] = true_vel_ms
    tau = 0.4
    break_idx = None

    for i in range(1, n):
        sep = drfm_sep[i]
        in_gate = sep < gate_ms
        if in_gate:
            centroid = (jsr * sep) / (1 + jsr)
        else:
            if jsr > 1.0 and tracker[i - 1] > true_vel_ms + gate_ms * 0.4:
                centroid = sep
            else:
                centroid = 0.0
        target_v = true_vel_ms + centroid
        tracker[i] = tracker[i - 1] + (target_v - tracker[i - 1]) * dt_s / tau
        if break_idx is None and abs(tracker[i] - true_vel_ms) > gate_ms * 0.8:
            break_idx = i

    return {
        "t": t,
        "true_vel": np.full(n, true_vel_ms),
        "drfm_vel": true_vel_ms + drfm_sep,
        "tracker": tracker,
        "break_time": float(t[break_idx]) if break_idx else None,
    }


@st.cache_data
def simulate_ftg(
    true_range_km: float,
    true_vel_ms: float,
    n_false: int,
    range_spread_km: float,
    vel_spread_ms: float,
    jsr_total_db: float,
    radar_freq_ghz: float,
    seed: int,
) -> dict:
    rng = np.random.default_rng(seed)
    ft_ranges = true_range_km + rng.uniform(-range_spread_km, range_spread_km, n_false)
    ft_vels   = true_vel_ms   + rng.uniform(-vel_spread_ms,   vel_spread_ms,   n_false)
    jsr_each  = 10 ** ((jsr_total_db - 10 * np.log10(n_false)) / 10)

    n_r, n_v = 180, 180
    r_ax = np.linspace(true_range_km - range_spread_km * 2.2,
                        true_range_km + range_spread_km * 2.2, n_r)
    v_ax = np.linspace(max(0, true_vel_ms - vel_spread_ms * 2.2),
                        true_vel_ms + vel_spread_ms * 2.2, n_v)
    sigma_r = (r_ax[1] - r_ax[0]) * 2.5
    sigma_v = (v_ax[1] - v_ax[0]) * 2.5
    rd = np.zeros((n_v, n_r))

    def blob(r0, v0, pwr):
        return pwr * np.outer(
            np.exp(-0.5 * ((v_ax - v0) / sigma_v) ** 2),
            np.exp(-0.5 * ((r_ax - r0) / sigma_r) ** 2),
        )

    rd += blob(true_range_km, true_vel_ms, 1.0)   # skin echo
    for fr, fv in zip(ft_ranges, ft_vels):
        rd += blob(fr, fv, jsr_each)

    return {
        "r_ax": r_ax, "v_ax": v_ax,
        "rd_db": 20 * np.log10(np.maximum(rd, 1e-9)),
        "true_range": true_range_km, "true_vel": true_vel_ms,
        "ft_ranges": ft_ranges, "ft_vels": ft_vels,
        "jsr_each_db": float(jsr_total_db - 10 * np.log10(n_false)),
    }


def _render_rgpo():
    st.subheader("Range Gate Pull-Off (RGPO)")
    st.caption(
        "DRFM captures the radar pulse and replays it at a gradually increasing delay. "
        "The range tracker follows the power centroid of true + false target. "
        "If JSR ≥ 6 dB and ramp rate exceeds tracker bandwidth, lock breaks — "
        "the radar range solution becomes corrupted."
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        true_range = st.slider("True target range (km)", 10, 150, 50, 5)
        gate_w = st.slider("Range gate width (km)", 0.1, 5.0, 1.0, 0.1)
        ramp = st.slider("Ramp rate (km/s)", 0.1, 5.0, 0.5, 0.1,
                          help="Rate the DRFM walks the false target range outward.")
        jsr = st.slider("JSR (dB) — DRFM vs skin echo", -10, 30, 15, 1)
        t_total = st.slider("Simulation time (s)", 2.0, 20.0, 10.0, 1.0)

    res = simulate_rgpo(true_range, gate_w, ramp, jsr, t_total)
    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=res["t"], y=res["true_range"],
                                  mode="lines", name="True target",
                                  line=dict(color="#8b949e", dash="dot", width=1.5)))
        fig.add_trace(go.Scatter(x=res["t"], y=res["drfm_range"],
                                  mode="lines", name="DRFM false target",
                                  line=dict(color="#e3b341", dash="dash", width=1.5)))
        fig.add_trace(go.Scatter(x=res["t"], y=res["tracker"],
                                  mode="lines", name="Radar range tracker",
                                  line=dict(color="#39d353", width=2.5)))
        if res["break_time"]:
            fig.add_vline(x=res["break_time"],
                           line=dict(color="#f85149", dash="dash", width=1.5),
                           annotation_text=f"Gate break {res['break_time']:.1f}s",
                           annotation_font=dict(color="#f85149", family="Courier New", size=10))
        fig.add_hrect(y0=true_range - gate_w / 2, y1=true_range + gate_w / 2,
                       fillcolor="rgba(88,166,255,0.05)",
                       line=dict(color="#58a6ff", width=0.5, dash="dot"),
                       annotation_text="Gate", annotation_font=dict(size=9, color="#58a6ff"))
        fig.update_layout(title=dict(text="RGPO — Range Tracker Response",
                                      font=dict(color="#c9d1d9", family="Courier New")),
                           xaxis=dict(title="Time (s)", gridcolor="#21262d"),
                           yaxis=dict(title="Range (km)", gridcolor="#21262d"),
                           height=340, **_L)
        st.plotly_chart(fig, use_container_width=True)
        if res["break_time"]:
            c1, c2 = st.columns(2)
            c1.metric("Gate break time", f"{res['break_time']:.1f} s")
            c2.metric("Range error at break", f"{res['break_error']:.2f} km")
            st.success(
                f"Gate break at {res['break_time']:.1f}s. Tracker pulled "
                f"{res['break_error']:.2f} km from true target — "
                "weapon guidance range solution is now corrupted."
            )
        else:
            st.warning("Gate break not achieved. Increase JSR or ramp rate.")


def _render_vgpo():
    st.subheader("Velocity Gate Pull-Off (VGPO)")
    st.caption(
        "DRFM replays the captured pulse with a progressively increasing Doppler shift. "
        "The Doppler tracker follows the false velocity until break-lock — "
        "fuzing and intercept timing are then corrupted."
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        true_vel = st.slider("True target velocity (m/s)", 100, 800, 250, 25)
        gate_v = st.slider("Doppler gate (m/s)", 5, 100, 25, 5)
        ramp_v = st.slider("VGPO ramp rate (m/s per s)", 1, 100, 20, 5)
        jsr_v = st.slider("JSR (dB)", -10, 30, 12, 1, key="vgpo_jsr")

    res = simulate_vgpo(true_vel, gate_v, ramp_v, jsr_v)
    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=res["t"], y=res["true_vel"],
                                  mode="lines", name="True velocity",
                                  line=dict(color="#8b949e", dash="dot", width=1.5)))
        fig.add_trace(go.Scatter(x=res["t"], y=res["drfm_vel"],
                                  mode="lines", name="DRFM false velocity",
                                  line=dict(color="#e3b341", dash="dash", width=1.5)))
        fig.add_trace(go.Scatter(x=res["t"], y=res["tracker"],
                                  mode="lines", name="Radar Doppler tracker",
                                  line=dict(color="#39d353", width=2.5)))
        if res["break_time"]:
            fig.add_vline(x=res["break_time"],
                           line=dict(color="#f85149", dash="dash", width=1.5),
                           annotation_text=f"Break {res['break_time']:.1f}s",
                           annotation_font=dict(color="#f85149", family="Courier New", size=10))
        fig.update_layout(title=dict(text="VGPO — Doppler Tracker Response",
                                      font=dict(color="#c9d1d9", family="Courier New")),
                           xaxis=dict(title="Time (s)", gridcolor="#21262d"),
                           yaxis=dict(title="Velocity (m/s)", gridcolor="#21262d"),
                           height=340, **_L)
        st.plotly_chart(fig, use_container_width=True)
        if res["break_time"]:
            st.success(
                f"Doppler tracker broken at {res['break_time']:.1f}s. "
                "Fire control system loses velocity solution — intercept geometry degraded."
            )
        else:
            st.warning("Tracker not broken. Increase JSR or ramp rate.")


def _render_ftg():
    st.subheader("False Target Generation (FTG)")
    st.caption(
        "DRFM replays the radar pulse N times with different delays and Doppler shifts. "
        "The range-Doppler display is flooded with ghost contacts at the same power level "
        "as the skin echo — saturating automatic target recognition."
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        n_ft = st.slider("False targets", 2, 20, 8, 1)
        tr_ftg = st.slider("True range (km)", 20, 150, 60, 5, key="ftg_r")
        tv_ftg = st.slider("True velocity (m/s)", 50, 600, 200, 25, key="ftg_v")
        r_spread = st.slider("Range spread ±(km)", 1.0, 30.0, 10.0, 1.0)
        v_spread = st.slider("Velocity spread ±(m/s)", 10, 200, 60, 10)
        jsr_ftg = st.slider("Total JSR (dB)", 0, 30, 15, 1, key="ftg_jsr")
        freq_ftg = st.slider("Radar frequency (GHz)", 1, 18, 10, 1, key="ftg_freq")
        seed = int(st.number_input("Seed", value=42, step=1, key="ftg_seed"))

    res = simulate_ftg(tr_ftg, tv_ftg, n_ft, r_spread, v_spread, jsr_ftg, freq_ftg, seed)
    with col_b:
        fig = go.Figure(data=go.Heatmap(
            z=res["rd_db"], x=res["r_ax"], y=res["v_ax"],
            colorscale=[[0, "#0d1117"], [0.4, "#196c2e"], [0.75, "#e3b341"], [1.0, "#f85149"]],
            colorbar=dict(title="dB", tickfont=dict(family="Courier New", color="#c9d1d9")),
        ))
        fig.add_trace(go.Scatter(
            x=[res["true_range"]], y=[res["true_vel"]], mode="markers", name="True target",
            marker=dict(color="#ffffff", size=12, symbol="cross", line=dict(color="#fff", width=2)),
        ))
        fig.update_layout(
            title=dict(text=f"Range-Doppler: True target + {n_ft} false contacts",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Range (km)", gridcolor="#21262d"),
            yaxis=dict(title="Velocity (m/s)", gridcolor="#21262d"),
            height=400, **_L,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info(
            f"True target (white cross) is one of {n_ft + 1} contacts with similar power. "
            f"JSR per false target: {res['jsr_each_db']:.1f} dB. "
            "ATR must use kinematic filtering or multi-look integration to separate real from false."
        )


def render():
    d1, d2, d3 = st.tabs(["📍 Range Gate Pull-Off", "〰 Velocity Gate Pull-Off", "👻 False Target Generation"])
    with d1: _render_rgpo()
    with d2: _render_vgpo()
    with d3: _render_ftg()
