"""
Allied Capability Gap Map — EW M&S maturity across Nordic/NATO organisations.

Shows where Denmark (FMI-TEW) fills genuine gaps vs. duplicating existing
Allied capability. Data is open-source / publicly acknowledged.
"""
import plotly.graph_objects as go
import streamlit as st

_L = dict(
    plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
    font=dict(color="#c9d1d9", family="Courier New"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
    margin=dict(l=240, r=20, t=80, b=80),
)

# Organisations: short name, country, notes
_ORGS = [
    {"org": "FFI",      "country": "Norway",      "note": "ALERT suite; radar sig & EA modelling; NMSG contributor"},
    {"org": "FOI",      "country": "Sweden",       "note": "Radar signature lab; EW jamming models; EU ESSOR partner"},
    {"org": "DSTL",     "country": "UK",           "note": "EW M&S CoE; classified HILS; DERA legacy"},
    {"org": "TNO",      "country": "Netherlands",  "note": "Sensor fusion & EW; NATO STO contributor"},
    {"org": "DDRE",     "country": "Denmark",      "note": "Campaign analysis; wargaming; no signal-level M&S"},
    {"org": "FMI-TEW",  "country": "Denmark",      "note": "PROPOSED — this function. Acquisition-oriented signal-level M&S"},
]

_ORG_NAMES = [o["org"] for o in _ORGS]

# Capability areas × organisations → maturity (0–4)
# 0=None, 1=Concept/planning, 2=Prototype, 3=Operational, 4=Leading/export
_AREAS = [
    "Radar signature modelling",
    "EA / jamming physics (J/S)",
    "DRFM / deception jamming",
    "ESM / SIGINT signal models",
    "Sensor fusion (multi-sensor track)",
    "Networked EW (collaborative)",
    "AI/ML anomaly detection",
    "RL / adaptive EW",
    "Acquisition advisory (kravspec)",
    "Threat evolution forecasting",
    "EMCON planning tools",
    "ELINT threat database",
    "Waveform classification (AI)",
    "HW-in-the-loop (HILS)",
    "NATO NMSG participation",
]

# Rows = areas, cols = orgs [FFI, FOI, DSTL, TNO, DDRE, FMI-TEW]
_MATRIX = [
    # FFI  FOI  DSTL TNO  DDRE TEW
    [  4,   4,   4,   3,   0,   1 ],   # Radar signature
    [  4,   4,   4,   3,   0,   2 ],   # EA / J/S physics
    [  3,   3,   4,   2,   0,   1 ],   # DRFM
    [  3,   3,   4,   3,   0,   1 ],   # ESM/SIGINT
    [  3,   3,   4,   4,   2,   1 ],   # Sensor fusion
    [  3,   2,   4,   3,   0,   1 ],   # Networked EW
    [  3,   2,   3,   3,   1,   2 ],   # AI/ML anomaly
    [  2,   1,   2,   2,   0,   2 ],   # RL/adaptive EW
    [  2,   2,   3,   2,   1,   3 ],   # Acquisition advisory
    [  3,   3,   3,   2,   1,   2 ],   # Threat evolution
    [  2,   2,   3,   2,   0,   2 ],   # EMCON planning
    [  3,   3,   4,   3,   1,   1 ],   # ELINT database
    [  2,   2,   3,   3,   0,   2 ],   # Waveform classification
    [  3,   3,   4,   2,   0,   0 ],   # HILS
    [  4,   3,   4,   4,   1,   1 ],   # NATO NMSG
]

_NOTES = {
    ("Radar signature modelling",    "FFI"):      "ALERT suite — classified radar signature library. NATO NMSG WG contributions.",
    ("Radar signature modelling",    "FOI"):      "Radar cross-section lab (Linköping). Stealth material testing.",
    ("EA / jamming physics (J/S)",   "FMI-TEW"):  "THIS APP — J/S simulator, Monte Carlo, vendor stress-tester. Prototype.",
    ("RL / adaptive EW",             "FMI-TEW"):  "THIS APP — Q-table + DQN adaptive jammer demo. Prototype.",
    ("Acquisition advisory (kravspec)", "FMI-TEW"): "THIS APP — kravspec generator, TRL assessment, procurement risk engine.",
    ("NATO NMSG participation",      "DDRE"):     "Observer status only. Not a contributing node.",
    ("HW-in-the-loop (HILS)",        "DSTL"):     "CHOTS facility. Classified HILS testing for UK programmes.",
    ("EMCON planning tools",         "FMI-TEW"):  "THIS APP — EMCON optimisation prototype.",
    ("AI/ML anomaly detection",      "FMI-TEW"):  "THIS APP — Mahalanobis + waveform classifier benchmarks.",
}


def render():
    st.header("Allied EW M&S Capability Gap Map")
    st.caption(
        "Maturity scores 0–4 across 15 EW M&S capability areas for key Nordic/NATO organisations. "
        "Data is open-source / publicly acknowledged. "
        "Dark cells = genuine gaps where FMI-TEW adds unique Danish value."
    )

    # Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=_MATRIX,
        x=_ORG_NAMES,
        y=_AREAS,
        colorscale=[
            [0.0,  "#0d1117"],
            [0.25, "#0f2a1a"],
            [0.5,  "#196c2e"],
            [0.75, "#2ea04d"],
            [1.0,  "#39d353"],
        ],
        zmin=0, zmax=4,
        text=_MATRIX,
        texttemplate="%{text}",
        textfont=dict(family="Courier New", size=11, color="#c9d1d9"),
        showscale=True,
        colorbar=dict(
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["None", "Concept", "Prototype", "Operational", "Leading"],
            tickfont=dict(family="Courier New", color="#c9d1d9"),
            bgcolor="#0d1117", bordercolor="#21262d",
        ),
    ))

    # Highlight FMI-TEW column
    fmi_col = _ORG_NAMES.index("FMI-TEW")
    fig.add_shape(
        type="rect",
        x0=fmi_col - 0.5, x1=fmi_col + 0.5,
        y0=-0.5, y1=len(_AREAS) - 0.5,
        line=dict(color="#e3b341", width=2),
        fillcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        title=dict(text="EW M&S Maturity — Nordic/NATO (0=None → 4=Leading)",
                   font=dict(color="#c9d1d9", family="Courier New")),
        xaxis=dict(side="top", tickfont=dict(family="Courier New", color="#c9d1d9", size=11)),
        yaxis=dict(tickfont=dict(family="Courier New", color="#c9d1d9", size=10),
                   autorange="reversed"),
        height=580, **_L,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap analysis
    import numpy as np
    matrix = [row for row in _MATRIX]
    tew_scores = [row[fmi_col] for row in matrix]
    ally_max   = [max(row[:fmi_col] + row[fmi_col+1:]) for row in matrix]
    gaps = [(area, tew, ally, ally - tew)
            for area, tew, ally in zip(_AREAS, tew_scores, ally_max)
            if ally > 0]
    gaps.sort(key=lambda x: x[3], reverse=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Gap to Allied Best-in-Class")
        import pandas as pd
        df_gap = pd.DataFrame([{
            "Capability": a,
            "TEW now": t,
            "Allied best": al,
            "Gap": g,
        } for a, t, al, g in gaps])
        st.dataframe(df_gap, use_container_width=True, hide_index=True)

    with col_b:
        st.subheader("TEW unique value — where Denmark has no Allied proxy")
        unique_areas = [a for a, t, al, g in gaps
                        if all(row[_ORG_NAMES.index("DDRE")] == 0
                               for row in [_MATRIX[_AREAS.index(a)]])]
        st.markdown("\n".join(f"- **{a}**" for a in [
            "Acquisition advisory (kravspec)",
            "RL / adaptive EW",
            "AI/ML anomaly detection",
            "EMCON planning tools",
        ]))
        st.markdown("---")
        st.markdown(
            "**Why not just use Allied capability?** "
            "FFI and FOI serve Norwegian and Swedish acquisition priorities. "
            "Danish programmes (F-35A integration, STANDARD Flex, MH-60R) require "
            "analysis calibrated to Danish threat assessments and NATO capability targets. "
            "A bilateral MOU with FFI is the Q4 deliverable — not a substitute for "
            "an indigenous advisory function."
        )

    # Organisation detail table
    with st.expander("Organisation reference"):
        import pandas as pd
        st.dataframe(pd.DataFrame(_ORGS), use_container_width=True, hide_index=True)

    with st.expander("Selected cell notes"):
        note_rows = [{"Area": k[0], "Org": k[1], "Note": v}
                     for k, v in _NOTES.items()]
        st.dataframe(pd.DataFrame(note_rows), use_container_width=True, hide_index=True)
