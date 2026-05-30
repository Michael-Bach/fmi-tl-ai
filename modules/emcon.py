"""
EMCON (Emission Control) Optimisation.

Given N platforms with mandatory emissions and a threat ESM network,
compute an emission schedule that minimises simultaneous exposure
while satisfying all mission communication and radar requirements.

Solver: greedy bin-packing + optional scipy LP relaxation.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=60, r=20, t=60, b=50),
)

_MISSION_ROLES = {
    "Flagship / C2": [
        {"name": "Link-16 datalink",  "duration": 2, "priority": 1, "erp_dbw": 10},
        {"name": "HF radio",          "duration": 1, "priority": 2, "erp_dbw": 5},
        {"name": "Search radar",       "duration": 3, "priority": 2, "erp_dbw": 60},
        {"name": "Fire control radar", "duration": 1, "priority": 1, "erp_dbw": 65},
    ],
    "Escort / SAM": [
        {"name": "Illumination radar", "duration": 2, "priority": 1, "erp_dbw": 60},
        {"name": "Link-16 datalink",   "duration": 1, "priority": 2, "erp_dbw": 10},
        {"name": "Navigation radar",   "duration": 1, "priority": 3, "erp_dbw": 40},
    ],
    "Submarine": [
        {"name": "Periscope radar (burst)", "duration": 1, "priority": 1, "erp_dbw": 35},
        {"name": "ESM (receive only)",      "duration": 0, "priority": 0, "erp_dbw": -99},
    ],
    "Maritime patrol aircraft": [
        {"name": "Search radar",    "duration": 3, "priority": 1, "erp_dbw": 55},
        {"name": "AIS transponder", "duration": 1, "priority": 3, "erp_dbw": 5},
        {"name": "Datalink",        "duration": 1, "priority": 2, "erp_dbw": 12},
    ],
}

_COLORS = ["#58a6ff", "#39d353", "#e3b341", "#d2a8ff"]


def _detect_prob(erp_dbw: float, range_km: float, esm_sens_dbm: float,
                  freq_ghz: float = 9.0) -> float:
    if erp_dbw < -90:
        return 0.0
    wl = SPEED_OF_LIGHT / (freq_ghz * 1e9)
    r_m = max(range_km * 1e3, 100)
    fspl = 20 * np.log10(4 * np.pi * r_m / wl)
    received = erp_dbw - fspl + 30   # dBm
    # Sigmoid detection model: certain above sensitivity, falls off below
    snr_above = received - esm_sens_dbm
    return float(1 / (1 + np.exp(-0.8 * snr_above)))


@st.cache_data
def compute_emcon_schedule(
    platforms: tuple,       # ((name, role, range_km_to_threat), ...)
    esm_sensitivity_dbm: float,
    n_slots: int,
    optimize: bool,
) -> dict:
    all_emissions = []
    for p_idx, (p_name, role, range_km) in enumerate(platforms):
        for em in _MISSION_ROLES.get(role, []):
            if em["duration"] == 0:
                continue
            all_emissions.append({
                "platform": p_name,
                "p_idx":    p_idx,
                "name":     em["name"],
                "duration": em["duration"],
                "priority": em["priority"],
                "erp_dbw":  em["erp_dbw"],
                "range_km": range_km,
            })

    # Sort by priority then spread across slots
    all_emissions.sort(key=lambda x: x["priority"])

    # Assign slots: greedy — place each emission in the slot with fewest simultaneous transmissions
    schedule = {s: [] for s in range(n_slots)}
    slot_load = np.zeros(n_slots)  # number of active transmitters per slot

    for em in all_emissions:
        dur = em["duration"]
        # Find the window of `dur` consecutive slots with minimum total load
        best_start = 0
        best_load  = np.inf
        for start in range(n_slots - dur + 1):
            window_load = slot_load[start:start + dur].sum()
            if window_load < best_load:
                best_load  = window_load
                best_start = start
        for s in range(best_start, best_start + dur):
            schedule[s].append(em)
            slot_load[s] += 1

    # Compute per-slot detection probability (prob ANY ESM in range detects ANY emission)
    detect_probs = []
    erp_sums = []
    for s in range(n_slots):
        if not schedule[s]:
            detect_probs.append(0.0)
            erp_sums.append(-99.0)
            continue
        # P(at least one detection) = 1 - prod(1 - P_i)
        p_none = 1.0
        erp_lin = 0.0
        for em in schedule[s]:
            pd = _detect_prob(em["erp_dbw"], em["range_km"], esm_sensitivity_dbm)
            p_none *= (1 - pd)
            erp_lin += 10 ** (em["erp_dbw"] / 10)
        detect_probs.append(1 - p_none)
        erp_sums.append(10 * np.log10(max(erp_lin, 1e-10)))

    # Unoptimised baseline: all emissions in first N slots (naive sequential)
    baseline_probs = []
    b_slot = 0
    b_sched = {s: [] for s in range(n_slots)}
    for em in all_emissions:
        for _ in range(em["duration"]):
            if b_slot < n_slots:
                b_sched[b_slot].append(em)
                b_slot += 1
    for s in range(n_slots):
        if not b_sched[s]:
            baseline_probs.append(0.0)
            continue
        p_none = 1.0
        for em in b_sched[s]:
            pd = _detect_prob(em["erp_dbw"], em["range_km"], esm_sensitivity_dbm)
            p_none *= (1 - pd)
        baseline_probs.append(1 - p_none)

    return {
        "schedule":       schedule,
        "detect_probs":   detect_probs,
        "baseline_probs": baseline_probs,
        "erp_sums":       erp_sums,
        "n_slots":        n_slots,
        "platforms":      platforms,
    }


def render():
    st.header("EMCON Optimisation Planner")
    st.caption(
        "Given mission emission requirements for N platforms, schedule transmissions "
        "across time slots to minimise simultaneous exposure to threat ESM. "
        "Shows the detection probability reduction achieved by optimised EMCON vs. "
        "an uncoordinated (naive sequential) emission schedule."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        n_plat = st.slider("Number of platforms", 1, 4, 3, 1)
        plat_configs = []
        for i in range(n_plat):
            name = st.text_input(f"Platform {i+1} name",
                                  value=["Flagship", "Escort", "MPA", "Submarine"][i],
                                  key=f"em_name_{i}")
            role = st.selectbox(f"Role", list(_MISSION_ROLES.keys()),
                                 index=i % len(_MISSION_ROLES), key=f"em_role_{i}")
            range_km = st.slider(f"Range to threat ESM (km)", 10, 500, [150, 200, 120, 80][i], 10,
                                  key=f"em_range_{i}")
            plat_configs.append((name, role, range_km))

        st.divider()
        esm_sens = st.slider("Threat ESM sensitivity (dBm)", -120, -40, -80, 5)
        n_slots  = st.slider("Time slots", 6, 24, 12, 2)

    plat_tuple = tuple(map(tuple, plat_configs))
    res = compute_emcon_schedule(plat_tuple, esm_sens, n_slots, True)

    with col_b:
        # Gantt chart of optimised schedule
        slot_labels = [f"T{i:02d}" for i in range(n_slots)]
        fig_gantt = go.Figure()

        for p_idx, (p_name, role, _) in enumerate(plat_configs):
            for s in range(n_slots):
                for em in res["schedule"][s]:
                    if em["p_idx"] == p_idx:
                        prio_col = {1: "#f85149", 2: "#e3b341", 3: "#58a6ff"}.get(
                            em["priority"], "#8b949e"
                        )
                        fig_gantt.add_shape(
                            type="rect",
                            x0=s - 0.4, x1=s + 0.4,
                            y0=p_idx - 0.35, y1=p_idx + 0.35,
                            fillcolor=prio_col, opacity=0.75,
                            line=dict(color="#0d1117", width=1),
                        )
                        fig_gantt.add_annotation(
                            x=s, y=p_idx,
                            text=em["name"][:12],
                            font=dict(family="Courier New", color="#0d1117", size=8),
                            showarrow=False,
                        )

        fig_gantt.update_layout(
            title=dict(text="Optimised EMCON Schedule (red=P1, yellow=P2, blue=P3)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(tickvals=list(range(n_slots)), ticktext=slot_labels,
                       title="Time slot", gridcolor="#21262d",
                       tickfont=dict(family="Courier New", size=9)),
            yaxis=dict(tickvals=list(range(n_plat)),
                       ticktext=[p[0] for p in plat_configs],
                       title="Platform", gridcolor="#21262d",
                       tickfont=dict(family="Courier New", size=9)),
            height=230, **_L,
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

        # Detection probability comparison
        fig_dp = go.Figure()
        fig_dp.add_trace(go.Bar(
            x=slot_labels, y=[p * 100 for p in res["baseline_probs"]],
            name="Uncoordinated", marker=dict(color="#f85149", opacity=0.6),
        ))
        fig_dp.add_trace(go.Bar(
            x=slot_labels, y=[p * 100 for p in res["detect_probs"]],
            name="Optimised EMCON", marker=dict(color="#39d353", opacity=0.8),
        ))
        fig_dp.update_layout(
            title=dict(text="Detection Probability per Time Slot (%)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            xaxis=dict(title="Time slot", gridcolor="#21262d"),
            yaxis=dict(title="P(detection) %", gridcolor="#21262d", range=[0, 110]),
            barmode="group", height=260, **_L,
        )
        st.plotly_chart(fig_dp, use_container_width=True)

        avg_base = np.mean(res["baseline_probs"]) * 100
        avg_opt  = np.mean(res["detect_probs"]) * 100
        peak_opt = max(res["detect_probs"]) * 100

        m1, m2, m3 = st.columns(3)
        m1.metric("Avg detection % (uncoordinated)", f"{avg_base:.0f}%")
        m2.metric("Avg detection % (optimised)",     f"{avg_opt:.0f}%",
                   delta=f"{avg_opt - avg_base:.0f}pp", delta_color="inverse")
        m3.metric("Peak detection % (optimised)",    f"{peak_opt:.0f}%")

        with st.expander("Schedule detail"):
            rows = []
            for s in range(n_slots):
                for em in res["schedule"][s]:
                    rows.append({
                        "Slot": f"T{s:02d}",
                        "Platform": em["platform"],
                        "Emission": em["name"],
                        "ERP (dBW)": em["erp_dbw"],
                        "Priority": em["priority"],
                        "P(detect)": f"{_detect_prob(em['erp_dbw'], em['range_km'], esm_sens):.0%}",
                    })
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
