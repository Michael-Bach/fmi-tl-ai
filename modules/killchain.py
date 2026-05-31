"""
SAM kill chain engagement timeline.

Models five sequential radar stages, each with a J/S threshold requirement.
Shows which stages the jammer defeats and computes Pk reduction.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8
THREAT_MODES = {"Barrage": -10, "Spot": 0, "Sweep": -5}

# Each stage: (label, J/S threshold dB, baseline Pk contribution, description)
# Thresholds represent effective J/S (after ECCM reduction) needed to defeat each stage.
# Based on open-source estimates for modern ECCM-capable SAM systems (S-300/S-400 class).
STAGES = [
    ("Search",       15, 0.90, "Wide-beam scan. Must overcome scan-to-scan integration gain."),
    ("Acquisition",  25, 0.85, "Beam narrows. Must defeat range/angle resolution and Doppler processing."),
    ("Track",        35, 0.80, "STT fire-control lock. Highest leverage point — breaking track forces re-acquisition."),
    ("Fire Control", 45, 0.75, "Precision engagement solution. High-duty-cycle radar with full ECCM suite."),
    ("Seeker",       20, 0.70, "Terminal guidance. Closer range restores jammer advantage."),
]

STAGE_COLORS_WIN  = ["#39d353", "#3fb950", "#196c2e", "#145220", "#0d3b1c"]
STAGE_COLORS_LOSE = ["#f85149", "#da3633", "#b62324", "#8e1a1a", "#6e1313"]


@st.cache_data
def compute_killchain(
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
    radar_freq_ghz: float,
    threat_mode: str,
    engagement_range_km: float,
    eccm_db: float = 0.0,
) -> dict:
    mode_penalty = THREAT_MODES[threat_mode]
    r_m = engagement_range_km * 1e3

    # J/S at engagement range (self-screening), reduced by ECCM effectiveness
    js = (
        jammer_erp_dbw + mode_penalty - radar_erp_dbw
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(r_m)
        - rcs_dbsm
        - eccm_db
    )

    # Per-stage effectiveness
    results = []
    pk_running = 1.0
    pk_jammed  = 1.0
    for label, threshold, pk_contrib, desc in STAGES:
        effective = js >= threshold
        margin    = js - threshold
        # Pk contribution: if jammer effective at this stage, probability drops by (1 - 0.15)
        pk_running *= pk_contrib
        stage_pk   = pk_contrib if not effective else pk_contrib * 0.15
        pk_jammed  *= stage_pk
        results.append({
            "stage":     label,
            "threshold": threshold,
            "js":        float(js),
            "effective": effective,
            "margin":    float(margin),
            "desc":      desc,
        })

    return {
        "stages":    results,
        "js":        float(js),
        "pk_unjammed": float(pk_running),
        "pk_jammed":   float(pk_jammed),
        "pk_reduction": float(pk_running - pk_jammed),
    }


def render():
    st.header("SAM Kill Chain — EW Intervention Timeline")
    st.caption(
        "Five sequential radar stages from search to seeker guidance. "
        "Each stage has a J/S threshold. EW effectiveness is shown stage-by-stage. "
        "Output: probability of kill (Pk) with and without EW."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**Engagement parameters**")
        engagement_range = st.slider(
            "Engagement range (km)", 10, 300, 80, 5,
            help="Range at which the strike package enters the SAM engagement envelope.",
        )
        rcs_dbsm = st.slider("Platform RCS (dBsm)", -20, 15, 5, 1,
                             help="F-35A ≈ −15 dBsm · Legacy fighter ≈ +5 dBsm · Large aircraft ≈ +15 dBsm")
        jammer_erp = st.slider("Jammer ERP (dBW)", -10, 60, 15, 1)
        threat_mode = st.selectbox("Jamming mode", list(THREAT_MODES.keys()), index=0)
        radar_erp   = st.slider("Threat radar ERP (dBW)", 20, 80, 58, 1)
        radar_freq  = st.slider("Radar frequency (GHz)", 1, 18, 10, 1)
        eccm_db = st.slider(
            "Threat ECCM effectiveness (dB)", 0, 40, 20, 2,
            help="Effective J/S reduction from radar ECCM (frequency agility, pulse compression, "
                 "sidelobe cancellation). Modern SAM fire-control radars: 20–35 dB. "
                 "Set to 0 for no ECCM.",
        )

    res = compute_killchain(
        jammer_erp, radar_erp, rcs_dbsm, radar_freq, threat_mode, engagement_range,
        eccm_db=eccm_db,
    )

    with col_b:
        # Stage bar chart
        stage_labels = [s["stage"] for s in res["stages"]]
        thresholds   = [s["threshold"] for s in res["stages"]]
        js_vals      = [res["js"]] * len(STAGES)
        effective    = [s["effective"] for s in res["stages"]]
        bar_colors   = [
            STAGE_COLORS_WIN[i] if effective[i] else STAGE_COLORS_LOSE[i]
            for i in range(len(STAGES))
        ]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=stage_labels,
            y=thresholds,
            name="J/S threshold (dB)",
            marker=dict(color="#21262d", line=dict(color="#8b949e", width=1)),
            hovertemplate="%{x}<br>Required J/S: %{y} dB<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=stage_labels,
            y=js_vals,
            mode="lines+markers",
            name=f"Achieved J/S ({res['js']:.1f} dB)",
            line=dict(color="#39d353" if res["js"] > 5 else "#f85149", width=2.5),
            marker=dict(
                color=bar_colors,
                size=14,
                symbol=["circle" if e else "x" for e in effective],
                line=dict(color="#0d1117", width=1),
            ),
            hovertemplate="%{x}<br>J/S: %{y:.1f} dB<extra></extra>",
        ))
        fig.update_layout(
            title=dict(text="J/S vs Stage Threshold — SAM Engagement",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Kill chain stage", gridcolor="#21262d"),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Pk waterfall
        pk_steps  = [1.0]
        pk_jammed_steps = [1.0]
        for s in res["stages"]:
            _, _, pk_contrib, _ = STAGES[len(pk_steps) - 1]
            pk_steps.append(pk_steps[-1] * pk_contrib)
            pk_jammed_steps.append(
                pk_jammed_steps[-1] * (pk_contrib * 0.15 if s["effective"] else pk_contrib)
            )
        stage_labels_full = ["Pre-engagement"] + [s["stage"] for s in res["stages"]]

        fig_pk = go.Figure()
        fig_pk.add_trace(go.Scatter(
            x=stage_labels_full, y=pk_steps,
            mode="lines+markers", name="Pk (no EW)",
            line=dict(color="#f85149", width=2),
            marker=dict(size=6),
        ))
        fig_pk.add_trace(go.Scatter(
            x=stage_labels_full, y=pk_jammed_steps,
            mode="lines+markers", name="Pk (with EW)",
            line=dict(color="#39d353", width=2),
            marker=dict(size=6),
        ))
        fig_pk.update_layout(
            title=dict(text="Probability of Kill Cascade",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(gridcolor="#21262d"),
            yaxis=dict(title="Pk", gridcolor="#21262d", range=[0, 1.05],
                       tickformat=".0%"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50),
            height=220,
        )
        st.plotly_chart(fig_pk, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        stages_won = sum(1 for s in res["stages"] if s["effective"])
        m1.metric("J/S at range (dB)", f"{res['js']:.1f}")
        m2.metric("Stages defeated", f"{stages_won} / {len(STAGES)}")
        m3.metric("Pk (no EW)", f"{res['pk_unjammed']:.1%}")
        m4.metric("Pk (with EW)", f"{res['pk_jammed']:.1%}",
                  delta=f"−{res['pk_reduction']:.1%}",
                  delta_color="inverse")

        if stages_won < 3:
            st.warning(
                f"Jammer defeats only {stages_won}/{len(STAGES)} stages at {engagement_range} km. "
                "Track and Fire Control stages are not suppressed — engagement remains viable for the threat.",
                icon="⚠️",
            )

        st.subheader("Stage breakdown")
        for s in res["stages"]:
            badge = "✅" if s["effective"] else "❌"
            margin_str = f"+{s['margin']:.1f}" if s["margin"] >= 0 else f"{s['margin']:.1f}"
            st.markdown(
                f"{badge} **{s['stage']}** — threshold {s['threshold']} dB, "
                f"margin {margin_str} dB — *{s['desc']}*"
            )
