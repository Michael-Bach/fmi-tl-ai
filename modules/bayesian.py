import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm as sp_norm

SPEED_OF_LIGHT = 3e8


@st.cache_data
def run_bayesian_update(
    true_erp: float,
    esm_range_km: float,
    radar_freq_ghz: float,
    meas_noise_db: float,
    n_obs: int,
    seed: int,
) -> dict:
    rng = np.random.default_rng(seed)

    wavelength = SPEED_OF_LIGHT / (radar_freq_ghz * 1e9)
    fspl = 20 * np.log10(4 * np.pi * esm_range_km * 1e3 / wavelength)
    true_received_dbm = true_erp - fspl + 30

    # Noisy ESM power observations
    obs_dbm = true_received_dbm + rng.normal(0, meas_noise_db, n_obs)

    # Each observation gives a noisy ERP estimate: ERP_i = obs_i + FSPL - 30
    erp_estimates = obs_dbm + fspl - 30

    # Conjugate Gaussian-Gaussian Bayesian update
    # Prior: ERP ~ N(35, 15²) — broad, covers the plausible 10–80 dBW range
    mu_prior, sigma_prior = 35.0, 15.0
    mus, sigmas = [], []
    mu, sigma = mu_prior, sigma_prior
    for est in erp_estimates:
        prec_post = 1 / sigma**2 + 1 / meas_noise_db**2
        mu_post = (mu / sigma**2 + est / meas_noise_db**2) / prec_post
        sigma_post = np.sqrt(1 / prec_post)
        mus.append(mu_post)
        sigmas.append(sigma_post)
        mu, sigma = mu_post, sigma_post

    erp_range = np.linspace(0, 90, 500)
    prior_pdf = sp_norm.pdf(erp_range, mu_prior, sigma_prior)
    posterior_pdf = sp_norm.pdf(erp_range, mus[-1], sigmas[-1])

    return {
        "erp_range": erp_range,
        "prior_pdf": prior_pdf,
        "posterior_pdf": posterior_pdf,
        "posteriors_mu": mus,
        "posteriors_sigma": sigmas,
        "erp_estimates": erp_estimates,
        "final_mu": mus[-1],
        "final_sigma": sigmas[-1],
    }


def render():
    st.header("Bayesian Threat Parameter Estimation")
    st.caption(
        "ESM receiver collects noisy power measurements. Conjugate Gaussian-Gaussian "
        "Bayesian updating infers the threat radar ERP posterior. "
        "Shows why single-shot classical estimation breaks under measurement noise — "
        "and how Bayesian updating recovers accuracy with repeated observations."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**True threat parameters (hidden in reality)**")
        true_erp = st.slider("True ERP (dBW)", 20, 80, 50, 1)
        radar_freq = st.slider("Radar frequency (GHz)", 1, 18, 10, 1)

        st.markdown("**ESM platform**")
        esm_range = st.slider("ESM platform range (km)", 10, 300, 80, 5)
        meas_noise = st.slider("Measurement noise σ (dB)", 0.5, 8.0, 3.0, 0.5,
                               help="1σ uncertainty on each received power measurement")
        n_obs = st.slider("Number of observations", 1, 50, 15, 1)
        seed = st.number_input("Random seed", value=42, step=1)

    result = run_bayesian_update(true_erp, esm_range, radar_freq, meas_noise, n_obs, int(seed))

    with col_b:
        # Prior vs posterior PDF
        fig_pdf = go.Figure()
        fig_pdf.add_trace(go.Scatter(
            x=result["erp_range"], y=result["prior_pdf"],
            mode="lines", name="Prior (broad — no observations)",
            line=dict(color="#8b949e", dash="dash", width=1.5),
        ))
        fig_pdf.add_trace(go.Scatter(
            x=result["erp_range"], y=result["posterior_pdf"],
            mode="lines", name=f"Posterior (n={n_obs} observations)",
            line=dict(color="#39d353", width=2),
        ))
        fig_pdf.add_vline(
            x=true_erp,
            line=dict(color="#f85149", dash="dot", width=2),
            annotation_text="True ERP",
            annotation_font=dict(color="#f85149", family="Courier New", size=10),
        )
        fig_pdf.add_vline(
            x=result["final_mu"],
            line=dict(color="#39d353", dash="dash", width=1),
            annotation_text=f"Estimate: {result['final_mu']:.1f} dBW",
            annotation_position="top left",
            annotation_font=dict(color="#39d353", family="Courier New", size=10),
        )
        fig_pdf.update_layout(
            title=dict(text="ERP Posterior Distribution",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Estimated ERP (dBW)", gridcolor="#21262d"),
            yaxis=dict(title="Probability density", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=260,
        )
        st.plotly_chart(fig_pdf, use_container_width=True)

        # Convergence with observation count
        obs_idx = list(range(1, n_obs + 1))
        upper = [m + 2 * s for m, s in zip(result["posteriors_mu"], result["posteriors_sigma"])]
        lower = [m - 2 * s for m, s in zip(result["posteriors_mu"], result["posteriors_sigma"])]

        fig_conv = go.Figure()
        fig_conv.add_trace(go.Scatter(
            x=obs_idx + obs_idx[::-1],
            y=upper + lower[::-1],
            fill="toself", fillcolor="rgba(57,211,83,0.10)",
            line=dict(color="rgba(0,0,0,0)"),
            name="95% credible interval", hoverinfo="skip",
        ))
        fig_conv.add_trace(go.Scatter(
            x=obs_idx, y=result["posteriors_mu"],
            mode="lines+markers", line=dict(color="#39d353", width=2),
            marker=dict(size=4), name="Posterior mean",
        ))
        fig_conv.add_hline(
            y=true_erp, line=dict(color="#f85149", dash="dot", width=1.5),
            annotation_text="True ERP",
            annotation_font=dict(color="#f85149", family="Courier New", size=10),
        )
        fig_conv.update_layout(
            title=dict(text="Posterior Convergence with Observations",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Number of ESM observations", gridcolor="#21262d"),
            yaxis=dict(title="ERP estimate (dBW)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=240,
        )
        st.plotly_chart(fig_conv, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Posterior mean ERP (dBW)", f"{result['final_mu']:.1f}")
        m2.metric("95% CI width (dB)", f"{4 * result['final_sigma']:.1f}")
        error = abs(result["final_mu"] - true_erp)
        m3.metric("Estimation error (dB)", f"{error:.1f}",
                  delta=f"{error:.1f} dB from truth",
                  delta_color="inverse")

    with st.expander("Why this matters for acquisition"):
        st.markdown(
            "A single ESM intercept at 3 dB noise gives an ERP estimate with "
            "a ±6 dB 95% interval — a factor of 4 uncertainty in power. "
            "Writing a kravspecifikation jammer ERP requirement on that single intercept "
            "would be unsound. "
            "Bayesian updating across 10–15 observations compresses the credible interval "
            "to under 2 dB, sufficient to anchor a requirements document. "
            "This is the capability gap between a classical ESM receiver report and an "
            "AI-assisted intelligence product."
        )
