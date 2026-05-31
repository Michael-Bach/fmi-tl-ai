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

    st.divider()
    _render_allied_synthesis()


# ---------------------------------------------------------------------------
# LLM-powered allied contribution synthesis
# ---------------------------------------------------------------------------

_SYNTHESIS_PROMPT = """\
You are the Team Lead for AI, Modelling and Simulation at FMI TEW.

Below is the EW M&S capability maturity matrix for key Nordic/NATO organisations, \
scored 0 (None) to 4 (Leading/export-capable). FMI-TEW is the proposed Danish function.

Organisations: {org_names}
Capability areas: {areas}

Matrix (rows = areas, cols = orgs in same order):
{matrix_rows}

Using this data, produce a structured contribution strategy in JSON with this exact format:
{{
  "unique_contributions": [
    {{
      "area": "<capability area name>",
      "rationale": "<why Denmark has genuine non-duplicative value here (2–3 sentences)>",
      "priority": "high|medium|low"
    }}
  ],
  "bilateral_priorities": [
    {{
      "partner": "<org name>",
      "recommended_engagement": "<specific, actionable engagement recommendation>",
      "avoid": "<what not to duplicate from this partner>"
    }}
  ],
  "nmsg_recommendation": {{
    "lead_wg": "<one NMSG working group Denmark should aspire to lead>",
    "rationale": "<why Denmark is positioned to lead this>",
    "contribute_wgs": ["<WG 1>", "<WG 2>"]
  }},
  "strategic_summary": "<2–3 sentence plain-language summary for a programme manager>"
}}

Return ONLY the JSON object. No markdown fences, no other text.
"""


def _build_matrix_text() -> str:
    lines = []
    for i, area in enumerate(_AREAS):
        row_vals = " | ".join(
            f"{_ORG_NAMES[j]}:{_MATRIX[i][j]}" for j in range(len(_ORG_NAMES))
        )
        lines.append(f"  {area}: {row_vals}")
    return "\n".join(lines)


@st.cache_data(show_spinner=False)
def _call_synthesis_llm() -> dict:
    """Call Claude with cached context to synthesise Denmark's contribution strategy.
    Cached by st.cache_data so it only fires once per session."""
    import json
    import re
    from workflow.llm import get_native_client, CACHING_MODEL
    from workflow.context import get_cached_system_blocks

    client = get_native_client()
    prompt = _SYNTHESIS_PROMPT.format(
        org_names=", ".join(_ORG_NAMES),
        areas=", ".join(_AREAS),
        matrix_rows=_build_matrix_text(),
    )
    response = client.messages.create(
        model=CACHING_MODEL,
        max_tokens=2048,
        system=get_cached_system_blocks(),
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    # Parse JSON
    try:
        return json.loads(text), response.usage
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group()), response.usage
            except Exception:
                pass
    return {}, response.usage


def _render_allied_synthesis():
    st.subheader("Allied Contribution Strategy — AI Synthesis")
    st.caption(
        "LLM-synthesised analysis of where Denmark can make unique, non-duplicative "
        "contributions to Nordic/NATO EW M&S, based on the capability matrix above. "
        "Model: claude-sonnet-4-6 with prompt caching."
    )

    if st.button("Generate contribution strategy", key="gap_synthesis_btn"):
        with st.spinner("Analysing matrix with Claude…"):
            result, usage = _call_synthesis_llm()

        if not result:
            st.error("Could not parse synthesis output.")
            return

        cache_read = getattr(usage, "cache_read_input_tokens", 0)
        col_u1, col_u2 = st.columns(2)
        col_u1.metric("Input tokens", f"{usage.input_tokens:,}")
        col_u2.metric("Cache read", f"{cache_read:,}",
                      help="Context served from prompt cache")

        # Strategic summary
        summary = result.get("strategic_summary", "")
        if summary:
            st.info(f"**Strategic summary:** {summary}")

        col_a, col_b = st.columns(2)

        # Unique contributions
        with col_a:
            st.markdown("#### Unique Danish Contributions")
            for uc in result.get("unique_contributions", []):
                priority = uc.get("priority", "medium")
                badge_color = {"high": "#e3b341", "medium": "#58a6ff", "low": "#8b949e"}.get(
                    priority, "#8b949e"
                )
                st.markdown(
                    f"<div style='background:#161b22; padding:10px; margin-bottom:8px; "
                    f"border-radius:4px; border-left:3px solid {badge_color};'>"
                    f"<b>{uc.get('area', '—')}</b> "
                    f"<span style='color:{badge_color}; font-size:11px;'>"
                    f"[{priority.upper()}]</span><br>"
                    f"<span style='font-size:13px;'>{uc.get('rationale', '')}</span></div>",
                    unsafe_allow_html=True,
                )

        # Bilateral priorities
        with col_b:
            st.markdown("#### Bilateral Engagement Priorities")
            for bp in result.get("bilateral_priorities", []):
                st.markdown(
                    f"<div style='background:#161b22; padding:10px; margin-bottom:8px; "
                    f"border-radius:4px; border-left:3px solid #39d353;'>"
                    f"<b>{bp.get('partner', '—')}</b><br>"
                    f"<span style='font-size:13px;'>{bp.get('recommended_engagement', '')}</span><br>"
                    f"<span style='color:#8b949e; font-size:12px;'>"
                    f"Avoid duplicating: {bp.get('avoid', '')}</span></div>",
                    unsafe_allow_html=True,
                )

        # NMSG recommendation
        nmsg = result.get("nmsg_recommendation", {})
        if nmsg:
            st.markdown("#### NMSG Working Group Recommendation")
            lead_wg = nmsg.get("lead_wg", "—")
            rationale = nmsg.get("rationale", "")
            contrib = nmsg.get("contribute_wgs", [])
            st.markdown(
                f"<div style='background:#0f2a1a; padding:12px; border-radius:4px; "
                f"border:1px solid #39d353;'>"
                f"<b>Lead:</b> {lead_wg}<br>"
                f"<span style='font-size:13px;'>{rationale}</span><br><br>"
                f"<b>Contribute to:</b> {', '.join(contrib)}</div>",
                unsafe_allow_html=True,
            )
