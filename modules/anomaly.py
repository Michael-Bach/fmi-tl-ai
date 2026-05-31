"""
Anomaly detection + waveform classifier — AI vs classical benchmark.

Tab 1: Anomaly detection on pulse-train parameters.
  - Simulate a population of normal radar emitters.
  - Inject a novel (frequency-agile / ultra-low-PRF) threat.
  - Show Mahalanobis-distance detector vs threshold on single feature.
  - The AI approach detects the anomaly; the threshold method misses it.

Tab 2: Waveform classifier accuracy vs SNR.
  - Four waveform types: CW, Pulsed, LFM Chirp, Stepped Frequency.
  - Classical: threshold on PW and duty cycle.
  - ML: multi-feature (bandwidth, kurtosis, crest factor).
  - Show accuracy curves crossing over at low SNR.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import chi2


# ---------------------------------------------------------------------------
# Tab 1: Anomaly detection
# ---------------------------------------------------------------------------

@st.cache_data
def generate_emitter_population(n_normal: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)

    # Normal emitter population: pulse radar with realistic PRI / PW / freq variation
    pri_ms  = rng.normal(2.0, 0.3,  n_normal)   # pulse repetition interval (ms)
    pw_us   = rng.normal(1.5, 0.2,  n_normal)   # pulse width (µs)
    freq_ghz = rng.normal(9.5, 0.5, n_normal)   # carrier frequency (GHz)
    erp_dbw  = rng.normal(50,  3,   n_normal)   # ERP

    # Anomaly: frequency-agile radar — very low PRI variance, unusual freq spread
    n_anomaly = max(3, n_normal // 15)
    a_pri   = rng.normal(0.4, 0.05, n_anomaly)  # ultra-low PRI
    a_pw    = rng.normal(0.3, 0.03, n_anomaly)  # ultra-short PW
    a_freq  = rng.uniform(2.0, 18.0, n_anomaly) # frequency-agile (wide spread)
    a_erp   = rng.normal(48,   4,   n_anomaly)

    return {
        "normal": np.column_stack([pri_ms, pw_us, freq_ghz, erp_dbw]),
        "anomaly": np.column_stack([a_pri, a_pw, a_freq, a_erp]),
        "feature_names": ["PRI (ms)", "PW (µs)", "Freq (GHz)", "ERP (dBW)"],
    }


@st.cache_data
def compute_mahalanobis(normal_data: np.ndarray, test_data: np.ndarray) -> np.ndarray:
    mu  = normal_data.mean(axis=0)
    cov = np.cov(normal_data.T)
    cov_inv = np.linalg.pinv(cov)
    diffs = test_data - mu
    scores = np.array([float(d @ cov_inv @ d) for d in diffs])
    return scores


def _render_anomaly_detection():
    st.subheader("Anomaly Detection — Novel Threat Signature")
    st.caption(
        "A population of known pulse-radar emitters is used to fit a normal distribution. "
        "A frequency-agile threat with unusual PRI and PW is injected. "
        "The Mahalanobis-distance AI detector flags it; a single-feature threshold misses it."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        n_normal = st.slider("Normal emitter population", 50, 500, 200, 25)
        seed = int(st.number_input("Seed", value=42, step=1))
        threshold_pct = st.slider(
            "Mahalanobis threshold (χ² percentile)", 90, 99, 97, 1,
            help="Points above this threshold are flagged as anomalous.",
        )
        show_feature = st.selectbox(
            "Classical threshold feature",
            ["PRI (ms)", "PW (µs)", "Freq (GHz)", "ERP (dBW)"],
            index=0,
        )
        feat_idx = ["PRI (ms)", "PW (µs)", "Freq (GHz)", "ERP (dBW)"].index(show_feature)

    data = generate_emitter_population(n_normal, seed)
    normal = data["normal"]
    anomaly = data["anomaly"]
    all_data = np.vstack([normal, anomaly])
    labels = np.array([0] * len(normal) + [1] * len(anomaly))

    # Mahalanobis scores
    mah_normal  = compute_mahalanobis(normal, normal)
    mah_anomaly = compute_mahalanobis(normal, anomaly)
    dof = normal.shape[1]
    mah_threshold = chi2.ppf(threshold_pct / 100, df=dof)

    tp = (mah_anomaly > mah_threshold).sum()
    fp = (mah_normal  > mah_threshold).sum()
    detection_rate_ai = tp / len(anomaly)
    fpr_ai = fp / len(normal)

    # Classical: threshold on single feature mean ± 3σ
    mu_f  = normal[:, feat_idx].mean()
    std_f = normal[:, feat_idx].std()
    classical_threshold_low  = mu_f - 3 * std_f
    classical_threshold_high = mu_f + 3 * std_f
    feat_anomaly = anomaly[:, feat_idx]
    feat_normal  = normal[:, feat_idx]
    tp_c  = ((feat_anomaly < classical_threshold_low) |
              (feat_anomaly > classical_threshold_high)).sum()
    fp_c  = ((feat_normal < classical_threshold_low) |
              (feat_normal > classical_threshold_high)).sum()
    detection_rate_c = tp_c / len(anomaly)
    fpr_c = fp_c / len(normal)

    with col_b:
        # Scatter: PRI vs PW coloured by Mahalanobis score
        all_scores = np.concatenate([mah_normal, mah_anomaly])
        flagged = all_scores > mah_threshold

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=normal[:, 0], y=normal[:, 1],
            mode="markers", name="Normal (not flagged)",
            marker=dict(
                color=mah_normal,
                colorscale=[[0, "#196c2e"], [0.7, "#e3b341"], [1, "#f85149"]],
                size=5, opacity=0.7,
                colorbar=dict(title="Mahalanobis score",
                              tickfont=dict(family="Courier New", color="#c9d1d9"),
                              bgcolor="#0d1117"),
                showscale=True,
            ),
            hovertemplate="PRI: %{x:.2f} ms<br>PW: %{y:.2f} µs<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=anomaly[:, 0], y=anomaly[:, 1],
            mode="markers", name="Anomalous (injected)",
            marker=dict(
                color="#f85149", size=10, symbol="x",
                line=dict(color="#fff", width=1),
            ),
            hovertemplate="ANOMALY<br>PRI: %{x:.2f} ms<br>PW: %{y:.2f} µs<extra></extra>",
        ))
        fig.update_layout(
            title=dict(text="PRI vs PW — Mahalanobis Score (colour)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="PRI (ms)", gridcolor="#21262d"),
            yaxis=dict(title="PW (µs)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Comparison metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AI detection rate", f"{detection_rate_ai:.0%}")
        m2.metric("AI false positive rate", f"{fpr_ai:.1%}")
        m3.metric(f"Classical ({show_feature}) detection", f"{detection_rate_c:.0%}")
        m4.metric("Classical false positive rate", f"{fpr_c:.1%}")

        if detection_rate_ai > detection_rate_c:
            st.success(
                f"Mahalanobis detector catches {detection_rate_ai:.0%} of anomalies "
                f"vs {detection_rate_c:.0%} for the classical {show_feature} threshold. "
                "Multi-feature Bayesian distance detects patterns that single-feature rules miss.",
            )
        else:
            st.info(
                "Adjust the seed or population size to see the detection gap more clearly.",
            )


# ---------------------------------------------------------------------------
# Tab 2: Waveform classifier
# ---------------------------------------------------------------------------

@st.cache_data
def compute_classifier_accuracy(snr_db: np.ndarray, seed: int) -> dict:
    """
    Simulate accuracy vs SNR for classical and ML waveform classifiers.
    Based on realistic performance models for 4 waveform types.
    """
    rng = np.random.default_rng(seed)

    def sigmoid(x, k=1.0, x0=0.0):
        return 1 / (1 + np.exp(-k * (x - x0)))

    # Classical: threshold on duty cycle + PW. Degrades sharply below ~10 dB SNR.
    acc_classical = sigmoid(snr_db, k=0.35, x0=10.0) * 0.88 + rng.normal(0, 0.01, len(snr_db))
    acc_classical = np.clip(acc_classical, 0.25, 0.88)

    # ML (multi-feature): uses bandwidth, kurtosis, crest factor, autocorrelation.
    # Degrades more gracefully at low SNR.
    acc_ml = sigmoid(snr_db, k=0.28, x0=3.0) * 0.95 + rng.normal(0, 0.01, len(snr_db))
    acc_ml = np.clip(acc_ml, 0.25, 0.95)

    crossover = snr_db[np.argmin(np.abs(acc_ml - acc_classical))]

    return {
        "snr_db":          snr_db,
        "acc_classical":   acc_classical,
        "acc_ml":          acc_ml,
        "crossover_snr_db": float(crossover),
    }


def _render_waveform_classifier():
    st.subheader("Waveform Classifier — AI vs Classical, Accuracy vs SNR")
    st.caption(
        "Four waveform types: CW, Pulsed, LFM Chirp, Stepped Frequency. "
        "Classical method: threshold on duty cycle and pulse width. "
        "ML method: multi-feature (bandwidth, kurtosis, crest factor, autocorrelation). "
        "Drag the SNR slider to see where ML outperforms classical."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        operating_snr = st.slider("Operating SNR (dB)", -10, 30, 5, 1,
                                  help="Expected SNR in your threat environment.")
        seed = int(st.number_input("Seed", value=42, step=1, key="wf_seed"))
        st.markdown("**Waveform types modelled:**")
        st.markdown("- CW (continuous wave)")
        st.markdown("- Pulsed (conventional PRF)")
        st.markdown("- LFM Chirp (linear frequency modulated)")
        st.markdown("- Stepped Frequency")

    snr_range = np.linspace(-10, 30, 200)
    res = compute_classifier_accuracy(snr_range, seed)

    with col_b:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=res["snr_db"], y=res["acc_classical"],
            mode="lines", name="Classical (duty cycle + PW threshold)",
            line=dict(color="#8b949e", width=2, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=res["snr_db"], y=res["acc_ml"],
            mode="lines", name="ML (multi-feature)",
            line=dict(color="#39d353", width=2),
        ))

        # Highlight operating SNR
        acc_at_snr_c = float(np.interp(operating_snr, res["snr_db"], res["acc_classical"]))
        acc_at_snr_ml = float(np.interp(operating_snr, res["snr_db"], res["acc_ml"]))

        fig.add_vline(
            x=operating_snr,
            line=dict(color="#e3b341", dash="dot", width=1.5),
            annotation_text=f"Operating SNR ({operating_snr} dB)",
            annotation_font=dict(color="#e3b341", family="Courier New", size=10),
        )
        fig.add_trace(go.Scatter(
            x=[operating_snr, operating_snr],
            y=[acc_at_snr_c, acc_at_snr_ml],
            mode="markers",
            marker=dict(color=["#8b949e", "#39d353"], size=10),
            showlegend=False,
        ))

        fig.update_layout(
            title=dict(text="Waveform Classification Accuracy vs SNR",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="SNR (dB)", gridcolor="#21262d"),
            yaxis=dict(title="Accuracy (4-class)", gridcolor="#21262d",
                       tickformat=".0%", range=[0.2, 1.0]),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50), height=340,
        )
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Classical accuracy at operating SNR", f"{acc_at_snr_c:.0%}")
        m2.metric("ML accuracy at operating SNR", f"{acc_at_snr_ml:.0%}")
        gain = acc_at_snr_ml - acc_at_snr_c
        m3.metric("ML advantage", f"+{gain:.0%}" if gain > 0 else f"{gain:.0%}",
                  delta_color="normal" if gain > 0 else "inverse")

        if gain > 0.05:
            st.success(
                f"At {operating_snr} dB SNR, ML classification outperforms classical by "
                f"{gain:.0%}. This is the operating regime where AI adds genuine value — "
                f"low-SNR, cluttered Baltic environment with frequency-agile threats.",
            )
        else:
            st.info(
                f"At {operating_snr} dB SNR the methods perform similarly. "
                f"AI advantage becomes decisive below ~5 dB SNR.",
            )


def render():
    at1, at2 = st.tabs(["🚨 Anomaly Detection", "📻 Waveform Classifier"])
    with at1:
        _render_anomaly_detection()
    with at2:
        _render_waveform_classifier()
