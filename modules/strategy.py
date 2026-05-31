"""
Strategy tab — 6 sub-tabs addressing the FMI TEW posting requirements:

1. Digital Battlespace      — "den digitale kampplads inden for EW"
2. Demo Planning            — "sparre om teknologidemonstrationer / udvikle koncepter"
3. Capability Maturity      — "opbygge og vedligeholde en M&S kapacitet"
4. NATO Fora                — "deltage i teknologiske fora ind- og udland"
5. Team Composition         — "sætte retning og prioritere ressourcer i teamet"
6. Cost of Inaction         — "bidrage direkte til kampkraft og overlevelsesevne"
"""
import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.strategy_data import (
    CAPABILITY_DIMENSIONS,
    COMPETENCY_AREAS,
    FUNCTION_ANNUAL_COST_MDKK,
    NATO_FORA,
    PROCUREMENT_EXAMPLES,
    RECENT_PUBLICATIONS,
    TEAM_COMPETENCY_SCORES,
    TEAM_ROLES,
)


# ---------------------------------------------------------------------------
# 1. Digital Battlespace
# ---------------------------------------------------------------------------

def _render_digital_battlespace():
    st.header("Den Digitale Kampplads — EW Integration Architecture")
    st.caption(
        "How signal-level EW M&S outputs flow into the digital battlespace: "
        "from physics simulation through operational EW picture to C2 decision support. "
        "TEW's role at each layer."
    )

    # Sankey: data flow from TEW outputs to decision
    labels = [
        # Sources (0-3)
        "Signal simulation\n(TEW)", "Intelligence pipeline\n(TEW)",
        "Vendor stress-test\n(TEW)", "TRL assessment\n(TEW)",
        # Intermediary (4-7)
        "EW programme\nadvisory", "Kravspecifikation\ndraft",
        "Technology\ndemonstration", "Allied M&S\n(FFI / NMSG)",
        # Outputs (8-10)
        "FMI acquisition\ndecision", "Forsvaret operative\nkapacitet",
        "NATO standard\ncontribution",
    ]
    source = [0, 0, 1, 2, 3, 3, 4, 5, 6, 7, 4, 7]
    target = [4, 6, 4, 5, 5, 6, 8, 8, 8, 8, 9, 10]
    value  = [3, 2, 2, 2, 2, 1, 3, 2, 3, 2, 2, 2]
    colors = [
        "#196c2e", "#196c2e", "#145220", "#0d3b1c",
        "#1a4a6e", "#1a4a6e", "#4a3a00", "#1a3a6e",
        "#6e1313", "#6e1313", "#6e1313",
        "#0d3b1c",
    ]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20,
            line=dict(color="#21262d", width=0.5),
            label=labels,
            color=["#39d353", "#39d353", "#39d353", "#39d353",
                   "#58a6ff", "#58a6ff", "#e3b341", "#d2a8ff",
                   "#f85149", "#f85149", "#f85149"],
            hovertemplate="%{label}<extra></extra>",
        ),
        link=dict(
            source=source, target=target, value=value,
            color=["rgba(57,211,83,0.2)"] * 4 +
                  ["rgba(88,166,255,0.2)"] * 4 +
                  ["rgba(248,81,73,0.2)"] * 4,
        ),
    )])
    fig.update_layout(
        title=dict(text="TEW Output Flow — Signal Level to Acquisition Decision",
                   font=dict(color="#c9d1d9", family="Courier New")),
        font=dict(family="Courier New", color="#c9d1d9", size=10),
        paper_bgcolor="#0d1117",
        margin=dict(l=20, r=20, t=60, b=20),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Layer descriptions
    col1, col2, col3, col4 = st.columns(4)
    for col, title, color, items in [
        (col1, "Layer 1: Physics simulation", "#39d353",
         ["J/S, SEAD, burn-through", "Threat evolution", "Multi-sensor fusion", "Kill chain"]),
        (col2, "Layer 2: Advisory products", "#58a6ff",
         ["Vendor stress-test", "Kravspec section", "Teknisk vurdering", "TRL assessment"]),
        (col3, "Layer 3: Demonstration", "#e3b341",
         ["Concept demonstrations", "Technology demos", "Allied M&S exercises", "HIL testing"]),
        (col4, "Layer 4: Digital integration", "#f85149",
         ["FMI acquisition decisions", "NATO standard contributions", "Allied M&S datasets", "Forsvaret EW picture"]),
    ]:
        col.markdown(
            f"<div style='border-top: 3px solid {color}; padding-top: 8px;'>"
            f"<b style='color:{color}'>{title}</b><br>"
            + "".join(f"<br>• {item}" for item in items)
            + "</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# 2. Demo Planning
# ---------------------------------------------------------------------------

def _render_demo_planning():
    st.header("Technology Demonstration Planning")
    st.caption(
        "'Sparre med udviklingsteams i forbindelse med teknologidemonstrationer' "
        "and 'Udvikle og demonstrere koncepter'. "
        "Structured approach: from hypothesis to success criteria to downloadable plan."
    )

    with st.form("demo_form"):
        tech_name   = st.text_input("Technology / concept to demonstrate",
                                     placeholder="e.g. AI anomaly detection on ESM pulse trains")
        hypothesis  = st.text_area("Hypothesis to test", height=80,
                                    placeholder="e.g. Mahalanobis-distance detector will detect "
                                               "frequency-agile threat signatures with Pd > 80% "
                                               "at Pfa < 5% on representative Baltic ESM data.")
        success_criteria = st.text_area("Success criteria (measurable)", height=80,
                                         placeholder="e.g. Pd ≥ 80%, Pfa ≤ 5%, "
                                                     "computational latency < 10 ms per observation, "
                                                     "validated on ≥ 100 intercepts from TERMA test emulator.")
        test_setup  = st.text_area("Minimum viable test setup", height=60,
                                    placeholder="e.g. TERMA HIL emulator, 3 threat modes, "
                                               "1 novel frequency-agile mode not in training data.")
        stakeholders = st.text_input("Stakeholders and communication plan",
                                      placeholder="e.g. FMI programme office (weekly update), "
                                                  "TERMA technical lead (daily during test week), "
                                                  "FMI leadership (go/no-go briefing after test).")
        go_nogo     = st.text_area("Go/no-go criteria", height=60,
                                    placeholder="e.g. Go: Pd > 70% on first 50 test cases. "
                                               "No-go: < 60% Pd or > 10% Pfa after tuning.")
        failure_modes = st.text_area("Known failure modes and mitigations", height=60,
                                      placeholder="e.g. Distribution shift (mitigate: test on "
                                                  "held-out threat types from training set).")
        timeline    = st.text_input("Timeline", placeholder="e.g. Q2 Y1 — 3-week test window")
        responsible = st.text_input("Responsible", placeholder="e.g. Team Lead")

        submitted = st.form_submit_button("Generate demo plan", type="primary")

    if not submitted:
        return

    if not tech_name.strip():
        st.error("Enter a technology name.")
        return

    date_str = datetime.date.today().isoformat()
    plan = f"""# Technology Demonstration Plan
**Technology:** {tech_name}
**Generated:** {date_str}  |  **Classification:** IKKE-KLASSIFICERET

---

## Hypothesis
{hypothesis or "Not specified."}

## Success Criteria
{success_criteria or "Not specified."}

## Minimum Viable Test Setup
{test_setup or "Not specified."}

## Stakeholder Communication
{stakeholders or "Not specified."}

## Go / No-Go Criteria
{go_nogo or "Not specified."}

## Known Failure Modes and Mitigations
{failure_modes or "Not specified."}

## Timeline and Responsibility
**Timeline:** {timeline or "TBD"}
**Responsible:** {responsible or "Team Lead"}

---
*Prepared by FMI TEW — AI Modellering og Simulering*
"""
    st.markdown(plan)
    st.download_button(
        "Download demo plan (.md)",
        data=plan,
        file_name=f"demo_plan_{tech_name[:30].lower().replace(' ', '_')}_{date_str}.md",
        mime="text/markdown",
    )


# ---------------------------------------------------------------------------
# 3. Capability Maturity
# ---------------------------------------------------------------------------

def _render_capability_maturity():
    st.header("Capability Maturity Model — TEW M&S Function")
    st.caption(
        "'Opbygge og vedligeholde en M&S kapacitet'. "
        "Five dimensions, current state vs. Year 1/2/3 targets. "
        "Specific closing action for each gap."
    )

    year = st.radio("View target year", ["Current", "Year 1", "Year 2", "Year 3"],
                    horizontal=True, index=0)
    year_map = {"Current": "current", "Year 1": "y1_target",
                "Year 2": "y2_target", "Year 3": "y3_target"}
    key = year_map[year]

    dims   = [d["name"] for d in CAPABILITY_DIMENSIONS]
    scores = [d[key] for d in CAPABILITY_DIMENSIONS]

    fig = go.Figure()
    # Fill for target year
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=dims + [dims[0]],
        fill="toself",
        fillcolor="rgba(57,211,83,0.15)",
        line=dict(color="#39d353", width=2),
        name=year,
    ))
    # Overlay current if viewing a target year
    if key != "current":
        cur_scores = [d["current"] for d in CAPABILITY_DIMENSIONS]
        fig.add_trace(go.Scatterpolar(
            r=cur_scores + [cur_scores[0]],
            theta=dims + [dims[0]],
            fill="toself",
            fillcolor="rgba(139,148,158,0.08)",
            line=dict(color="#8b949e", width=1.5, dash="dot"),
            name="Current",
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(family="Courier New")),
            angularaxis=dict(tickfont=dict(family="Courier New", size=10, color="#c9d1d9")),
            bgcolor="#0d1117",
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
        margin=dict(l=60, r=60, t=40, b=40), height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Dimension detail")
    for d in CAPABILITY_DIMENSIONS:
        current = d["current"]
        target  = d[key]
        gap     = target - current
        with st.expander(
            f"{'▲' if gap > 0 else '●'} **{d['name']}** — "
            f"Current: {current}/5 → {year}: {target}/5",
            expanded=False,
        ):
            st.markdown(f"*{d['description']}*")
            if key == "y1_target" and gap > 0:
                st.markdown(f"**Y1 closing action:** {d['closing_action_y1']}")
            elif key == "y2_target" and gap > 0:
                st.markdown(f"**Y2 closing action:** {d['closing_action_y2']}")
            elif key == "y3_target" and gap > 0:
                st.markdown(f"**Y3 closing action:** {d['closing_action_y3']}")
            elif gap == 0:
                st.markdown("No change required at this target year.")


# ---------------------------------------------------------------------------
# 4. NATO Fora
# ---------------------------------------------------------------------------

def _render_nato_fora():
    st.header("NATO Fora & Research Current Awareness")
    st.caption(
        "'Deltage i teknologiske fora i både ind- og udland med relevante partnere'. "
        "Active NATO/Nordic working groups and recent publications relevant to TEW."
    )

    priority_filter = st.multiselect(
        "Filter by priority", ["High", "Medium", "Low"],
        default=["High", "Medium"],
    )

    st.subheader("Active working groups and fora")
    priority_badge = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
    status_color   = {"Not engaged": "#f85149", "Observer via FFI bilateral": "#e3b341",
                      "Participant (Forsvaret), FMI TEW not yet engaged": "#e3b341"}

    for f in NATO_FORA:
        if f["priority"] not in priority_filter:
            continue
        badge = priority_badge[f["priority"]]
        with st.expander(
            f"{badge} **{f['forum']}** — {f['topic']}",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Lead nations:** {f['lead_nations']}")
                st.markdown(f"**TEW relevance:** {f['tew_relevance']}")
                st.markdown(f"**Contribution type:** {f['contribution_type']}")
            with col2:
                dk_color = status_color.get(f["dk_status"], "#8b949e")
                st.markdown(
                    f"<span style='color:{dk_color}'>● DK status: {f['dk_status']}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Next event:** {f['next_event']}")

    st.divider()
    st.subheader("Recent Allied publications")
    for pub in RECENT_PUBLICATIONS:
        st.markdown(
            f"📄 **{pub['title']}** ({pub['authors']}, {pub['year']})  \n"
            f"*{pub['relevance']}*  \n"
            f"Access: `{pub['access']}`"
        )
        st.markdown("")


# ---------------------------------------------------------------------------
# 5. Team Composition
# ---------------------------------------------------------------------------

def _render_team_composition():
    st.header("Team Composition — Kompetenceprofiler Y1–Y3")
    st.caption(
        "'Sætte retning for resten af teamet og prioritere ressourcer.' "
        "Job profiles for each hire, combined competency matrix progression."
    )

    for role in TEAM_ROLES:
        year_label = {1: "Year 1 (current)", 2: "Year 2 — Hire #2", 3: "Year 3 — Hire #3"}[role["year"]]
        with st.expander(f"**{year_label}: {role['title']}**", expanded=(role["year"] == 1)):
            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown(f"**Profile:** {role['profile']}")
                st.markdown("**Primary skills:**")
                for s in role["primary_skills"]:
                    st.markdown(f"  - {s}")
                st.markdown("**Covers:**")
                for c in role["covers"]:
                    st.markdown(f"  ✅ {c}")
            with col2:
                st.markdown("**Gap remaining after this hire:**")
                for g in role["gap_left"]:
                    st.markdown(f"  ⚠ {g}")

    st.divider()
    st.subheader("Competency matrix progression")

    year_sel = st.radio("Year", list(TEAM_COMPETENCY_SCORES.keys()), horizontal=True)
    scores = TEAM_COMPETENCY_SCORES[year_sel]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=COMPETENCY_AREAS + [COMPETENCY_AREAS[0]],
        fill="toself",
        fillcolor="rgba(57,211,83,0.15)",
        line=dict(color="#39d353", width=2),
        name=year_sel,
    ))
    if year_sel != "Year 1 (TL alone)":
        y1 = TEAM_COMPETENCY_SCORES["Year 1 (TL alone)"]
        fig.add_trace(go.Scatterpolar(
            r=y1 + [y1[0]],
            theta=COMPETENCY_AREAS + [COMPETENCY_AREAS[0]],
            fill="toself",
            fillcolor="rgba(139,148,158,0.06)",
            line=dict(color="#8b949e", width=1, dash="dot"),
            name="Year 1 (TL alone)",
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5],
                            tickfont=dict(family="Courier New")),
            angularaxis=dict(tickfont=dict(family="Courier New", size=9, color="#c9d1d9")),
            bgcolor="#0d1117",
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
        margin=dict(l=60, r=60, t=30, b=30), height=340,
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# 6. Cost of Inaction
# ---------------------------------------------------------------------------

