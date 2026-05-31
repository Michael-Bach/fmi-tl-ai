"""
Multi-jammer cooperative gain + two-agent arms race.

Tab 1: Multi-jammer — compute J/S for two escort jammers with angular diversity.
  Shows combined J/S vs. single jammer with doubled ERP.
  The key acquisition question: one powerful jammer or two weaker ones?

Tab 2: Arms Race — two-agent Q-learning.
  Jammer agent: Barrage / Spot / Sweep.
  Radar agent: Normal scan / Frequency agile / LPRO (low probability of intercept).
  Show co-evolutionary reward dynamics over training rounds.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8
THREAT_MODES_NAMES   = ["Barrage", "Spot", "Sweep"]
THREAT_MODES_PENALTY = [-10, 0, -5]

RADAR_MODES_NAMES  = ["Normal", "Frequency agile", "LPRO"]
# Radar mode effect on jammer effectiveness: multiplier on effective J/S
# Frequency agile: defeats Spot jamming (-8 dB effective), Barrage less affected
# LPRO: spreads radar power → harder to detect but lower ERP effective (-3 dB)
RADAR_VS_JAMMER = np.array([
    # Normal  Freq-agile  LPRO
    [  0,      0,          3],   # Barrage (spread spectrum — less affected by FA)
    [  0,     -8,          3],   # Spot (crippled by frequency agile)
    [  0,     -4,          3],   # Sweep (intermediate)
])


# ---------------------------------------------------------------------------
# Tab 1: Multi-jammer cooperative gain
# ---------------------------------------------------------------------------

@st.cache_data
def compute_multijammer(
    strike_range_km: float,
    jammer1_erp_dbw: float,
    jammer1_offset_km: float,
    jammer1_angle_deg: float,
    jammer2_erp_dbw: float,
    jammer2_offset_km: float,
    jammer2_angle_deg: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
) -> dict:
    def jammer_range(strike_km, offset_km, angle_deg):
        angle = np.radians(angle_deg)
        jx = strike_km + offset_km * np.cos(angle)
        jy = offset_km * np.sin(angle)
        return float(np.sqrt(jx**2 + jy**2))

    R_t = strike_range_km * 1e3

    def js_single(erp, R_j_km):
        R_j = max(R_j_km * 1e3, 1e3)
        return (erp - radar_erp_dbw
                + 10 * np.log10(4 * np.pi)
                + 40 * np.log10(R_t)
                - 20 * np.log10(R_j)
                - rcs_dbsm)

    R_j1 = jammer_range(strike_range_km, jammer1_offset_km, jammer1_angle_deg)
    R_j2 = jammer_range(strike_range_km, jammer2_offset_km, jammer2_angle_deg)

    js1 = js_single(jammer1_erp_dbw, R_j1)
    js2 = js_single(jammer2_erp_dbw, R_j2)

    # Incoherent power combination (decorrelated jammers): P_total = P1 + P2
    # In dB: JS_combined = 10*log10(10^(JS1/10) + 10^(JS2/10))
    p1 = 10 ** (js1 / 10)
    p2 = 10 ** (js2 / 10)
    js_combined = float(10 * np.log10(p1 + p2))

    # Single jammer with doubled ERP (same offset as jammer 1)
    js_doubled = js_single(jammer1_erp_dbw + 3.0, R_j1)  # +3 dB = double power

    # Sweep over strike ranges
    ranges_km = np.linspace(20, 300, 300)
    js1_arr, js2_arr, jsc_arr, jsd_arr = [], [], [], []
    for r in ranges_km:
        R_t_r = r * 1e3
        def js_r(erp, R_j_km, R_t_r=R_t_r):
            R_j = max(R_j_km * 1e3, 1e3)
            return (erp - radar_erp_dbw
                    + 10 * np.log10(4 * np.pi)
                    + 40 * np.log10(R_t_r)
                    - 20 * np.log10(R_j)
                    - rcs_dbsm)
        j1 = js_r(jammer1_erp_dbw, R_j1)
        j2 = js_r(jammer2_erp_dbw, R_j2)
        jc = 10 * np.log10(10**(j1/10) + 10**(j2/10))
        jd = js_r(jammer1_erp_dbw + 3.0, R_j1)
        js1_arr.append(j1); js2_arr.append(j2); jsc_arr.append(jc); jsd_arr.append(jd)

    return {
        "js1": js1, "js2": js2, "js_combined": js_combined, "js_doubled": js_doubled,
        "ranges_km": ranges_km,
        "js1_arr": np.array(js1_arr), "js2_arr": np.array(js2_arr),
        "jsc_arr": np.array(jsc_arr), "jsd_arr": np.array(jsd_arr),
        "R_j1": R_j1, "R_j2": R_j2,
    }


def _render_multijammer():
    st.subheader("Multi-Jammer Cooperative Gain")
    st.caption(
        "Two escort jammers at different angular offsets. "
        "Incoherent power combination vs. single jammer with doubled ERP. "
        "Acquisition question: is angular diversity worth more than concentrating ERP on one platform?"
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        strike_range = st.slider("Strike range (km)", 50, 300, 120, 10)
        radar_erp    = st.slider("Radar ERP (dBW)", 20, 80, 55, 1)
        rcs_dbsm     = st.slider("Platform RCS (dBsm)", -20, 15, -15, 1)

        st.markdown("**Jammer 1**")
        j1_erp    = st.slider("Jammer 1 ERP (dBW)", -10, 60, 25, 1)
        j1_offset = st.slider("Jammer 1 offset (km)", 0, 100, 20, 5)
        j1_angle  = st.slider("Jammer 1 angle (°)", -90, 90, 0, 5,
                              help="0° = directly behind strike")

        st.markdown("**Jammer 2**")
        j2_erp    = st.slider("Jammer 2 ERP (dBW)", -10, 60, 25, 1, key="j2_erp")
        j2_offset = st.slider("Jammer 2 offset (km)", 0, 100, 25, 5, key="j2_off")
        j2_angle  = st.slider("Jammer 2 angle (°)", -90, 90, 45, 5, key="j2_ang",
                              help="Angular diversity from jammer 1")

    res = compute_multijammer(
        strike_range, j1_erp, j1_offset, j1_angle,
        j2_erp, j2_offset, j2_angle, radar_erp, rcs_dbsm,
    )

    with col_b:
        fig = go.Figure()
        for arr, name, color, dash in [
            (res["js1_arr"],  f"Jammer 1 alone", "#8b949e", "dot"),
            (res["js2_arr"],  f"Jammer 2 alone", "#58a6ff", "dot"),
            (res["jsd_arr"],  "Single jammer (+3 dB ERP, same offset)", "#e3b341", "dash"),
            (res["jsc_arr"],  "Two jammers combined (angular diversity)", "#39d353", "solid"),
        ]:
            fig.add_trace(go.Scatter(
                x=res["ranges_km"], y=arr,
                mode="lines", name=name,
                line=dict(color=color, dash=dash, width=2),
            ))
        fig.add_hline(y=0, line=dict(color="#8b949e", dash="dot", width=1))
        fig.update_layout(
            title=dict(text="J/S — Two Jammers vs Single (+3 dB ERP)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Strike range (km)", gridcolor="#21262d"),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d", font=dict(size=9)),
            margin=dict(l=60, r=20, t=60, b=50), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Jammer 1 alone (dB)", f"{res['js1']:.1f}")
        m2.metric("Jammer 2 alone (dB)", f"{res['js2']:.1f}")
        m3.metric("Two-jammer combined (dB)", f"{res['js_combined']:.1f}")
        gain_vs_double = res["js_combined"] - res["js_doubled"]
        m4.metric("vs doubled ERP (dB)", f"{gain_vs_double:+.1f}",
                  delta_color="normal" if gain_vs_double > 0 else "inverse")

        if gain_vs_double > 0:
            st.success(
                f"Two-jammer angular diversity outperforms doubling ERP on one platform "
                f"by **{gain_vs_double:.1f} dB** at this geometry. "
                f"Acquisition implication: two lower-ERP platforms may be more cost-effective "
                f"than one high-ERP platform.",
            )
        else:
            st.info(
                f"At this geometry, doubling ERP on one platform is "
                f"{-gain_vs_double:.1f} dB more effective. "
                f"Angular diversity advantage depends on offset angles — try wider separation.",
            )


# ---------------------------------------------------------------------------
# Tab 2: Arms Race
# ---------------------------------------------------------------------------

N_RANGE_BINS  = 8
N_JAM_ACTIONS = 3
N_RAD_ACTIONS = 3

_JAMMER_ERP, _RADAR_ERP, _RCS = 25.0, 55.0, 5.0
_WAVELENGTH = SPEED_OF_LIGHT / (10e9)


def _js_base(range_km: float) -> float:
    r = max(range_km * 1e3, 1e3)
    return float(_JAMMER_ERP - _RADAR_ERP + 10 * np.log10(4 * np.pi) + 20 * np.log10(r) - _RCS)


def _jam_reward(range_km: float, jam_action: int, rad_action: int) -> float:
    js = _js_base(range_km) + THREAT_MODES_PENALTY[jam_action] + RADAR_VS_JAMMER[jam_action, rad_action]
    # ESM detection penalty
    r = max(range_km * 1e3, 1e3)
    fspl = 20 * np.log10(4 * np.pi * r / _WAVELENGTH)
    esm = _JAMMER_ERP + THREAT_MODES_PENALTY[jam_action] - fspl + 30
    detected = esm > -70
    return (1.0 if js > 0 else -1.5) + (-0.4 if detected else 0)


def _rad_reward(range_km: float, jam_action: int, rad_action: int) -> float:
    js = _js_base(range_km) + THREAT_MODES_PENALTY[jam_action] + RADAR_VS_JAMMER[jam_action, rad_action]
    return 1.0 if js < 0 else -1.0


def _range_bin(r: float) -> int:
    return int(np.clip((r - 20) / 180 * N_RANGE_BINS, 0, N_RANGE_BINS - 1))


@st.cache_data
def train_arms_race(n_rounds: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    Qj = np.zeros((N_RANGE_BINS, N_JAM_ACTIONS))
    Qr = np.zeros((N_RANGE_BINS, N_RAD_ACTIONS))
    alpha, gamma = 0.15, 0.85

    jammer_rewards, radar_rewards = [], []

    for ep in range(n_rounds):
        eps = max(0.05, 1.0 - ep / n_rounds)
        range_km = float(rng.uniform(20, 200))
        s = _range_bin(range_km)
        total_j = total_r = 0.0

        for _ in range(20):
            ja = int(rng.integers(N_JAM_ACTIONS)) if rng.random() < eps else int(np.argmax(Qj[s]))
            ra = int(rng.integers(N_RAD_ACTIONS)) if rng.random() < eps else int(np.argmax(Qr[s]))

            rj = _jam_reward(range_km, ja, ra)
            rr = _rad_reward(range_km, ja, ra)
            total_j += rj; total_r += rr

            range_km = float(np.clip(range_km + rng.uniform(-20, 20), 20, 200))
            ns = _range_bin(range_km)
            Qj[s, ja] += alpha * (rj + gamma * np.max(Qj[ns]) - Qj[s, ja])
            Qr[s, ra] += alpha * (rr + gamma * np.max(Qr[ns]) - Qr[s, ra])
            s = ns

        jammer_rewards.append(total_j)
        radar_rewards.append(total_r)

    jammer_policy = [THREAT_MODES_NAMES[int(np.argmax(Qj[s]))] for s in range(N_RANGE_BINS)]
    radar_policy  = [RADAR_MODES_NAMES[int(np.argmax(Qr[s]))] for s in range(N_RANGE_BINS)]

    return {
        "jammer_rewards": jammer_rewards,
        "radar_rewards":  radar_rewards,
        "jammer_policy":  jammer_policy,
        "radar_policy":   radar_policy,
    }


def _render_arms_race():
    st.subheader("Arms Race — Two-Agent Co-Evolutionary Training")
    st.caption(
        "Jammer agent and radar agent both learn simultaneously. "
        "Radar has three modes: Normal / Frequency agile (defeats Spot jamming) / LPRO. "
        "Shows the co-evolutionary arms race dynamic — static rules break, learned policies adapt."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        n_rounds = st.slider("Training rounds", 500, 5000, 2000, 250)
        seed = int(st.number_input("Seed", value=7, step=1, key="ar_seed"))

        st.markdown("**Radar modes**")
        st.markdown("- Normal: no counter-measure")
        st.markdown("- Frequency agile: defeats Spot jamming (−8 dB effective)")
        st.markdown("- LPRO: lower ERP → harder to detect (+3 dB to jammer ESM advantage)")

        st.markdown("**Jammer modes**")
        for m, p in zip(THREAT_MODES_NAMES, THREAT_MODES_PENALTY):
            st.markdown(f"- {m}: {p:+d} dB bandwidth penalty")

    res = train_arms_race(n_rounds, seed)

    with col_b:
        window = max(1, n_rounds // 40)
        sm_j = np.convolve(res["jammer_rewards"], np.ones(window) / window, mode="valid")
        sm_r = np.convolve(res["radar_rewards"],  np.ones(window) / window, mode="valid")
        ep_x = list(range(len(sm_j)))

        fig_tr = go.Figure()
        fig_tr.add_trace(go.Scatter(x=ep_x, y=sm_j, mode="lines",
                                     name="Jammer reward",
                                     line=dict(color="#39d353", width=1.5)))
        fig_tr.add_trace(go.Scatter(x=ep_x, y=sm_r, mode="lines",
                                     name="Radar reward",
                                     line=dict(color="#f85149", width=1.5)))
        fig_tr.add_hline(y=0, line=dict(color="#8b949e", dash="dot", width=1))
        fig_tr.update_layout(
            title=dict(text="Arms Race Training Dynamics",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Episode", gridcolor="#21262d"),
            yaxis=dict(title="Total reward (smoothed)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=250,
        )
        st.plotly_chart(fig_tr, use_container_width=True)

        # Policy tables side by side
        range_labels = [f"{int(20 + i * 22)} km" for i in range(N_RANGE_BINS)]
        col_j, col_r = st.columns(2)
        with col_j:
            st.markdown("**Jammer learned policy**")
            for lbl, mode in zip(range_labels, res["jammer_policy"]):
                icon = {"Barrage": "🟡", "Spot": "🔵", "Sweep": "🟣"}[mode]
                st.markdown(f"`{lbl}` → {icon} {mode}")

        with col_r:
            st.markdown("**Radar learned counter-policy**")
            for lbl, mode in zip(range_labels, res["radar_policy"]):
                icon = {"Normal": "⚪", "Frequency agile": "🟠", "LPRO": "🔴"}[mode]
                st.markdown(f"`{lbl}` → {icon} {mode}")

        final_j = float(np.mean(res["jammer_rewards"][-100:]))
        final_r = float(np.mean(res["radar_rewards"][-100:]))
        m1, m2 = st.columns(2)
        m1.metric("Jammer final avg reward (last 100)", f"{final_j:.1f}")
        m2.metric("Radar final avg reward (last 100)",  f"{final_r:.1f}")

        spot_count = res["jammer_policy"].count("Spot")
        if spot_count < N_RANGE_BINS // 2:
            st.info(
                "Jammer has learned to reduce Spot usage — "
                "the radar's frequency-agile counter-policy makes Spot less effective. "
                "This is the arms race dynamic: static rules (always Spot for maximum J/S) "
                "become exploitable; learned adaptive policy survives.",
            )


def render():
    at1, at2 = st.tabs(["🔊 Multi-Jammer", "⚔️ Arms Race"])
    with at1:
        _render_multijammer()
    with at2:
        _render_arms_race()
