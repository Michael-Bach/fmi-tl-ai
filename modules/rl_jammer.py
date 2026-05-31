import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

MODE_NAMES = ["Barrage", "Spot", "Sweep"]
# (bandwidth_penalty_db, esm_detectability_offset_db)
# Barrage: low J/S, harder for ESM to classify/geolocate (spread spectrum)
# Spot:    max J/S, easy ESM intercept (narrowband, predictable)
# Sweep:   intermediate on both axes
MODE_ATTRS = [(-10, +3), (0, -3), (-5, 0)]

N_RANGE_BINS = 12
N_ACTIONS = 3

# Fixed environment parameters
_RADAR_ERP = 50.0
_JAMMER_ERP = 25.0
_RCS_DBSM = 5.0
_ESM_SENSITIVITY = -70.0
_RADAR_FREQ_GHZ = 10.0
_WAVELENGTH = SPEED_OF_LIGHT / (_RADAR_FREQ_GHZ * 1e9)


def _js_db(range_km: float, mode_idx: int) -> float:
    penalty, _ = MODE_ATTRS[mode_idx]
    r_m = max(range_km * 1e3, 1e3)
    return float(
        _JAMMER_ERP + penalty - _RADAR_ERP
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(r_m)
        - _RCS_DBSM
    )


def _esm_received_dbm(range_km: float, mode_idx: int) -> float:
    _, detect_offset = MODE_ATTRS[mode_idx]
    r_m = max(range_km * 1e3, 1e3)
    fspl = 20 * np.log10(4 * np.pi * r_m / _WAVELENGTH)
    return float(_JAMMER_ERP + detect_offset - fspl + 30)


def _range_to_state(range_km: float) -> int:
    return int(np.clip((range_km - 20) / 180 * N_RANGE_BINS, 0, N_RANGE_BINS - 1))


def _reward(range_km: float, mode_idx: int) -> float:
    js = _js_db(range_km, mode_idx)
    esm_p = _esm_received_dbm(range_km, mode_idx)
    r = 1.0 if js > 0 else -1.5   # jamming effectiveness
    if esm_p > _ESM_SENSITIVITY:
        r -= 0.4               # penalty for being detectable
    return r


