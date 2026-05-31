"""
Multi-sensor Kalman fusion — sensor fusion advisory prototype.

Three sensor types with different uncertainty characteristics:
  - Radar:   good range AND bearing  → isotropic covariance
  - ESM:     good bearing ONLY       → elongated ellipse (large range uncertainty)
  - SIGINT:  coarse position estimate → large isotropic covariance

Shows:
  1. Each sensor's solo track + uncertainty ellipse
  2. Fused track + tighter uncertainty ellipse
  3. RMSE reduction vs. number of sensors fused
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Sensor positions (relative to scene, km)
SENSOR_POSITIONS = {
    "Radar": np.array([0.0, 0.0]),
    "ESM":   np.array([-50.0, 30.0]),
    "SIGINT": np.array([20.0, -40.0]),
}


def _uncertainty_ellipse(cov2x2: np.ndarray, center: np.ndarray, n_std: float = 2.0, n_pts: int = 100):
    """Return (x, y) points for the n_std-sigma uncertainty ellipse of cov2x2 centred at center."""
    vals, vecs = np.linalg.eigh(cov2x2)
    vals = np.maximum(vals, 1e-9)
    theta = np.linspace(0, 2 * np.pi, n_pts)
    circle = np.column_stack([np.cos(theta), np.sin(theta)])
    ellipse = circle @ (vecs * (n_std * np.sqrt(vals)))
    return center[0] + ellipse[:, 0], center[1] + ellipse[:, 1]


@st.cache_data
def simulate_fusion(
    n_steps: int,
    radar_noise_km: float,
    esm_range_noise_km: float,
    esm_bearing_noise_km: float,
    sigint_noise_km: float,
    seed: int,
) -> dict:
    rng = np.random.default_rng(seed)

    # True target trajectory: straight line
    t = np.linspace(0, 1, n_steps)
    true_x = 50 + 80 * t
    true_y = 20 + 30 * t
    true_pos = np.column_stack([true_x, true_y])

    # Per-sensor measurements
    def measure(pos, noise_x, noise_y):
        return pos + rng.normal(0, 1, pos.shape) * np.array([noise_x, noise_y])

    radar_meas  = measure(true_pos, radar_noise_km, radar_noise_km)
    esm_meas    = measure(true_pos, esm_range_noise_km, esm_bearing_noise_km)
    sigint_meas = measure(true_pos, sigint_noise_km, sigint_noise_km)

    # Covariance matrices
    R_radar  = np.diag([radar_noise_km**2,  radar_noise_km**2])
    R_esm    = np.diag([esm_range_noise_km**2, esm_bearing_noise_km**2])
    R_sigint = np.diag([sigint_noise_km**2, sigint_noise_km**2])

    # Kalman fusion: sequential update for each sensor
    H = np.eye(2)  # measurement matrix (position only)
    fused_pos = np.zeros_like(true_pos)
    fused_covs = []

    for i in range(n_steps):
        # Prior (identity covariance — no prediction step for simplicity)
        P = np.diag([1e6, 1e6])
        x = np.array([0.0, 0.0])

        for meas, R in [(radar_meas[i], R_radar),
                        (esm_meas[i], R_esm),
                        (sigint_meas[i], R_sigint)]:
            S = H @ P @ H.T + R
            K = P @ H.T @ np.linalg.inv(S)
            innov = meas - H @ x
            x = x + K @ innov
            P = (np.eye(2) - K @ H) @ P

        fused_pos[i] = x
        fused_covs.append(P.copy())

    def rmse(est, truth):
        return float(np.sqrt(np.mean(np.sum((est - truth)**2, axis=1))))

    # Solo tracks (just the measurement average — no prior fusion)
    rmse_radar  = rmse(radar_meas,  true_pos)
    rmse_esm    = rmse(esm_meas,    true_pos)
    rmse_sigint = rmse(sigint_meas, true_pos)
    rmse_fused  = rmse(fused_pos,   true_pos)

    # Mid-point covariances for ellipse display
    mid = n_steps // 2
    cov_radar  = R_radar
    cov_esm    = R_esm
    cov_sigint = R_sigint
    cov_fused  = fused_covs[mid]

    return {
        "true_pos":    true_pos,
        "radar_meas":  radar_meas,
        "esm_meas":    esm_meas,
        "sigint_meas": sigint_meas,
        "fused_pos":   fused_pos,
        "cov_radar":   cov_radar,
        "cov_esm":     cov_esm,
        "cov_sigint":  cov_sigint,
        "cov_fused":   cov_fused,
        "mid_idx":     mid,
        "rmse": {
            "Radar":  rmse_radar,
            "ESM":    rmse_esm,
            "SIGINT": rmse_sigint,
            "Fused":  rmse_fused,
        },
    }


def render():
    st.header("Multi-Sensor Fusion — Kalman Track Combination")
    st.caption(
        "Three sensor types with different uncertainty characteristics. "
        "Kalman fusion sequentially assimilates each measurement. "
        "Demonstrates why 'Fusion' is listed as a separate advisory area in the TEW mandate: "
        "no single sensor gives the full picture."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**Sensor noise parameters**")
        radar_noise   = st.slider("Radar position noise (km)", 0.5, 10.0, 1.5, 0.5,
                                   help="Isotropic: radar measures range and bearing well.")
        esm_range_noise = st.slider("ESM range uncertainty (km)", 5.0, 50.0, 20.0, 2.5,
                                     help="ESM has bearing only — large range uncertainty.")
        esm_bear_noise  = st.slider("ESM bearing uncertainty (km)", 0.5, 5.0, 1.0, 0.5,
                                     help="ESM bearing is precise — small cross-range noise.")
        sigint_noise    = st.slider("SIGINT position noise (km)", 5.0, 30.0, 10.0, 2.5,
                                     help="Coarse geolocation from frequency analysis.")
        n_steps = st.slider("Track points", 10, 50, 20, 5)
        seed    = int(st.number_input("Seed", value=42, step=1))

    res = simulate_fusion(n_steps, radar_noise, esm_range_noise,
                          esm_bear_noise, sigint_noise, seed)

    with col_b:
        fig = go.Figure()
        mid = res["mid_idx"]

        # True track
        fig.add_trace(go.Scatter(
            x=res["true_pos"][:, 0], y=res["true_pos"][:, 1],
            mode="lines", name="True track",
            line=dict(color="#8b949e", width=2, dash="dot"),
        ))

        sensor_cfg = [
            ("radar_meas",  res["cov_radar"],  "#58a6ff", "Radar"),
            ("esm_meas",    res["cov_esm"],    "#e3b341", "ESM (bearing-only)"),
            ("sigint_meas", res["cov_sigint"], "#d2a8ff", "SIGINT"),
            ("fused_pos",   res["cov_fused"],  "#39d353", "Fused"),
        ]

        for key, cov, color, name in sensor_cfg:
            pts = res[key]
            fig.add_trace(go.Scatter(
                x=pts[:, 0], y=pts[:, 1],
                mode="lines+markers",
                name=f"{name} (RMSE {res['rmse'].get(name.split()[0], res['rmse']['Fused']):.1f} km)",
                line=dict(color=color, width=1.5 if name != "Fused" else 2.5,
                          dash="dot" if name != "Fused" else "solid"),
                marker=dict(size=4),
                opacity=0.8 if name != "Fused" else 1.0,
            ))

            # Uncertainty ellipse at mid-point
            cx, cy = _uncertainty_ellipse(cov, pts[mid])
            fig.add_trace(go.Scatter(
                x=cx, y=cy, mode="lines",
                line=dict(color=color, width=1, dash="dot"),
                showlegend=False, hoverinfo="skip",
                fill="toself", fillcolor=color.replace(")", ", 0.06)").replace("rgb(", "rgba(").replace("#", "rgba(") if "#" in color else color,
                opacity=0.3,
            ))

        # Draw sensor positions
        for sname, spos in SENSOR_POSITIONS.items():
            fig.add_trace(go.Scatter(
                x=[spos[0]], y=[spos[1]],
                mode="markers+text",
                marker=dict(color="#f85149", size=10, symbol="triangle-up"),
                text=[sname], textposition="top center",
                textfont=dict(family="Courier New", color="#f85149", size=9),
                showlegend=False,
                hoverinfo="text",
            ))

        fig.update_layout(
            title=dict(text="Multi-Sensor Track Fusion — 2σ Uncertainty Ellipses at Mid-Track",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="East (km)", gridcolor="#21262d", scaleanchor="y"),
            yaxis=dict(title="North (km)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d", font=dict(size=9)),
            margin=dict(l=60, r=20, t=60, b=50),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

        # RMSE bar
        rmse_vals = res["rmse"]
        fig_bar = go.Figure(go.Bar(
            x=list(rmse_vals.keys()),
            y=list(rmse_vals.values()),
            marker=dict(
                color=["#58a6ff", "#e3b341", "#d2a8ff", "#39d353"],
                line=dict(color="#0d1117", width=1),
            ),
        ))
        fig_bar.update_layout(
            title=dict(text="RMSE by Sensor (km) — lower is better",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(title="RMSE (km)", gridcolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=200,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        improvement = (rmse_vals["Radar"] - rmse_vals["Fused"]) / rmse_vals["Radar"] * 100
        m1, m2, m3 = st.columns(3)
        m1.metric("Best single-sensor RMSE (km)",
                  f"{min(rmse_vals['Radar'], rmse_vals['ESM'], rmse_vals['SIGINT']):.1f}")
        m2.metric("Fused RMSE (km)", f"{rmse_vals['Fused']:.1f}")
        m3.metric("Improvement vs radar alone", f"{improvement:.0f}%")

        with st.expander("Acquisition relevance"):
            st.markdown(
                "Sensor fusion matters for procurement because Danish sensor programmes "
                "often evaluate systems in isolation — radar vs radar, ESM vs ESM. "
                "The combined track quality of a multi-sensor architecture is only visible "
                "through simulation. A standalone radar kravspecifikation that ignores "
                "the ESM contribution underspecifies the architecture and overspecifies "
                "the individual sensor. This analysis supports the case for "
                "system-level requirements rather than box-level requirements."
            )
