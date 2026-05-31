"""
Threat evolution trajectory 2025-2035.

Projects burn-through range as threat radar capabilities grow along published
open-source trend lines. Overlays the procurement horizon for a candidate system.
Answers: will this system still be adequate when it reaches FOC?
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

THREAT_PROFILES = {
    "Russian S-400 / S-500 upgrade path": {
        "erp_2025": 55,
        "erp_annual_growth_db": 1.2,
        "rcs_improvement_db_pa": 0.0,
        "description": "Continuing Russian S-400 / S-500 upgrade programme. "
                        "ERP growth driven by solid-state transmitter improvements. "
                        "~1.2 dB/year based on open-source reporting.",
    },
    "Chinese HQ-9 / HQ-22 family": {
        "erp_2025": 53,
        "erp_annual_growth_db": 1.0,
        "rcs_improvement_db_pa": 0.0,
        "description": "Chinese HQ-9B / HQ-22 upgrade trajectory. "
                        "Slightly slower development cycle than Russian. "
                        "~1.0 dB/year ERP growth estimate.",
    },
    "Near-peer hypothetical (pessimistic)": {
        "erp_2025": 52,
        "erp_annual_growth_db": 2.0,
        "rcs_improvement_db_pa": 0.0,
        "description": "Pessimistic upper bound: adversary adopts AESA upgrades "
                        "at accelerated pace. 2 dB/year ERP growth. "
                        "Use for stress-testing requirements.",
    },
}

PLATFORM_PROFILES = {
    "F-35A (AN/ASQ-239 Barracuda)": {"rcs": -15, "jammer_erp_2025": 25, "jammer_upgrade_db": 0},
    "Legacy fighter (~5 dBsm)":     {"rcs":   5, "jammer_erp_2025": 20, "jammer_upgrade_db": 0},
    "EF-2000 Typhoon":              {"rcs":   0, "jammer_erp_2025": 22, "jammer_upgrade_db": 0},
}

THREAT_MODES = {"Barrage": -10, "Spot": 0, "Sweep": -5}


@st.cache_data
def compute_trajectory(
    threat_key: str,
    platform_key: str,
    jammer_upgrade_year: int,
    jammer_upgrade_db: float,
    engagement_range_km: float,
    threat_mode: str,
) -> dict:
    profile  = THREAT_PROFILES[threat_key]
    platform = PLATFORM_PROFILES[platform_key]
    mode_penalty = THREAT_MODES[threat_mode]
    r_m = engagement_range_km * 1e3
    years = np.arange(2025, 2036)

    threat_erps = np.array([
        profile["erp_2025"] + profile["erp_annual_growth_db"] * (y - 2025)
        for y in years
    ])

    jammer_erps = np.array([
        platform["jammer_erp_2025"] + (jammer_upgrade_db if y >= jammer_upgrade_year else 0)
        for y in years
    ])

    rcs = platform["rcs"]

    js_trajectory = (
        jammer_erps + mode_penalty - threat_erps
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(r_m)
        - rcs
    )

    bt_trajectory = (
        10 ** ((threat_erps - jammer_erps - mode_penalty + rcs - 10 * np.log10(4 * np.pi)) / 20)
        / 1e3
    )

    obsolete_year = None
    for i, (y, js) in enumerate(zip(years, js_trajectory)):
        if js < 0:
            obsolete_year = int(y)
            break

    return {
        "years":          years,
        "js_trajectory":  js_trajectory,
        "bt_trajectory":  bt_trajectory,
        "threat_erps":    threat_erps,
        "jammer_erps":    jammer_erps,
        "obsolete_year":  obsolete_year,
    }


def render():
    st.header("Threat Evolution Trajectory 2025–2035")
    st.caption(
        "Projects J/S and burn-through range as threat radar ERP grows along open-source trend lines. "
        "Overlays the system procurement horizon. "
        "Answers the procurement officer's question: will this system still be adequate at FOC?"
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        threat_key   = st.selectbox("Threat profile", list(THREAT_PROFILES.keys()))
        platform_key = st.selectbox("Friendly platform", list(PLATFORM_PROFILES.keys()))
        threat_mode  = st.selectbox("Jamming mode", list(THREAT_MODES.keys()), index=1)
        engagement_range = st.slider("Engagement range (km)", 20, 200, 80, 5)

        st.markdown("**Procurement horizon**")
        foc_year = st.slider(
            "System FOC year", 2026, 2035, 2030, 1,
            help="Full Operational Capability year for the candidate system.",
        )
        service_life = st.slider("Service life (years)", 5, 20, 15, 1)
        eol_year = foc_year + service_life

        st.markdown("**Jammer upgrade option**")
        upgrade_year = st.slider("Upgrade ERP (year)", 2025, 2035, 2030, 1)
        upgrade_db   = st.slider("Upgrade ERP gain (dB)", 0, 10, 0, 1,
                                 help="ERP improvement from a planned mid-life upgrade.")

        st.caption(THREAT_PROFILES[threat_key]["description"])

    res = compute_trajectory(
        threat_key, platform_key, upgrade_year, upgrade_db,
        engagement_range, threat_mode,
    )

    with col_b:
        years    = res["years"]
        js_traj  = res["js_trajectory"]
        bt_traj  = res["bt_trajectory"]
        obsolete = res["obsolete_year"]

        # J/S trajectory
        fig = go.Figure()
        line_colors = ["#39d353" if v >= 0 else "#f85149" for v in js_traj]

        fig.add_trace(go.Scatter(
            x=years, y=js_traj,
            mode="lines+markers",
            line=dict(color="#39d353", width=2),
            marker=dict(
                color=["#39d353" if v >= 0 else "#f85149" for v in js_traj],
                size=8,
            ),
            name="J/S (dB)",
        ))

        shapes, annotations = [], []

        # Zero dB threshold
        shapes.append(dict(
            type="line", x0=years[0], x1=years[-1], y0=0, y1=0,
            line=dict(color="#8b949e", dash="dot", width=1),
        ))

        # FOC band
        shapes.append(dict(
            type="rect",
            x0=foc_year, x1=min(eol_year, years[-1]), y0=min(js_traj) - 2, y1=max(js_traj) + 2,
            fillcolor="rgba(88,166,255,0.06)",
            line=dict(color="#58a6ff", width=0.5, dash="dot"),
        ))
        annotations.append(dict(
            x=foc_year + (min(eol_year, years[-1]) - foc_year) / 2,
            y=max(js_traj) * 0.85,
            text=f"Service life<br>({foc_year}–{min(eol_year, years[-1])})",
            showarrow=False,
            font=dict(color="#58a6ff", family="Courier New", size=9),
        ))

        if obsolete and foc_year <= obsolete <= eol_year:
            shapes.append(dict(
                type="line", x0=obsolete, x1=obsolete,
                y0=min(js_traj) - 2, y1=max(js_traj) + 2,
                line=dict(color="#f85149", dash="dash", width=2),
            ))
            annotations.append(dict(
                x=obsolete, y=0,
                text=f"Obsolescence<br>{obsolete}",
                showarrow=True, arrowhead=2, arrowcolor="#f85149",
                font=dict(color="#f85149", family="Courier New", size=10),
                ay=-30,
            ))

        if upgrade_db > 0:
            shapes.append(dict(
                type="line", x0=upgrade_year, x1=upgrade_year,
                y0=min(js_traj) - 2, y1=max(js_traj) + 2,
                line=dict(color="#e3b341", dash="dash", width=1.5),
            ))
            annotations.append(dict(
                x=upgrade_year, y=max(js_traj) * 0.6,
                text=f"+{upgrade_db} dB upgrade",
                showarrow=False,
                font=dict(color="#e3b341", family="Courier New", size=9),
            ))

        fig.update_layout(
            title=dict(text="J/S Trajectory vs Threat Evolution",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Year", gridcolor="#21262d",
                       tickvals=list(years), ticktext=[str(y) for y in years]),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
            shapes=shapes, annotations=annotations,
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ERP growth table
        fig_erp = go.Figure()
        fig_erp.add_trace(go.Scatter(
            x=years, y=res["threat_erps"],
            mode="lines+markers", name="Threat ERP (dBW)",
            line=dict(color="#f85149", width=2), marker=dict(size=5),
        ))
        fig_erp.add_trace(go.Scatter(
            x=years, y=res["jammer_erps"],
            mode="lines+markers", name="Jammer ERP (dBW)",
            line=dict(color="#39d353", width=2), marker=dict(size=5),
        ))
        fig_erp.update_layout(
            title=dict(text="ERP Trajectories",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(gridcolor="#21262d",
                       tickvals=list(years), ticktext=[str(y) for y in years]),
            yaxis=dict(title="ERP (dBW)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=50, b=50), height=200,
        )
        st.plotly_chart(fig_erp, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        js_at_foc = float(js_traj[list(years).index(foc_year)] if foc_year in years else js_traj[-1])
        m1.metric("J/S at FOC year", f"{js_at_foc:.1f} dB")
        if obsolete:
            within = foc_year <= obsolete <= eol_year
            m2.metric(
                "Jammer obsolescence year", str(obsolete),
                delta="⚠ within service life" if within else "beyond service life",
                delta_color="inverse" if within else "normal",
            )
        else:
            m2.metric("Jammer obsolescence", "Beyond 2035")
        m3.metric("J/S degradation 2025→2035",
                  f"{js_traj[-1] - js_traj[0]:.1f} dB")

        if obsolete and foc_year <= obsolete <= eol_year:
            st.error(
                f"⚠ System becomes ineffective against this threat in **{obsolete}** — "
                f"{obsolete - foc_year} years into its service life. "
                f"Either require higher jammer ERP in the kravspecifikation, "
                f"or plan a mid-life upgrade at year {upgrade_year}.",
            )
        elif js_at_foc < 3:
            st.warning(
                f"J/S margin at FOC is only {js_at_foc:.1f} dB — "
                "within uncertainty of open-source threat parameters. "
                "A kravspecifikation written against nominal figures may be inadequate by delivery.",
            )
        else:
            st.success(
                f"System maintains positive J/S throughout service life against this threat profile. "
                f"Margin at FOC: {js_at_foc:.1f} dB.",
            )