def _render_cost_of_inaction():
    st.header("Cost-of-Inaction Calculator")
    st.caption(
        "The M&S function's budget justification in acquisition economics terms. "
        "Expected cost of procuring an under-spec system without independent technical validation, "
        "vs. annual cost of the TEW M&S function. "
        "'Bidrage direkte til at forøge kampkraften samt overlevelsesevnen.'"
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        example_names = [p["name"] for p in PROCUREMENT_EXAMPLES]
        selected = st.selectbox("Procurement scenario", example_names)
        ex = next(p for p in PROCUREMENT_EXAMPLES if p["name"] == selected)

        st.markdown("**Scenario parameters**")
        value    = st.slider("Procurement value (mDKK)", 50, 2000, int(ex["value_mdkk"]), 25)
        lifecycle = st.slider("System lifecycle (years)", 5, 25, int(ex["lifecycle_years"]), 1)
        p_under  = st.slider("P(under-spec without M&S) (%)", 5, 60,
                             int(ex["p_underspec_without_ms"] * 100), 5) / 100
        shortfall_pct = st.slider("Performance shortfall (%)", 5, 60,
                                   int(ex["performance_shortfall_pct"]), 5) / 100
        p_with_ms = st.slider("P(under-spec with M&S) (%)", 0, 20, 5, 1) / 100
        n_procurements = st.slider("Active EW procurements per year", 1, 8, 3, 1)

    with col_b:
        # Expected cost calculations
        # Without M&S: expected shortfall = value × P(under-spec) × shortfall% × (some lifecycle cost fraction)
        # Shortfall cost: assume procurement restart or performance penalty = value × shortfall%
        shortfall_cost = value * shortfall_pct  # cost of getting it wrong (performance gap value)
        expected_cost_without = shortfall_cost * p_under
        expected_cost_with    = shortfall_cost * p_with_ms

        # Annual risk exposure across all procurements
        annual_risk_without = expected_cost_without * n_procurements
        annual_risk_with    = expected_cost_with * n_procurements
        annual_saving       = annual_risk_without - annual_risk_with

        ms_cost_annual = FUNCTION_ANNUAL_COST_MDKK
        net_benefit    = annual_saving - ms_cost_annual
        roi_pct        = (annual_saving / ms_cost_annual - 1) * 100 if ms_cost_annual > 0 else 0
        breakeven_n    = ms_cost_annual / (expected_cost_without - expected_cost_with) if (expected_cost_without - expected_cost_with) > 0 else float("inf")

        # Waterfall chart
        fig = go.Figure(go.Waterfall(
            x=["Annual risk\n(no M&S)", "Risk reduction\nfrom M&S",
               "M&S function\ncost", "Net annual\nbenefit"],
            y=[annual_risk_without, -(annual_risk_without - annual_risk_with),
               -ms_cost_annual, net_benefit],
            measure=["absolute", "relative", "relative", "total"],
            text=[f"{annual_risk_without:.1f} mDKK",
                  f"−{annual_risk_without - annual_risk_with:.1f} mDKK",
                  f"−{ms_cost_annual:.1f} mDKK",
                  f"{net_benefit:.1f} mDKK"],
            textposition="outside",
            textfont=dict(family="Courier New", color="#c9d1d9", size=10),
            connector=dict(line=dict(color="#21262d")),
            increasing=dict(marker=dict(color="#f85149")),
            decreasing=dict(marker=dict(color="#39d353")),
            totals=dict(marker=dict(color="#58a6ff")),
        ))
        fig.update_layout(
            title=dict(text="Annual Risk vs. M&S Function Cost (mDKK)",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(gridcolor="#21262d",
                       tickfont=dict(family="Courier New", color="#c9d1d9")),
            yaxis=dict(title="mDKK/year", gridcolor="#21262d"),
            showlegend=False,
            margin=dict(l=60, r=20, t=60, b=60), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Annual risk (no M&S)", f"{annual_risk_without:.1f} mDKK")
        m2.metric("Annual risk (with M&S)", f"{annual_risk_with:.1f} mDKK")
        m3.metric("M&S function cost/yr", f"{ms_cost_annual:.1f} mDKK")
        m4.metric("Net annual benefit", f"{net_benefit:.1f} mDKK",
                  delta=f"ROI {roi_pct:.0f}%",
                  delta_color="normal" if net_benefit > 0 else "inverse")

        if net_benefit > 0:
            st.success(
                f"M&S function pays for itself at **{breakeven_n:.1f} procurements/year** "
                f"(current: {n_procurements}). "
                f"Net annual benefit: **{net_benefit:.1f} mDKK**. "
                f"ROI: **{roi_pct:.0f}%**.",
            )
        else:
            st.info(
                "Increase scenario value or P(under-spec) to show positive ROI. "
                "These parameters are conservative — real shortfall costs include "
                "lifecycle performance gaps, re-procurement, and operational risk.",
            )

        with st.expander("Methodology note"):
            st.markdown(
                "**Shortfall cost** = procurement value × performance shortfall percentage. "
                "Represents the value of capability not delivered, not necessarily a direct reprocurement cost. "
                "**Expected cost** = shortfall cost × probability of procuring under-spec system. "
                "**P(under-spec without M&S)** is a conservative estimate based on documented cases "
                "of ERP discrepancies between vendor claims and independent test results in Allied nations. "
                "All figures are illustrative — not based on classified FMI programme data."
            )


# ---------------------------------------------------------------------------
# Top-level render
# ---------------------------------------------------------------------------

def render():
    (s1, s2, s3, s4, s5, s6) = st.tabs([
        "🗺️ Digital Battlespace",
        "📋 Demo Planning",
        "📈 Capability Maturity",
        "🌐 NATO Fora",
        "👥 Team Composition",
        "💰 Cost of Inaction",
    ])
    with s1: _render_digital_battlespace()
    with s2: _render_demo_planning()
    with s3: _render_capability_maturity()
    with s4: _render_nato_fora()
    with s5: _render_team_composition()
    with s6: _render_cost_of_inaction()
