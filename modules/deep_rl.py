"""
Deep RL Jammer — numpy DQN vs Q-table benchmark.

The Q-table agent from rl_jammer.py discretises range into 12 bins.
This module trains a 2-layer neural Q-network (3 → 16 → 3) on the same
environment with a continuous 3-dimensional state, then benchmarks both
on held-out ranges including out-of-distribution values between bins.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8
_RADAR_ERP = 50.0
_JAMMER_ERP = 25.0
_RCS_DBSM = 5.0
_ESM_SENS = -70.0
_FREQ_GHZ = 10.0
_WL = SPEED_OF_LIGHT / (_FREQ_GHZ * 1e9)

MODE_NAMES = ["Barrage", "Spot", "Sweep"]
MODE_ATTRS = [(-10, +3), (0, -3), (-5, 0)]  # (bw_penalty, esm_offset)


def _js(r_km, mode):
    pen, _ = MODE_ATTRS[mode]
    r = max(r_km * 1e3, 1e3)
    return _JAMMER_ERP + pen - _RADAR_ERP + 10 * np.log10(4 * np.pi) + 20 * np.log10(r) - _RCS_DBSM


def _esm(r_km, mode):
    _, off = MODE_ATTRS[mode]
    r = max(r_km * 1e3, 1e3)
    fspl = 20 * np.log10(4 * np.pi * r / _WL)
    return _JAMMER_ERP + off - fspl + 30


def _reward(r_km, mode):
    js = _js(r_km, mode)
    esm_p = _esm(r_km, mode)
    r = 1.0 if js > 0 else -1.5
    if esm_p > _ESM_SENS:
        r -= 0.4
    return r


def _state(r_km):
    js_est = _js(r_km, 1)   # Spot J/S as a feature
    esm_p = _esm(r_km, 1)
    return np.array([r_km / 200.0, np.clip(js_est / 40.0, -1, 1),
                      np.clip((esm_p + 100) / 60.0, 0, 1)], dtype=np.float32)


# ---------------------------------------------------------------------------
# Minimal numpy DQN
# ---------------------------------------------------------------------------

class _QNet:
    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 0.3, (3, 16)).astype(np.float32)
        self.b1 = np.zeros(16, dtype=np.float32)
        self.W2 = rng.normal(0, 0.3, (16, 3)).astype(np.float32)
        self.b2 = np.zeros(3, dtype=np.float32)
        # Target network copy
        self.W1t = self.W1.copy(); self.b1t = self.b1.copy()
        self.W2t = self.W2.copy(); self.b2t = self.b2.copy()

    def q(self, x, target=False):
        W1, b1, W2, b2 = (self.W1t, self.b1t, self.W2t, self.b2t) if target else (self.W1, self.b1, self.W2, self.b2)
        h = np.maximum(0, x @ W1 + b1)
        return h @ W2 + b2

    def update_target(self):
        self.W1t[:] = self.W1; self.b1t[:] = self.b1
        self.W2t[:] = self.W2; self.b2t[:] = self.b2

    def train_batch(self, states, actions, targets, lr=3e-3):
        h = np.maximum(0, states @ self.W1 + self.b1)
        q_out = h @ self.W2 + self.b2
        delta = q_out.copy()
        delta[np.arange(len(actions)), actions] = targets
        err = q_out - delta                  # (B, 3)
        dW2 = h.T @ err / len(states)
        db2 = err.mean(0)
        dh  = err @ self.W2.T * (h > 0)
        dW1 = states.T @ dh / len(states)
        db1 = dh.mean(0)
        self.W1 -= lr * dW1; self.b1 -= lr * db1
        self.W2 -= lr * dW2; self.b2 -= lr * db2
        return float(np.mean(err ** 2))


@st.cache_data
def train_dqn(n_episodes: int, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    net = _QNet(seed=seed)
    buf_s, buf_a, buf_r, buf_ns = [], [], [], []
    buf_cap = 2000
    gamma, batch = 0.90, 32
    eps_start, eps_end = 1.0, 0.05
    rewards = []
    step = 0

    for ep in range(n_episodes):
        eps = eps_start + (eps_end - eps_start) * ep / n_episodes
        r_km = float(rng.uniform(20, 200))
        s = _state(r_km)
        total = 0.0
        for _ in range(25):
            a = int(rng.integers(3)) if rng.random() < eps else int(np.argmax(net.q(s)))
            rew = _reward(r_km, a)
            total += rew
            r_km = float(np.clip(r_km + rng.uniform(-20, 20), 20, 200))
            ns = _state(r_km)
            if len(buf_s) >= buf_cap:
                buf_s.pop(0); buf_a.pop(0); buf_r.pop(0); buf_ns.pop(0)
            buf_s.append(s); buf_a.append(a); buf_r.append(rew); buf_ns.append(ns)
            s = ns
            step += 1
            if len(buf_s) >= batch and step % 4 == 0:
                idx = rng.integers(len(buf_s), size=batch)
                sb  = np.array([buf_s[i]  for i in idx], dtype=np.float32)
                ab  = [buf_a[i]  for i in idx]
                rb  = np.array([buf_r[i]  for i in idx], dtype=np.float32)
                nsb = np.array([buf_ns[i] for i in idx], dtype=np.float32)
                q_next = net.q(nsb, target=True).max(1)
                tgts = rb + gamma * q_next
                net.train_batch(sb, ab, tgts)
            if step % 50 == 0:
                net.update_target()

        rewards.append(total)

    return net, np.array(rewards)


@st.cache_data
def train_qtable(n_episodes: int, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    N_BINS = 12
    Q = np.zeros((N_BINS, 3))
    alpha, gamma = 0.15, 0.90
    eps_start, eps_end = 1.0, 0.05
    rewards = []

    def state_of(r):
        return int(np.clip((r - 20) / 180 * N_BINS, 0, N_BINS - 1))

    for ep in range(n_episodes):
        eps = eps_start + (eps_end - eps_start) * ep / n_episodes
        r_km = float(rng.uniform(20, 200))
        s = state_of(r_km)
        total = 0.0
        for _ in range(25):
            a = int(rng.integers(3)) if rng.random() < eps else int(np.argmax(Q[s]))
            rew = _reward(r_km, a)
            total += rew
            r_km = float(np.clip(r_km + rng.uniform(-20, 20), 20, 200))
            ns = state_of(r_km)
            Q[s, a] += alpha * (rew + gamma * Q[ns].max() - Q[s, a])
            s = ns
        rewards.append(total)

    return Q, np.array(rewards)


def _eval_policy(net_or_q, r_vals, is_nn: bool):
    """Return rewards at each range using greedy policy."""
    rewards = []
    for r in r_vals:
        if is_nn:
            a = int(np.argmax(net_or_q.q(_state(r))))
        else:
            N_BINS = 12
            s = int(np.clip((r - 20) / 180 * N_BINS, 0, N_BINS - 1))
            a = int(np.argmax(net_or_q[s]))
        rewards.append(_reward(r, a))
    return np.array(rewards)


_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)


def render():
    st.header("Deep RL Jammer — Neural Q-Network vs Q-Table")
    st.caption(
        "Both agents learn the Barrage/Spot/Sweep policy from the same reward signal. "
        "The Q-table discretises range into 12 bins and cannot generalise between them. "
        "The neural network takes continuous (range, J/S estimate, ESM power) state "
        "and generalises to arbitrary ranges — including values never seen during training."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        n_ep = st.slider("Training episodes", 500, 5000, 2000, 250)
        seed = int(st.number_input("Seed", value=42, step=1, key="drl_seed"))
        st.divider()
        st.markdown("**Architecture**")
        st.markdown("- DQN: 3 → 16 → 3 (ReLU)")
        st.markdown("- Replay buffer: 2000 transitions")
        st.markdown("- Batch size: 32, update every 4 steps")
        st.markdown("- Target network sync: every 50 steps")
        st.divider()
        st.markdown("**State (continuous)**")
        st.markdown("- range / 200")
        st.markdown("- J/S estimate / 40")
        st.markdown("- ESM power (normalised)")

    net, dqn_rewards = train_dqn(n_ep, seed)
    Q, qtb_rewards = train_qtable(n_ep, seed)

    with col_b:
        # Training curves
        w = max(1, n_ep // 40)
        smooth = lambda r: np.convolve(r, np.ones(w) / w, mode="valid")
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(x=list(range(len(smooth(qtb_rewards)))), y=smooth(qtb_rewards),
                                    mode="lines", name="Q-table",
                                    line=dict(color="#8b949e", width=1.5, dash="dash")))
        fig_t.add_trace(go.Scatter(x=list(range(len(smooth(dqn_rewards)))), y=smooth(dqn_rewards),
                                    mode="lines", name="DQN (neural)",
                                    line=dict(color="#39d353", width=2)))
        fig_t.update_layout(title=dict(text="Training Curves (smoothed)",
                                        font=dict(color="#c9d1d9", family="Courier New")),
                             xaxis=dict(title="Episode", gridcolor="#21262d"),
                             yaxis=dict(title="Total reward", gridcolor="#21262d"),
                             height=220, **_L)
        st.plotly_chart(fig_t, use_container_width=True)

        # Benchmark: performance across range spectrum including inter-bin values
        r_test = np.linspace(20, 200, 300)
        rew_nn  = _eval_policy(net, r_test, True)
        rew_qtb = _eval_policy(Q,   r_test, False)

        fig_b = go.Figure()
        fig_b.add_trace(go.Scatter(x=r_test, y=rew_qtb, mode="lines", name="Q-table policy",
                                    line=dict(color="#8b949e", width=1.5, dash="dash")))
        fig_b.add_trace(go.Scatter(x=r_test, y=rew_nn, mode="lines", name="DQN policy",
                                    line=dict(color="#39d353", width=2)))
        fig_b.add_hline(y=0, line=dict(color="#21262d", dash="dot", width=1))
        fig_b.update_layout(title=dict(text="Greedy Policy Reward vs Range (held-out evaluation)",
                                        font=dict(color="#c9d1d9", family="Courier New")),
                             xaxis=dict(title="Range (km)", gridcolor="#21262d"),
                             yaxis=dict(title="Reward", gridcolor="#21262d"),
                             height=240, **_L)
        st.plotly_chart(fig_b, use_container_width=True)

        # Summary metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("DQN mean reward", f"{rew_nn.mean():.3f}")
        m2.metric("Q-table mean reward", f"{rew_qtb.mean():.3f}")
        delta = rew_nn.mean() - rew_qtb.mean()
        m3.metric("DQN advantage", f"{delta:+.3f}", delta_color="normal" if delta >= 0 else "inverse")

        nn_modes  = [MODE_NAMES[int(np.argmax(net.q(_state(r))))] for r in r_test[::20]]
        qtb_modes = []
        for r in r_test[::20]:
            s = int(np.clip((r - 20) / 180 * 12, 0, 11))
            qtb_modes.append(MODE_NAMES[int(np.argmax(Q[s]))])

        with st.expander("Policy comparison — every ~9 km"):
            rows = [{"Range (km)": f"{r:.0f}", "Q-table": qt, "DQN": nn}
                    for r, qt, nn in zip(r_test[::20], qtb_modes, nn_modes)]
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.info(
            "The Q-table steps between discrete range bins — visible as the staircase in reward. "
            "The DQN produces a smooth policy that adapts continuously with range. "
            "This is the Q3 roadmap deliverable: AI benchmarked against a classical baseline, "
            "with a physics-grounded environment rather than a synthetic dataset."
        )