@st.cache_data
def train_agent(n_episodes: int, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    Q = np.zeros((N_RANGE_BINS, N_ACTIONS))
    alpha, gamma = 0.15, 0.90
    eps_start, eps_end = 1.0, 0.05
    episode_rewards = []

    for ep in range(n_episodes):
        eps = eps_start + (eps_end - eps_start) * ep / n_episodes
        range_km = float(rng.uniform(20, 200))
        state = _range_to_state(range_km)
        total = 0.0

        for _ in range(25):
            action = (
                int(rng.integers(N_ACTIONS))
                if rng.random() < eps
                else int(np.argmax(Q[state]))
            )
            r = _reward(range_km, action)
            total += r
            range_km = float(np.clip(range_km + rng.uniform(-20, 20), 20, 200))
            ns = _range_to_state(range_km)
            Q[state, action] += alpha * (r + gamma * np.max(Q[ns]) - Q[state, action])
            state = ns

        episode_rewards.append(total)

    return Q, episode_rewards


def render():
    st.header("RL Adaptive Jammer — Learned Mode Selection Policy")
    st.caption(
        "Q-learning agent trained to select Barrage / Spot / Sweep based on range. "
        "Trade-off: Spot maximises J/S but increases ESM detectability; "
        "Barrage reduces jamming effectiveness but degrades ESM intercept quality. "
        "The agent learns the policy without explicit rules."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        n_episodes = st.slider("Training episodes", 500, 5000, 2000, 250)
        seed = int(st.number_input("Seed", value=42, step=1))
        st.divider()
        st.markdown("**Environment (fixed)**")
        st.markdown(f"- Radar ERP: {_RADAR_ERP} dBW")
        st.markdown(f"- Jammer ERP: {_JAMMER_ERP} dBW")
        st.markdown(f"- Target RCS: {_RCS_DBSM} dBsm")
        st.markdown(f"- ESM sensitivity: {_ESM_SENSITIVITY} dBm")
        st.markdown(f"- Radar freq: {_RADAR_FREQ_GHZ} GHz")
        st.divider()
        st.markdown("**Reward structure**")
        st.markdown("- J/S > 0 dB: +1.0")
        st.markdown("- J/S < 0 dB: −1.5 (burned through)")
        st.markdown("- ESM detects jammer: −0.4")

    Q, rewards = train_agent(n_episodes, seed)

    with col_b:
        # Training curve (smoothed)
        window = max(1, n_episodes // 40)
        smoothed = np.convolve(rewards, np.ones(window) / window, mode="valid")
        fig_train = go.Figure()
        fig_train.add_trace(go.Scatter(
            x=list(range(len(smoothed))), y=smoothed,
            mode="lines", line=dict(color="#39d353", width=1.5),
            name="Smoothed episode reward",
        ))
        fig_train.update_layout(
            title=dict(text="Training Curve",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Episode", gridcolor="#21262d"),
            yaxis=dict(title="Total reward (smoothed)", gridcolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=200,
        )
        st.plotly_chart(fig_train, use_container_width=True)

        # Q-value heatmap
        range_labels = [f"{int(20 + i * 15)} km" for i in range(N_RANGE_BINS)]
        fig_q = go.Figure(data=go.Heatmap(
            z=Q.T,
            x=range_labels,
            y=MODE_NAMES,
            colorscale=[[0.0, "#0d1117"], [0.5, "#196c2e"], [1.0, "#39d353"]],
            text=np.round(Q.T, 2),
            texttemplate="%{text}",
            textfont=dict(family="Courier New", size=10, color="#c9d1d9"),
            colorbar=dict(
                tickfont=dict(family="Courier New", color="#c9d1d9"),
                bgcolor="#0d1117", bordercolor="#21262d",
            ),
        ))
        fig_q.update_layout(
            title=dict(text="Learned Q-Values (action value per range bin)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Range bin",
                       tickfont=dict(family="Courier New", color="#c9d1d9", size=9)),
            yaxis=dict(tickfont=dict(family="Courier New", color="#c9d1d9")),
            margin=dict(l=80, r=20, t=50, b=60), height=200,
        )
        st.plotly_chart(fig_q, use_container_width=True)

        # Policy summary + J/S and ESM lines for context
        policy = [MODE_NAMES[int(np.argmax(Q[s]))] for s in range(N_RANGE_BINS)]
        ranges_km = np.array([20 + i * 15 for i in range(N_RANGE_BINS)], dtype=float)

        fig_pol = go.Figure()
        for m_idx, (m_name, color) in enumerate(zip(MODE_NAMES, ["#e3b341", "#58a6ff", "#d2a8ff"])):
            js_vals = [_js_db(r, m_idx) for r in ranges_km]
            fig_pol.add_trace(go.Scatter(
                x=ranges_km, y=js_vals, mode="lines",
                line=dict(color=color, width=1.2, dash="dot"),
                name=f"J/S ({m_name})", opacity=0.6,
            ))
        # Highlight chosen mode
        chosen_js = [_js_db(r, int(np.argmax(Q[s]))) for s, r in enumerate(ranges_km)]
        fig_pol.add_trace(go.Scatter(
            x=ranges_km, y=chosen_js, mode="lines+markers",
            line=dict(color="#39d353", width=2),
            marker=dict(
                size=8,
                color=[{"Barrage": "#e3b341", "Spot": "#58a6ff", "Sweep": "#d2a8ff"}[p]
                       for p in policy],
            ),
            name="Chosen mode (policy)",
        ))
        fig_pol.add_hline(y=0, line=dict(color="#8b949e", dash="dot", width=1))
        fig_pol.update_layout(
            title=dict(text="Learned Policy: J/S Achieved vs Range",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Range (km)", gridcolor="#21262d"),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d", font=dict(size=9)),
            margin=dict(l=60, r=20, t=50, b=50), height=220,
        )
        st.plotly_chart(fig_pol, use_container_width=True)

        st.markdown("**Learned policy by range:**")
        cols = st.columns(N_RANGE_BINS)
        for i, (lbl, mode) in enumerate(zip(range_labels, policy)):
            color = {"Barrage": "🟡", "Spot": "🔵", "Sweep": "🟣"}[mode]
            cols[i].markdown(f"**{lbl}**\n\n{color} {mode}", unsafe_allow_html=False)
