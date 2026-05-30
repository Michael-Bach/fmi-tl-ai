"""
Procurement Risk Quantification Engine.

Translates burn-through Monte Carlo distributions into acquisition-language
risk metrics: P(mission success), parameter sensitivity ranking, lifecycle
forecast, and minimum ERP requirement for a specified confidence target.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8
THREAT_MODES   = {"Barrage": -10, "Spot": 0, "Sweep": -5}

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)


@st.cache_data
def run_risk_mc(
    jammer_erp: float,
    radar_erp: float,
    rcs_dbsm: float,
    mode: str,
    sigma_j: float = 1.5,
    sigma_r: float = 1.0,
    sigma_rcs: float = 1.5,
    n: int = 5000,
    seed: int = 42,
) -> dict:
    rng = np.random.default_rng(seed)
    pen = THREAT_MODES[mode]

    j  = jammer_erp + rng.normal(0, sigma_j,   n)
    r  = radar_erp  + rng.normal(0, sigma_r,   n)
    rc = rcs_dbsm   + rng.normal(0, sigma_rcs, n)

    exp = (r - j - pen + rc - 10 * np.log10(4 * np.pi)) / 20
    bt  = (10 ** exp) / 1e3   # km

    return {
        "bt_km": bt,
        "p10":  float(np.percentile(bt, 10)),
        "p50":  float(np.percentile(bt, 50)),
        "p90":  float(np.percentile(bt, 90)),
        "mean": float(bt.mean()),
        "std":  float(bt.std()),
    }


@st.cache_data
def sensitivity_analysis(
    jammer_erp: float,
    radar_erp: float,
    rcs_dbsm: float,
    mode: str,
    sigma_j: float,
    sigma_r: float,
    sigma_rcs: float,
) -> list:
    pen = THREAT_MODES[mode]

    def bt_nominal(j, r, rc):
        exp = (r - j - pen + rc - 10 * np.log10(4 * np.pi)) / 20
        return (10 ** exp) / 1e3

    base = bt_nominal(jammer_erp, radar_erp, rcs_dbsm)
    params = [
        ("Jammer ERP",   jammer_erp, sigma_j,   "dBW", True),
        ("Radar ERP",    radar_erp,  sigma_r,    "dBW", False),
        ("Target RCS",   rcs_dbsm,   sigma_rcs,  "dBsm", False),
    ]
    results = []
    for name, nominal, sigma, unit, is_jammer in params:
        bt_plus  = bt_nominal(
            nominal + sigma if is_jammer else jammer_erp,
            nominal + sigma if name == "Radar ERP" else radar_erp,
            nominal + sigma if name == "Target RCS" else rcs_dbsm,
        ) if not is_jammer else bt_nominal(nominal + sigma, radar_erp, rcs_dbsm)
        bt_minus = bt_nominal(
            nominal - sigma if is_jammer else jammer_erp,
            nominal - sigma if name == "Radar ERP" else radar_erp,
            nominal - sigma if name == "Target RCS" else rcs_dbsm,
        ) if not is_jammer else bt_nominal(nominal - sigma, radar_erp, rcs_dbsm)
        swing = abs(bt_plus - bt_minus)
        direction = "lowers BT ✓" if (is_jammer and bt_plus < base) else "raises BT ✗"
        results.append({
            "Parameter": name,
            "Nominal": f"{nominal:.1f} {unit}",
            "1σ uncertainty": f"±{sigma:.1f} {unit}",
            "Δ BT (km)": f"{swing:.3f}",
            "Effect": direction if is_jammer else (
                "raises BT ✗" if bt_plus > bt_minus else "lowers BT ✓"
            ),
        })
    results.sort(key=lambda x: float(x["Δ BT (km)"]), reverse=True)
    return results


@st.cache_data
def lifecycle_forecast(
    jammer_erp: float,
    radar_erp: float,
    rcs_dbsm: float,
    mode: str,
    threat_growth_db_yr: float,
    jammer_growth_db_yr: float,
    years: int,
    engagement_range_km: float,
    n: int = 2000,
) -> dict:
    pen = THREAT_MODES[mode]
    year_range = list(range(years + 1))
    pms = []
    bt_p50s = []

    for yr in year_range:
        r_yr = radar_erp  + threat_growth_db_yr  * yr
        j_yr = jammer_erp + jammer_growth_db_yr  * yr
        rng = np.random.default_rng(42 + yr)
        j_s = j_yr + rng.normal(0, 1.5, n)
        r_s = r_yr + rng.normal(0, 1.0, n)
        rc_s = rcs_dbsm + rng.normal(0, 1.5, n)
        exp = (r_s - j_s - pen + rc_s - 10 * np.log10(4 * np.pi)) / 20
        bt = (10 ** exp) / 1e3
        pms.append(float((bt < engagement_range_km).mean()))
        bt_p50s.append(float(np.percentile(bt, 50)))

    # Year when P(success) drops below 0.5
    fail_year = next((yr for yr, pm in zip(year_range, pms) if pm < 0.50), None)

    return {
        "years": year_range,
        "p_success": pms,
        "bt_p50": bt_p50s,
        "fail_year": fail_year,
    }


@st.cache_data
def min_erp_for_confidence(
    radar_erp: float,
    rcs_dbsm: float,
    mode: str,
    target_pm: float,
    engagement_range_km: float,
    sigma_j: float,
    sigma_r: float,
    sigma_rcs: float,
    n: int = 3000,
) -> float:
    """Binary search for minimum jammer ERP achieving P(BT < engagement_range) = target_pm."""
    pen = THREAT_MODES[mode]
    rng = np.random.default_rng(42)
    r_s  = radar_erp  + rng.normal(0, sigma_r,   n)
    rc_s = rcs_dbsm   + rng.normal(0, sigma_rcs, n)

    lo, hi = -10.0, 80.0
    for _ in range(30):
        mid = (lo + hi) / 2
        j_s = mid + rng.normal(0, sigma_j, n)
        exp = (r_s - j_s - pen + rc_s - 10 * np.log10(4 * np.pi)) / 20
        bt = (10 ** exp) / 1e3
        pm  = float((bt < engagement_range_km).mean())
        if pm < target_pm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def render():
    st.header("Procurement Risk Quantification Engine")
    st.caption(
        "Translate simulation uncertainty into acquisition-language risk: "
        "P(mission success), parameter sensitivity, lifecycle forecast. "
        "The output directly informs kravspecifikation ERP requirements "
        "and the procurement risk register."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**Nominal parameters**")
        j_erp = st.slider("Jammer ERP (dBW)", -10, 60, 20, 1, key="risk_jerp")
        r_erp = st.slider("Radar ERP (dBW)",   20, 80, 55, 1, key="risk_rerp")
        rcs   = st.slider("Target RCS (dBsm)", -25, 20, -15, 1, key="risk_rcs")
        mode  = st.selectbox("Jamming mode", list(THREAT_MODES), index=1, key="risk_mode")
        st.markdown("**Parameter uncertainty (1σ)**")
        sj  = st.slider("σ Jammer ERP (dB)", 0.5, 5.0, 1.5, 0.5, key="risk_sj")
        sr  = st.slider("σ Radar ERP (dB)",  0.5, 5.0, 1.0, 0.5, key="risk_sr")
        src = st.slider("σ RCS (dBsm)",       0.5, 5.0, 1.5, 0.5, key="risk_srcs")
        st.markdown("**Mission requirements**")
        eng_range = st.slider("Required max burn-through (km)", 0.5, 30.0, 5.0, 0.5,
                               help="Mission succeeds when burn-through < this range.")
        conf_target = st.slider("Confidence target (%)", 50, 99, 90, 5)
        st.markdown("**Lifecycle**")
        threat_growth = st.slider("Threat ERP growth (dB/yr)",  0.0, 3.0, 1.2, 0.1)
        jammer_growth = st.slider("Jammer ERP growth (dB/yr)",  0.0, 3.0, 0.5, 0.1)
        forecast_yrs  = st.slider("Forecast horizon (years)",   3, 20, 10, 1)

    mc = run_risk_mc(j_erp, r_erp, rcs, mode, sj, sr, src)
    pm_now = float((mc["bt_km"] < eng_range).mean())

    with col_b:
        # Burn-through distribution
        fig_hist = go.Figure()
        counts, edges = np.histogram(mc["bt_km"], bins=80, range=(0, min(50, mc["p90"] * 2)))
        fig_hist.add_trace(go.Bar(
            x=(edges[:-1] + edges[1:]) / 2, y=counts,
            marker=dict(color="#39d353", opacity=0.7),
            name="Burn-through distribution",
        ))
        fig_hist.add_vline(x=eng_range, line=dict(color="#e3b341", dash="dash", width=1.5),
                            annotation_text=f"Mission requirement {eng_range} km",
                            annotation_font=dict(color="#e3b341", family="Courier New", size=10))
        fig_hist.add_vline(x=mc["p10"], line=dict(color="#58a6ff", dash="dot", width=1),
                            annotation_text=f"P10={mc['p10']:.2f}km",
                            annotation_font=dict(color="#58a6ff", family="Courier New", size=9))
        fig_hist.add_vline(x=mc["p50"], line=dict(color="#8b949e", dash="dot", width=1),
                            annotation_text=f"P50={mc['p50']:.2f}km",
                            annotation_font=dict(color="#8b949e", family="Courier New", size=9))
        fig_hist.update_layout(
            title=dict(text="Burn-Through Distribution (N=5000 MC)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Burn-through range (km)", gridcolor="#21262d"),
            yaxis=dict(title="Count", gridcolor="#21262d"),
            height=250, **_L,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        # Key metrics
        m1, m2, m3, m4 = st.columns(4)
        risk_color = "normal" if pm_now >= conf_target / 100 else "inverse"
        m1.metric("P(mission success)", f"{pm_now:.0%}", delta_color=risk_color)
        m2.metric("Confidence target",  f"{conf_target}%")
        m3.metric("P10 burn-through",   f"{mc['p10']:.2f} km")
        m4.metric("P90 burn-through",   f"{mc['p90']:.2f} km")

        if pm_now < conf_target / 100:
            min_erp = min_erp_for_confidence(
                r_erp, rcs, mode, conf_target / 100, eng_range, sj, sr, src
            )
            gap = min_erp - j_erp
            st.error(
                f"⚠ Current jammer ERP ({j_erp} dBW) achieves only {pm_now:.0%} — "
                f"below the {conf_target}% target. "
                f"Required ERP: **{min_erp:.1f} dBW** (+{gap:.1f} dB). "
                "Write this as the kravspec minimum, not the nominal."
            )
        else:
            st.success(
                f"Current jammer ERP meets the {conf_target}% confidence target "
                f"at {pm_now:.0%} P(burn-through < {eng_range} km)."
            )

        # Sensitivity
        st.subheader("Parameter Sensitivity")
        sens = sensitivity_analysis(j_erp, r_erp, rcs, mode, sj, sr, src)
        import pandas as pd
        st.dataframe(pd.DataFrame(sens), use_container_width=True, hide_index=True)

        # Lifecycle forecast
        st.subheader("Lifecycle Forecast")
        lc = lifecycle_forecast(j_erp, r_erp, rcs, mode, threat_growth, jammer_growth,
                                 forecast_yrs, eng_range)
        fig_lc = go.Figure()
        fig_lc.add_trace(go.Scatter(
            x=lc["years"], y=[p * 100 for p in lc["p_success"]],
            mode="lines+markers", name="P(mission success) %",
            line=dict(color="#39d353", width=2), marker=dict(size=6),
        ))
        fig_lc.add_hline(y=conf_target, line=dict(color="#e3b341", dash="dash", width=1.5),
                          annotation_text=f"Target {conf_target}%",
                          annotation_font=dict(color="#e3b341", family="Courier New", size=10))
        if lc["fail_year"] is not None:
            fig_lc.add_vline(x=lc["fail_year"],
                              line=dict(color="#f85149", dash="dash", width=1.5),
                              annotation_text=f"Obsolescence year {lc['fail_year']}",
                              annotation_font=dict(color="#f85149", family="Courier New", size=10))
        fig_lc.update_layout(
            title=dict(text=f"P(success) over {forecast_yrs}-yr lifecycle "
                             f"(threat +{threat_growth}/jammer +{jammer_growth} dB/yr)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Years from procurement", gridcolor="#21262d"),
            yaxis=dict(title="P(mission success) %", gridcolor="#21262d", range=[0, 105]),
            height=260, **_L,
        )
        st.plotly_chart(fig_lc, use_container_width=True)

        if lc["fail_year"] is not None:
            st.warning(
                f"System becomes operationally marginal at year {lc['fail_year']} "
                f"under current threat growth assumptions. "
                "Kravspec should include a technology refresh clause or minimum ERP growth requirement."
            )
        else:
            st.success(
                f"System remains above the {conf_target}% threshold for the full "
                f"{forecast_yrs}-year forecast horizon."
            )
