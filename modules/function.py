"""
FMI TEW — Function management tab.
Eight sub-tabs covering the operational and leadership proof-points:
  1. Intake Workflow
  2. Capacity Model
  3. Adversarial Q&A Prep
  4. Capability Gap Register
  5. Allied Coordination
  6. Scope Boundary
  7. Decision Impact Log
  8. Three-Year Roadmap
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.function_data import (
    BILATERAL_ENGAGEMENTS,
    CAPACITY_ACTIVITIES,
    CAPACITY_PROJECTS,
    CAPABILITY_GAPS,
    DECISIONS,
    INTAKE_STEPS,
    MILESTONES_3YR,
    SCOPE_QUESTIONS,
)


# ---------------------------------------------------------------------------
# 1. Intake workflow
# ---------------------------------------------------------------------------

def _render_intake_workflow():
    st.header("Intake-to-Output Workflow")
    st.caption(
        "How a request from an acquisition programme office becomes a decision brief. "
        "Total cycle time: ~10 working days for a standard analysis request."
    )

    total_days = sum(s["duration_days"] for s in INTAKE_STEPS)
    fig = go.Figure()

    colors = ["#8b949e", "#e3b341", "#39d353", "#58a6ff", "#d2a8ff"]
    cumulative = 0
    for i, step in enumerate(INTAKE_STEPS):
        fig.add_trace(go.Bar(
            x=[step["duration_days"]],
            y=[step["step"]],
            orientation="h",
            base=cumulative,
            marker=dict(color=colors[i], line=dict(color="#0d1117", width=1)),
            name=f"{step['step']} ({step['duration_days']}d)",
            hovertemplate=(
                f"<b>{step['step']}</b><br>"
                f"Owner: {step['owner']}<br>"
                f"Duration: {step['duration_days']} day(s)<br>"
                f"Output: {step['output']}<br>"
                f"<extra></extra>"
            ),
        ))
        cumulative += step["duration_days"]

    fig.update_layout(
        title=dict(text=f"Analysis Request Lifecycle — {total_days} working days",
                   font=dict(color="#c9d1d9", family="Courier New")),
        barmode="stack",
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        xaxis=dict(title="Working days", gridcolor="#21262d"),
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        margin=dict(l=200, r=20, t=60, b=50),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Step detail")
    cols = st.columns(len(INTAKE_STEPS))
    step_colors = ["#8b949e", "#e3b341", "#39d353", "#58a6ff", "#d2a8ff"]
    for i, (col, step) in enumerate(zip(cols, INTAKE_STEPS)):
        col.markdown(
            f"<div style='border-left: 3px solid {step_colors[i]}; padding-left: 8px;'>"
            f"<b>{step['step']}</b><br>"
            f"<small style='color:#8b949e'>{step['owner']} · {step['duration_days']}d</small><br>"
            f"<small>{step['description'][:120]}…</small><br>"
            f"<small style='color:{step_colors[i]}'>↳ {step['output']}</small>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Why this matters"):
        st.markdown(
            "Acquisition programme offices currently have no defined intake process for "
            "technical EW analysis. Without one, requests arrive ad-hoc, scope creep is "
            "unmanaged, and the function's time is allocated reactively. "
            "A defined workflow with a standard scope statement and effort estimate protects "
            "capacity, sets expectations, and creates an audit trail for the decision impact log."
        )


# ---------------------------------------------------------------------------
# 2. Capacity model
# ---------------------------------------------------------------------------

def _render_capacity():
    st.header("Capacity Model — Year 1 with One Analyst")
    st.caption(
        "Honest time allocation across activities. "
        "Y1 capacity = one person. Y2 onward assumes analyst hire #2."
    )

    year = st.radio("Year", [1, 2, 3], horizontal=True, index=0)
    key = {1: "pct_y1", 2: "pct_y2", 3: "pct_y3"}[year]
    headcount = {1: 1, 2: 2, 3: 3}[year]
    working_days_year = 220 * headcount

    df = pd.DataFrame(CAPACITY_ACTIVITIES)
    df = df[df[key] > 0]
    labels = df["activity"].tolist()
    values = df[key].tolist()

    fig_pie = go.Figure(data=go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(
            colors=["#39d353", "#58a6ff", "#e3b341", "#d2a8ff", "#f85149", "#8b949e", "#3fb950"],
        ),
        textfont=dict(family="Courier New", size=10, color="#c9d1d9"),
        hovertemplate="%{label}<br>%{value}% of capacity<extra></extra>",
    ))
    fig_pie.update_layout(
        title=dict(
            text=f"Year {year} — {headcount} analyst(s) · ~{working_days_year} working days",
            font=dict(color="#c9d1d9", family="Courier New"),
        ),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        legend=dict(bgcolor="#0d1117", bordercolor="#21262d",
                    font=dict(family="Courier New", size=10)),
        margin=dict(l=20, r=20, t=60, b=20), height=340,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Project queue
    st.subheader("Project queue — Y1 capacity impact")
    analysis_days_y1 = int(working_days_year * 0.35)
    st.caption(f"~{analysis_days_y1} days available for active analysis in Y1.")

    total = 0
    rows = []
    for p in CAPACITY_PROJECTS:
        total += p["days_est"]
        pct = total / analysis_days_y1 * 100
        overload = pct > 100
        rows.append({
            "Project": p["project"],
            "Complexity": p["complexity"],
            "Urgency": p["urgency"],
            "Est. days": p["days_est"],
            "Cumulative load": f"{min(pct, 100):.0f}%{'  ⚠ OVERLOAD' if overload else ''}",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    remaining = analysis_days_y1 - total
    if remaining < 0:
        st.warning(
            f"Queue exceeds Y1 analysis capacity by {-remaining} days. "
            "Scope must be prioritised or sequenced into Y2.",
            icon="⚠️",
        )
    else:
        st.info(f"{remaining} days of analysis capacity available after listed projects.", icon="ℹ️")

    with st.expander("What this tells leadership"):
        st.markdown(
            "Y1 with one analyst can support 3–4 active acquisition projects at reasonable depth. "
            "Five simultaneous high-complexity projects exceed capacity. "
            "The team lead's job is to say this explicitly, before being asked, "
            "and to propose a sequencing plan — not to accept all requests and underdeliver on each."
        )


# ---------------------------------------------------------------------------
# 3. Adversarial Q&A prep (LLM-powered)
# ---------------------------------------------------------------------------

def _render_adversarial_qa():
    st.header("Adversarial Q&A Prep")
    st.caption(
        "Paste any analysis output, simulation summary, or recommendation. "
        "The tool generates the five hardest questions a sceptical programme manager "
        "or general officer will ask — with suggested answers. "
        "Prepare your brief before entering the room."
    )

    col_in, col_cfg = st.columns([3, 1])

    with col_cfg:
        try:
            from workflow.llm import get_llm
            provider = st.selectbox("LLM", ["anthropic", "mistral"],
                                    format_func=lambda k: {"anthropic": "Claude", "mistral": "Mistral"}[k])
        except Exception:
            provider = None

    with col_in:
        context_text = st.text_area(
            "Analysis context",
            height=200,
            placeholder=(
                "Paste simulation output, intelligence assessment, or recommendation here.\n\n"
                "Example: 'Simulation shows burn-through range of 2 km for self-screening jammer "
                "at 20 dBW ERP against 50 dBW radar. ESM detection at 45 km. "
                "Recommendation: require minimum 30 dBW jammer ERP in kravspecifikation.'"
            ),
        )

    run_btn = st.button("Generate Q&A", type="primary")

    if not run_btn:
        return

    if not context_text.strip():
        st.error("Paste an analysis context first.")
        return

    try:
        from workflow.llm import get_llm
        from workflow.pipeline import generate_adversarial_qa
        llm = get_llm(provider)

        with st.spinner("Generating adversarial questions…"):
            qa_pairs = generate_adversarial_qa(context_text.strip(), llm)

        st.subheader("Anticipated questions and suggested answers")
        for i, qa in enumerate(qa_pairs, 1):
            with st.expander(f"Q{i}: {qa['question']}", expanded=(i == 1)):
                st.markdown(f"**Suggested answer:** {qa['answer']}")
                if qa.get("follow_up"):
                    st.caption(f"Likely follow-up: {qa['follow_up']}")

    except EnvironmentError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Pipeline error: {e}")


# ---------------------------------------------------------------------------
# 4. Capability gap register
# ---------------------------------------------------------------------------

def _render_gap_register():
    st.header("Capability Gap Register")
    st.caption(
        "Living register of identified Danish EW capability gaps. "
        "Each gap is linked to simulation evidence or Allied precedent. "
        "Updated after each landscape review and acquisition project engagement."
    )

    urgency_filter = st.multiselect(
        "Filter by urgency", ["High", "Medium", "Low"],
        default=["High", "Medium"],
    )
    filtered = [g for g in CAPABILITY_GAPS if g["urgency"] in urgency_filter]

    m1, m2, m3 = st.columns(3)
    m1.metric("Total gaps", len(CAPABILITY_GAPS))
    m2.metric("High urgency", sum(1 for g in CAPABILITY_GAPS if g["urgency"] == "High"))
    m3.metric("Open", sum(1 for g in CAPABILITY_GAPS if g["status"] == "Open"))

    st.divider()

    urgency_badge = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
    for gap in filtered:
        with st.expander(
            f"{urgency_badge[gap['urgency']]} **{gap['id']}** — {gap['capability_area']}",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Description:** {gap['description']}")
                st.markdown(f"**Acquisition relevance:** {gap['acquisition_relevance']}")
                st.markdown(f"**Allied coverage:** {gap['allied_coverage']}")
                st.markdown(f"**Simulation evidence:** `{gap['simulation_evidence']}`")
            with col2:
                st.markdown(f"**Status:** {gap['status']}")
                st.markdown(f"**Urgency:** {urgency_badge[gap['urgency']]} {gap['urgency']}")
                st.markdown(f"**Linked programme:** {gap['linked_programme']}")
                st.markdown(f"**Last reviewed:** {gap['last_reviewed']}")


# ---------------------------------------------------------------------------
# 5. Allied coordination tracker
# ---------------------------------------------------------------------------

def _render_coordination():
    st.header("Allied & Industry Coordination Tracker")
    st.caption(
        "Active and planned engagements with Allied, industry, and academic partners. "
        "Demonstrates that TEW manages relationships as a function, not just analyses data."
    )

    priority_colors = {"High": "#f85149", "Medium": "#e3b341", "Low": "#39d353"}
    status_sort = {"Active": 0, "Q2 target": 1, "Q3 target": 2, "Q4 target": 3}
    sorted_eng = sorted(BILATERAL_ENGAGEMENTS,
                        key=lambda e: (status_sort.get(e["status"], 9), e["partner"]))

    # Summary metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total engagements", len(BILATERAL_ENGAGEMENTS))
    m2.metric("High priority", sum(1 for e in BILATERAL_ENGAGEMENTS if e["priority"] == "High"))
    m3.metric("Q2 targets", sum(1 for e in BILATERAL_ENGAGEMENTS if e["status"] == "Q2 target"))
    m4.metric("Q3–Q4 targets", sum(1 for e in BILATERAL_ENGAGEMENTS
                                    if e["status"] in ("Q3 target", "Q4 target")))

    st.divider()

    for eng in sorted_eng:
        color = priority_colors.get(eng["priority"], "#8b949e")
        with st.expander(
            f"**{eng['partner']}** — {eng['topic']} [{eng['status']}]",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Type:** {eng['type']}")
                st.markdown(f"**DK contribution:** {eng['dk_contribution']}")
                st.markdown(f"**DK benefit:** {eng['dk_benefit']}")
                st.markdown(f"**Next action:** {eng['next_action']}")
            with col2:
                st.markdown(
                    f"<span style='color:{color}'>●</span> **Priority: {eng['priority']}**",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Status:** {eng['status']}")
                st.markdown(f"**Owner:** {eng['owner']}")


# ---------------------------------------------------------------------------
# 6. Scope boundary
# ---------------------------------------------------------------------------

def _render_scope():
    st.header("Scope Boundary — Who Owns Which Questions")
    st.caption(
        "Interactive map of which organisation answers which type of acquisition question. "
        "Prevents duplication of Allied work and clarifies TEW's mandate vs. DDRE, FE, and procurement."
    )

    q_idx = st.selectbox(
        "Select an acquisition question",
        range(len(SCOPE_QUESTIONS)),
        format_func=lambda i: SCOPE_QUESTIONS[i]["question"],
    )
    q = SCOPE_QUESTIONS[q_idx]

    col1, col2, col3 = st.columns(3)
    col1.markdown(
        f"<div style='border: 1.5px solid #39d353; border-radius: 6px; padding: 12px;'>"
        f"<b style='color:#39d353'>✓ PRIMARY</b><br><br>"
        f"<b>{q['primary']}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"<div style='border: 1.5px solid #e3b341; border-radius: 6px; padding: 12px;'>"
        f"<b style='color:#e3b341'>◌ SUPPORTS</b><br><br>"
        f"<b>{q['secondary']}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )
    col3.markdown(
        f"<div style='border: 1.5px solid #f85149; border-radius: 6px; padding: 12px;'>"
        f"<b style='color:#f85149'>✗ NOT</b><br><br>"
        f"<b>{q['not']}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(f"**Rationale:** {q['rationale']}")
    st.caption(f"Domain: {q['domain']}")

    st.divider()

    # Domain coverage matrix
    st.subheader("Full scope map")
    orgs = sorted(set(
        [q["primary"] for q in SCOPE_QUESTIONS] +
        [q["secondary"] for q in SCOPE_QUESTIONS]
    ))
    domains = sorted(set(q["domain"] for q in SCOPE_QUESTIONS))

    matrix = []
    for domain in domains:
        row = []
        for org in orgs:
            qs_domain = [q for q in SCOPE_QUESTIONS if q["domain"] == domain]
            if any(q["primary"] == org for q in qs_domain):
                row.append(2)
            elif any(q["secondary"] == org for q in qs_domain):
                row.append(1)
            else:
                row.append(0)
        matrix.append(row)

    # Truncate long org names for display
    short_orgs = [o.split(" (")[0][:22] for o in orgs]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=short_orgs,
        y=domains,
        colorscale=[[0.0, "#0d1117"], [0.5, "#196c2e"], [1.0, "#39d353"]],
        zmin=0, zmax=2,
        text=[[{0: "", 1: "◌", 2: "✓"}[v] for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(family="Courier New", size=14, color="#c9d1d9"),
        showscale=True,
        colorbar=dict(
            tickvals=[0, 1, 2],
            ticktext=["None", "Supports", "Primary"],
            tickfont=dict(family="Courier New", color="#c9d1d9"),
            bgcolor="#0d1117", bordercolor="#21262d",
        ),
        hovertemplate="Domain: %{y}<br>Org: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Mandate Coverage by Domain",
                   font=dict(color="#c9d1d9", family="Courier New")),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        xaxis=dict(side="bottom", tickfont=dict(family="Courier New", color="#c9d1d9", size=9)),
        yaxis=dict(tickfont=dict(family="Courier New", color="#c9d1d9", size=9)),
        margin=dict(l=120, r=20, t=60, b=100),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# 7. Decision impact log
# ---------------------------------------------------------------------------

def _render_impact_log():
    st.header("Decision Impact Log")
    st.caption(
        "Analyses produced, decisions informed, outcomes tracked. "
        "This is the accountability record that justifies the function's continued budget. "
        "Illustrative entries — Year 1 projection."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Analyses completed", len(DECISIONS))
    m2.metric("Decisions informed", len(DECISIONS))
    m3.metric("High-confidence outcomes",
              sum(1 for d in DECISIONS if d["confidence"] == "High"))

    st.divider()

    conf_badge = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    for d in DECISIONS:
        with st.expander(
            f"{conf_badge[d['confidence']]} {d['date']} — {d['project']}",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Analysis provided:** {d['analysis_provided']}")
                st.markdown(f"**Recommendation:** {d['recommendation']}")
                st.markdown(f"**Decision made:** {d['decision_made']}")
                st.markdown(f"**Outcome:** {d['outcome']}")
            with col2:
                st.markdown(f"**Confidence:** {conf_badge[d['confidence']]} {d['confidence']}")
                st.markdown(f"**Impact:** {d['impact']}")

    with st.expander("Why this matters"):
        st.markdown(
            "Most technical advisory functions at FMI produce outputs with no mechanism "
            "to track whether those outputs influenced decisions or whether predictions proved correct. "
            "This log creates that mechanism. "
            "It also provides the evidence base for every future budget conversation: "
            "'in Year 1, TEW influenced X decisions and identified Y dB of over-claimed performance "
            "in vendor submissions.' That is a business case, not a budget request."
        )


# ---------------------------------------------------------------------------
# 8. Three-year roadmap
# ---------------------------------------------------------------------------

def _render_roadmap_3yr():
    st.header("Three-Year Capability Roadmap")
    st.caption(
        "Headcount, infrastructure, bilateral milestones, and capability targets across Y1–Y3. "
        "The Q4 deliverable — shown here as a draft to demonstrate the function's planning horizon."
    )

    category_colors = {
        "Deliverable": "#39d353",
        "Bilateral": "#58a6ff",
        "Staffing": "#d2a8ff",
        "Infrastructure": "#e3b341",
        "Capability": "#f85149",
    }

    year_filter = st.multiselect(
        "Show years", [1, 2, 3], default=[1, 2, 3],
        format_func=lambda y: f"Year {y}"
    )
    cat_filter = st.multiselect(
        "Show categories", list(category_colors.keys()),
        default=list(category_colors.keys()),
    )

    filtered = [m for m in MILESTONES_3YR
                if m["year"] in year_filter and m["category"] in cat_filter]

    fig = go.Figure()
    seen_cats = set()
    for m in filtered:
        color = category_colors[m["category"]]
        show_legend = m["category"] not in seen_cats
        seen_cats.add(m["category"])
        fig.add_trace(go.Bar(
            x=[m["end"]],
            y=[m["task"]],
            base=[m["start"]],
            orientation="h",
            marker=dict(color=color, opacity=0.85,
                        line=dict(color="#0d1117", width=0.5)),
            name=m["category"],
            showlegend=show_legend,
            legendgroup=m["category"],
            hovertemplate=(
                f"<b>{m['task']}</b><br>"
                f"Category: {m['category']}<br>"
                f"Year {m['year']}<br>"
                f"{m['start']} → {m['end']}"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=dict(text="TEW Capability Build — Year 1 to Year 3",
                   font=dict(color="#c9d1d9", family="Courier New")),
        barmode="overlay",
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Courier New"),
        xaxis=dict(
            title="",
            type="date",
            gridcolor="#21262d",
            tickformat="%b %Y",
            tickfont=dict(family="Courier New", size=9),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(family="Courier New", size=9),
        ),
        legend=dict(bgcolor="#0d1117", bordercolor="#21262d",
                    font=dict(family="Courier New", size=10),
                    orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=240, r=20, t=80, b=50),
        height=max(380, len(filtered) * 28 + 100),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Headcount progression summary
    st.subheader("Headcount and infrastructure progression")
    hc_data = {
        "Year": ["Year 1 (Aug 26 – Jul 27)", "Year 2 (Aug 27 – Jul 28)", "Year 3 (Aug 28 – Jul 29)"],
        "Analysts": [1, 2, 3],
        "Classification ceiling": ["IKKE-KLASSIFICERET / TIL TJENESTEBRUG", "FORTROLIGT", "HEMMELIGT"],
        "Active MOUs": [0, 2, 4],
        "NMSG role": ["Observer", "Contributor", "Working group lead"],
    }
    st.dataframe(pd.DataFrame(hc_data), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Top-level render
# ---------------------------------------------------------------------------

def render():
    (
        ft1, ft2, ft3, ft4, ft5, ft6, ft7, ft8,
    ) = st.tabs([
        "📋 Intake Workflow",
        "📊 Capacity Model",
        "🎯 Adversarial Prep",
        "📁 Gap Register",
        "🤝 Allied Coordination",
        "🗺️ Scope Boundary",
        "📈 Impact Log",
        "🗓️ 3-Year Roadmap",
    ])

    with ft1:
        _render_intake_workflow()
    with ft2:
        _render_capacity()
    with ft3:
        _render_adversarial_qa()
    with ft4:
        _render_gap_register()
    with ft5:
        _render_coordination()
    with ft6:
        _render_scope()
    with ft7:
        _render_impact_log()
    with ft8:
        _render_roadmap_3yr()
