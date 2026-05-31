"""
Technology Readiness Level (TRL) assessment for AI techniques in EW.

Addresses the posting requirement:
  "Vurder teknologimodenhed, muligheder, implikationer og begrænsninger
   for bl.a. AI i teknologisk relevante sensor systemer."

Data-driven, no LLM. Interactive scoring against 9 TRL criteria
adapted specifically for AI in EW sensor systems.
"""
import plotly.graph_objects as go
import streamlit as st

from data.strategy_data import AI_EW_TECHNIQUES, TRL_CRITERIA

TRL_COLOR = {
    1: "#f85149", 2: "#f85149", 3: "#da3633",
    4: "#e3b341", 5: "#e3b341",
    6: "#39d353", 7: "#39d353", 8: "#2ea043", 9: "#238636",
}

DEPLOYMENT_THRESHOLD = 7  # TRL ≥ 7 = ready for operational deployment


def render():
    st.header("Technology Readiness Level — AI in EW Sensor Systems")
    st.caption(
        "TRL 1–9 assessment adapted for AI techniques in the EW domain. "
        "Scores current maturity and identifies the specific blockers at each level. "
        "Implements 'Vurder teknologimodenhed' from the TEW mandate."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        technique = st.selectbox("Select AI technique", list(AI_EW_TECHNIQUES.keys()))
        profile = AI_EW_TECHNIQUES[technique]
        current_trl = profile["current_trl"]

        st.markdown(f"**Current TRL: {current_trl}**")
        st.markdown(profile["rationale"])
        st.divider()
        st.markdown("**Path to TRL 7 (deployment-ready):**")
        st.markdown(profile["path_to_7"])
        st.divider()

        # Manual override for exploration
        override = st.slider(
            "Override TRL (for 'what-if')", 1, 9, current_trl, 1,
            help="Drag to explore requirements at different maturity levels.",
        )

    with col_b:
        # TRL progress bar (horizontal)
        fig_bar = go.Figure()
        colors = [TRL_COLOR[i + 1] for i in range(9)]
        alpha_vals = [1.0 if (i + 1) <= override else 0.2 for i in range(9)]

        for i in range(9):
            trl_num = i + 1
            fig_bar.add_trace(go.Bar(
                x=[1],
                y=[f"TRL {trl_num}"],
                orientation="h",
                marker=dict(
                    color=TRL_COLOR[trl_num],
                    opacity=1.0 if trl_num <= override else 0.2,
                    line=dict(color="#0d1117", width=1),
                ),
                showlegend=False,
                hovertemplate=f"<b>TRL {trl_num}</b><br>{TRL_CRITERIA[i]['label']}<extra></extra>",
            ))

        fig_bar.add_vline(x=0.5, line=dict(color="#8b949e", dash="dot", width=1))
        fig_bar.update_layout(
            title=dict(text=f"TRL Status: {technique}",
                       font=dict(color="#c9d1d9", family="Courier New")),
            barmode="stack",
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(visible=False, range=[0, 1]),
            yaxis=dict(tickfont=dict(family="Courier New", color="#c9d1d9", size=10),
                       autorange="reversed"),
            margin=dict(l=60, r=20, t=60, b=20), height=320,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Current level detail
        crit = TRL_CRITERIA[override - 1]
        next_crit = TRL_CRITERIA[override] if override < 9 else None

        color = TRL_COLOR[override]
        st.markdown(
            f"<div style='border-left: 4px solid {color}; padding: 10px 14px;'>"
            f"<b style='color:{color}'>TRL {override}: {crit['label']}</b><br><br>"
            f"{crit['description']}<br><br>"
            f"<b>Evidence needed:</b> {crit['evidence_needed']}<br>"
            f"<b>Current blocker:</b> <i>{crit['blocker']}</i>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if next_crit:
            st.markdown("")
            st.markdown(
                f"<div style='border-left: 2px solid #21262d; padding: 8px 14px; margin-top:8px;'>"
                f"<small><b style='color:#8b949e'>Next: TRL {override+1} — {next_crit['label']}</b><br>"
                f"{next_crit['evidence_needed']}</small>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Portfolio overview
        st.divider()
        st.subheader("Portfolio TRL Overview")

        techniques = list(AI_EW_TECHNIQUES.keys())
        trl_vals   = [AI_EW_TECHNIQUES[t]["current_trl"] for t in techniques]
        bar_colors = [TRL_COLOR[v] for v in trl_vals]

        short_names = [t.split("(")[0].strip()[:30] for t in techniques]

        fig_portfolio = go.Figure(go.Bar(
            x=short_names,
            y=trl_vals,
            marker=dict(color=bar_colors, line=dict(color="#0d1117", width=1)),
            text=[f"TRL {v}" for v in trl_vals],
            textposition="outside",
            textfont=dict(family="Courier New", color="#c9d1d9", size=10),
        ))
        fig_portfolio.add_hline(
            y=DEPLOYMENT_THRESHOLD,
            line=dict(color="#39d353", dash="dash"),
            annotation_text="Deployment threshold (TRL 7)",
            annotation_font=dict(color="#39d353", family="Courier New", size=9),
        )
        fig_portfolio.update_layout(
            title=dict(text="TEW AI Portfolio — Current TRL",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(gridcolor="#21262d",
                       tickfont=dict(family="Courier New", color="#c9d1d9", size=9)),
            yaxis=dict(title="TRL", gridcolor="#21262d", range=[0, 10]),
            margin=dict(l=60, r=20, t=50, b=80), height=260,
        )
        st.plotly_chart(fig_portfolio, use_container_width=True)

        ready = sum(1 for v in trl_vals if v >= DEPLOYMENT_THRESHOLD)
        st.caption(
            f"{ready}/{len(techniques)} techniques at deployment-ready TRL (≥7). "
            f"Multi-sensor Kalman fusion is the most mature and closest to operational integration."
        )
