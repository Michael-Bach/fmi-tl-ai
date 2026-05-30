"""
Scenario Library — save, load, compare, and export J/S simulation scenarios.

Scenarios are persisted to data/scenarios.json so they survive restarts.
Any two saved scenarios can be compared side-by-side with delta metrics,
and a structured comparison brief can be exported as markdown.
"""
import datetime
import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

_SCENARIOS_PATH = Path(__file__).parent.parent / "data" / "scenarios.json"

SPEED_OF_LIGHT = 3e8
THREAT_MODES   = {"Barrage": -10, "Spot": 0, "Sweep": -5}

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)


def _load_scenarios() -> dict:
    if _SCENARIOS_PATH.exists():
        try:
            return json.loads(_SCENARIOS_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_scenarios(data: dict):
    _SCENARIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SCENARIOS_PATH.write_text(json.dumps(data, indent=2))


def _compute_metrics(p: dict) -> dict:
    pen  = THREAT_MODES[p["threat_mode"]]
    r_m  = np.linspace(1, p["max_range_km"] * 1e3, 500)
    js   = (p["jammer_erp_dbw"] + pen - p["radar_erp_dbw"]
            + 10 * np.log10(4 * np.pi) + 20 * np.log10(r_m) - p["rcs_dbsm"])
    exp  = (p["radar_erp_dbw"] - p["jammer_erp_dbw"] - pen
            + p["rcs_dbsm"] - 10 * np.log10(4 * np.pi)) / 20
    bt   = (10 ** exp) / 1e3
    wl   = SPEED_OF_LIGHT / (p["radar_freq_ghz"] * 1e9)
    r_esm_m = 10 ** ((p["jammer_erp_dbw"] + pen + 30
                       - p["esm_sensitivity_dbm"]
                       - 20 * np.log10(4 * np.pi / wl)) / 20)
    esm  = r_esm_m / 1e3

    # Monte Carlo
    rng  = np.random.default_rng(42)
    j_s  = p["jammer_erp_dbw"] + rng.normal(0, 1.5, 2000)
    r_s  = p["radar_erp_dbw"]  + rng.normal(0, 1.0, 2000)
    rc_s = p["rcs_dbsm"]       + rng.normal(0, 1.5, 2000)
    exp_mc = (r_s - j_s - pen + rc_s - 10 * np.log10(4 * np.pi)) / 20
    bt_mc  = (10 ** exp_mc) / 1e3

    return {
        "ranges_km":      r_m / 1e3,
        "js_db":          js,
        "burn_through_km": float(bt),
        "esm_km":         float(esm),
        "js_at_max":      float(js[-1]),
        "bt_p10":         float(np.percentile(bt_mc, 10)),
        "bt_p50":         float(np.percentile(bt_mc, 50)),
        "bt_p90":         float(np.percentile(bt_mc, 90)),
    }


def _metric_delta(a: float, b: float, higher_is_better: bool = True) -> str:
    d = a - b
    sign = "+" if d >= 0 else ""
    arrow = "↑" if (d > 0) == higher_is_better else "↓"
    return f"{sign}{d:.2f} {arrow}"


def _export_comparison(name_a: str, name_b: str,
                        p_a: dict, p_b: dict,
                        m_a: dict, m_b: dict) -> str:
    d = datetime.date.today().isoformat()
    lines = [
        f"# EW Scenario Comparison — {name_a} vs {name_b}",
        f"**Generated:** {d}  |  **Classification:** IKKE-KLASSIFICERET",
        "",
        "## Parameters",
        "| Parameter | " + name_a + " | " + name_b + " |",
        "|-----------|---------|---------|",
    ]
    for key, label in [
        ("jammer_erp_dbw", "Jammer ERP (dBW)"),
        ("radar_erp_dbw",  "Radar ERP (dBW)"),
        ("rcs_dbsm",       "Target RCS (dBsm)"),
        ("radar_freq_ghz", "Radar freq (GHz)"),
        ("esm_sensitivity_dbm", "ESM sensitivity (dBm)"),
        ("threat_mode",    "Jamming mode"),
    ]:
        lines.append(f"| {label} | {p_a.get(key, '—')} | {p_b.get(key, '—')} |")

    lines += [
        "",
        "## Key Results",
        "| Metric | " + name_a + " | " + name_b + " | Delta |",
        "|--------|---------|---------|-------|",
        f"| Burn-through (nom.) km | {m_a['burn_through_km']:.3f} | {m_b['burn_through_km']:.3f} "
        f"| {_metric_delta(m_a['burn_through_km'], m_b['burn_through_km'], False)} |",
        f"| BT P10 km | {m_a['bt_p10']:.2f} | {m_b['bt_p10']:.2f} "
        f"| {_metric_delta(m_a['bt_p10'], m_b['bt_p10'], False)} |",
        f"| BT P50 km | {m_a['bt_p50']:.2f} | {m_b['bt_p50']:.2f} "
        f"| {_metric_delta(m_a['bt_p50'], m_b['bt_p50'], False)} |",
        f"| ESM detection km | {m_a['esm_km']:.1f} | {m_b['esm_km']:.1f} "
        f"| {_metric_delta(m_a['esm_km'], m_b['esm_km'], False)} |",
        f"| J/S at max range dB | {m_a['js_at_max']:.1f} | {m_b['js_at_max']:.1f} "
        f"| {_metric_delta(m_a['js_at_max'], m_b['js_at_max'], True)} |",
        "",
        "## Acquisition Recommendation",
        f"Lower burn-through range is better (jammer is effective to closer range). "
        f"{'**' + name_a + '**' if m_a['bt_p10'] < m_b['bt_p10'] else '**' + name_b + '**'} "
        f"is preferred on the P10 (pessimistic) criterion.",
        "",
        "*Write kravspec requirements against the pessimistic (P10) case, not nominal.*",
    ]
    return "\n".join(lines)


def render():
    st.header("Scenario Library")
    st.caption(
        "Save named J/S simulation parameter sets, reload them, "
        "and compare any two scenarios side-by-side with delta metrics. "
        "Export a structured comparison brief for procurement decision packages."
    )

    db = _load_scenarios()

    # Save current scenario from J/S simulator
    st.subheader("Save current scenario")
    sim_params = st.session_state.get("sim_params", {})
    if sim_params:
        st.caption(
            f"Current J/S simulator: ERP {sim_params.get('jammer_erp_dbw')} dBW  "
            f"| Mode {sim_params.get('threat_mode')}  "
            f"| RCS {sim_params.get('rcs_dbsm')} dBsm"
        )
        sc1, sc2 = st.columns([3, 1])
        new_name = sc1.text_input("Scenario name", placeholder="e.g. F-35A vs SA-21 2031")
        if sc2.button("Save", type="primary") and new_name.strip():
            db[new_name.strip()] = {
                "params": sim_params,
                "saved": datetime.date.today().isoformat(),
            }
            _save_scenarios(db)
            st.success(f"Saved: {new_name.strip()}")
            st.rerun()
    else:
        st.info("Run the J/S Simulator (Simulation tab) first to populate parameters.")

    st.divider()

    if not db:
        st.info("No saved scenarios yet.")
        return

    # Saved scenarios table
    st.subheader(f"Saved scenarios ({len(db)})")
    import pandas as pd
    rows = [{
        "Name": name,
        "Saved": d["saved"],
        "Jammer ERP": d["params"].get("jammer_erp_dbw"),
        "Radar ERP":  d["params"].get("radar_erp_dbw"),
        "RCS (dBsm)": d["params"].get("rcs_dbsm"),
        "Mode":        d["params"].get("threat_mode"),
    } for name, d in db.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Delete scenario
    del_name = st.selectbox("Delete scenario", ["— select —"] + list(db.keys()), key="sc_del")
    if del_name != "— select —":
        if st.button(f"Delete '{del_name}'"):
            db.pop(del_name, None)
            _save_scenarios(db)
            st.rerun()

    st.divider()

    if len(db) < 2:
        st.info("Save at least two scenarios to enable comparison.")
        return

    # Comparison
    st.subheader("Scenario Comparison")
    names = list(db.keys())
    ca1, ca2 = st.columns(2)
    sel_a = ca1.selectbox("Scenario A", names, index=0, key="sc_a")
    sel_b = ca2.selectbox("Scenario B", names, index=min(1, len(names) - 1), key="sc_b")

    if sel_a == sel_b:
        st.warning("Select two different scenarios.")
        return

    p_a = db[sel_a]["params"]
    p_b = db[sel_b]["params"]
    m_a = _compute_metrics(p_a)
    m_b = _compute_metrics(p_b)

    # Overlay J/S curves
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m_a["ranges_km"], y=m_a["js_db"],
                              mode="lines", name=sel_a,
                              line=dict(color="#39d353", width=2)))
    fig.add_trace(go.Scatter(x=m_b["ranges_km"], y=m_b["js_db"],
                              mode="lines", name=sel_b,
                              line=dict(color="#58a6ff", width=2, dash="dash")))
    for m, name, color in [(m_a, sel_a, "#39d353"), (m_b, sel_b, "#58a6ff")]:
        if 0 < m["burn_through_km"] < max(p_a.get("max_range_km", 150), p_b.get("max_range_km", 150)):
            fig.add_vline(x=m["burn_through_km"],
                           line=dict(color=color, dash="dot", width=1),
                           annotation_text=f"BT {name[:12]}: {m['burn_through_km']:.1f}km",
                           annotation_font=dict(color=color, family="Courier New", size=9))
    fig.add_hline(y=0, line=dict(color="#8b949e", dash="dot", width=1))
    fig.update_layout(
        title=dict(text=f"J/S Overlay: {sel_a} vs {sel_b}",
                   font=dict(color="#c9d1d9", family="Courier New")),
        xaxis=dict(title="Range (km)", gridcolor="#21262d"),
        yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
        height=300, **_L,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Delta metrics table
    metrics = [
        ("Burn-through (nom.) km", m_a["burn_through_km"], m_b["burn_through_km"], False),
        ("BT P10 (pessimistic) km", m_a["bt_p10"],         m_b["bt_p10"],          False),
        ("BT P50 km",               m_a["bt_p50"],         m_b["bt_p50"],          False),
        ("ESM detection km",        m_a["esm_km"],         m_b["esm_km"],          False),
        ("J/S at max range dB",     m_a["js_at_max"],      m_b["js_at_max"],       True),
    ]
    met_rows = []
    for label, va, vb, hib in metrics:
        better = "A" if (va < vb) == (not hib) else "B"
        met_rows.append({
            "Metric": label,
            f"{sel_a}": f"{va:.2f}",
            f"{sel_b}": f"{vb:.2f}",
            "Delta (A−B)": f"{va - vb:+.2f}",
            "Better": f"← {sel_a}" if better == "A" else f"{sel_b} →",
        })
    st.dataframe(pd.DataFrame(met_rows), use_container_width=True, hide_index=True)

    brief = _export_comparison(sel_a, sel_b, p_a, p_b, m_a, m_b)
    st.download_button(
        "Download comparison brief (.md)",
        data=brief,
        file_name=f"comparison_{sel_a[:20].replace(' ', '_')}_vs_{sel_b[:20].replace(' ', '_')}.md",
        mime="text/markdown",
    )
