"""
Vendor claim stress-tester + kravspecifikation section generator.

Stress-tester: given a vendor's claimed J/S at stated range,
back-calculate the implied radar ERP or RCS and flag implausibility.

Kravspec generator: LLM pipeline that takes simulation parameters
and produces a draft kravspecifikation requirement section.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

SPEED_OF_LIGHT = 3e8
THREAT_MODES = {"Barrage": -10, "Spot": 0, "Sweep": -5}


@st.cache_data
def compute_implied_radar_erp(
    jammer_erp_dbw: float,
    rcs_dbsm: float,
    vendor_js_db: float,
    vendor_range_km: float,
    threat_mode: str,
) -> float:
    mode_penalty = THREAT_MODES[threat_mode]
    r_m = vendor_range_km * 1e3
    # J/S = ERP_J + mode - ERP_R + 10*log10(4π) + 20*log10(R) - RCS
    # → ERP_R = ERP_J + mode - J/S + 10*log10(4π) + 20*log10(R) - RCS
    return (
        jammer_erp_dbw + mode_penalty - vendor_js_db
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(r_m)
        - rcs_dbsm
    )


@st.cache_data
def compute_js_curve_vendor(
    jammer_erp_dbw: float,
    radar_erp_dbw: float,
    rcs_dbsm: float,
    threat_mode: str,
    max_range_km: float,
):
    mode_penalty = THREAT_MODES[threat_mode]
    ranges_km = np.linspace(1, max_range_km, 400)
    ranges_m = ranges_km * 1e3
    js = (
        jammer_erp_dbw + mode_penalty - radar_erp_dbw
        + 10 * np.log10(4 * np.pi)
        + 20 * np.log10(ranges_m)
        - rcs_dbsm
    )
    return ranges_km, js


def _render_stress_tester():
    st.subheader("Vendor Claim Stress-Tester")
    st.caption(
        "Enter a vendor's claimed J/S figure and the test geometry they used. "
        "The tool back-calculates what radar ERP their claim assumes — "
        "and flags if that assumption is implausible against the actual threat."
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("**Vendor's claim**")
        vendor_js = st.slider("Claimed J/S (dB)", -20, 40, 15, 1)
        vendor_range = st.slider("At range (km)", 5, 200, 50, 5)
        vendor_mode = st.selectbox("Test geometry mode", list(THREAT_MODES.keys()), index=1)

        st.markdown("**Known platform parameters**")
        jammer_erp = st.slider("Jammer ERP (dBW) — your known spec", -10, 60, 20, 1)
        rcs_dbsm = st.slider("Platform RCS (dBsm)", -20, 15, -15, 1)

        st.markdown("**Realistic threat baseline**")
        actual_radar_erp = st.slider("Actual threat radar ERP (dBW) — from FE/OSINT", 20, 80, 55, 1)
        max_range = st.slider("Display range (km)", 20, 300, 150, 10)

    implied_radar_erp = compute_implied_radar_erp(
        jammer_erp, rcs_dbsm, vendor_js, vendor_range, vendor_mode,
    )
    discrepancy = implied_radar_erp - actual_radar_erp

    with col_b:
        ranges_km_actual, js_actual = compute_js_curve_vendor(
            jammer_erp, actual_radar_erp, rcs_dbsm, vendor_mode, max_range,
        )
        ranges_km_implied, js_implied = compute_js_curve_vendor(
            jammer_erp, implied_radar_erp, rcs_dbsm, vendor_mode, max_range,
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ranges_km_actual, y=js_actual,
            mode="lines", name="J/S vs actual threat ERP",
            line=dict(color="#39d353", width=2),
        ))
        fig.add_trace(go.Scatter(
            x=ranges_km_implied, y=js_implied,
            mode="lines", name="J/S vs vendor-implied radar ERP",
            line=dict(color="#58a6ff", width=2, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=[vendor_range], y=[vendor_js],
            mode="markers", name="Vendor claimed point",
            marker=dict(color="#e3b341", size=14, symbol="star"),
        ))
        fig.add_hline(y=0, line=dict(color="#8b949e", dash="dot", width=1))

        fig.update_layout(
            title=dict(text="Vendor Claim vs Physics — J/S Comparison",
                       font=dict(color="#c9d1d9", family="Courier New")),
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", family="Courier New"),
            xaxis=dict(title="Range (km)", gridcolor="#21262d"),
            yaxis=dict(title="J/S (dB)", gridcolor="#21262d"),
            legend=dict(bgcolor="#0d1117", bordercolor="#21262d"),
            margin=dict(l=60, r=20, t=60, b=50), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Implied radar ERP (dBW)", f"{implied_radar_erp:.1f}")
        m2.metric("Actual threat ERP (dBW)", f"{actual_radar_erp:.1f}")
        sign = "+" if discrepancy > 0 else ""
        # discrepancy > 0: vendor used stronger emulator → conservative claim (good)
        # discrepancy < 0: vendor used weaker emulator → optimistic claim (bad)
        m3.metric(
            "Discrepancy (dB)",
            f"{sign}{discrepancy:.1f}",
            delta="Conservative (harder emulator)" if discrepancy > 3
                  else ("Optimistic (weaker emulator)" if discrepancy < -3 else "Consistent"),
            delta_color="normal" if discrepancy > -3 else "inverse",
        )

        if discrepancy < -6:
            st.error(
                f"⚠ Vendor's claimed J/S requires a threat radar ERP of only "
                f"**{implied_radar_erp:.1f} dBW** — **{-discrepancy:.1f} dB weaker** "
                f"than the FE/OSINT baseline of {actual_radar_erp} dBW. "
                f"This claim is **optimistic** — it will not reproduce against the real threat. "
                f"Request vendor clarification on test emulator parameters.",
            )
        elif discrepancy < -3:
            st.warning(
                f"Vendor's test emulator ({implied_radar_erp:.1f} dBW) is "
                f"{-discrepancy:.1f} dB below the realistic threat baseline — "
                f"claim may not hold against the actual threat. Worth querying.",
                icon="⚠️",
            )
        elif discrepancy > 6:
            st.success(
                f"Vendor used a more demanding emulator ({implied_radar_erp:.1f} dBW) "
                f"than the realistic threat ({actual_radar_erp} dBW). "
                f"Claim is **conservative** — actual performance against the real threat "
                f"will be at least {discrepancy:.1f} dB better.",
            )
        else:
            st.success(
                f"Vendor's claim is consistent with the known threat ERP baseline "
                f"(discrepancy: {sign}{discrepancy:.1f} dB). "
                f"Verify test geometry independently before accepting.",
            )


def _render_kravspec_generator():
    st.subheader("Kravspecifikation Section Generator")
    st.caption(
        "Paste simulation parameters and context. "
        "Generates a draft kravspecifikation technical requirement section "
        "in the standard FMI format: requirement, rationale, test method, acceptance criterion."
    )

    col_in, col_cfg = st.columns([3, 1])

    with col_cfg:
        try:
            from workflow.llm import get_llm
            provider = st.selectbox(
                "LLM", ["anthropic", "mistral"],
                format_func=lambda k: {"anthropic": "Claude", "mistral": "Mistral"}[k],
            )
        except Exception:
            provider = "anthropic"

        req_id = st.text_input("Requirement ID", value="REQ-EW-001")
        domain = st.selectbox("Domain", ["Electronic Warfare", "Sensors / ISR",
                                          "Communications / Datalinks", "Air Defence"])

    with col_in:
        sim_context = st.text_area(
            "Simulation context",
            height=160,
            placeholder=(
                "Example:\n"
                "Simulation shows burn-through range of 0.016 km for a self-screening jammer "
                "at 20 dBW ERP against a 55 dBW threat radar, F-35A RCS (−15 dBsm), Spot mode. "
                "ESM detection range: 45 km at −70 dBm sensitivity. "
                "Monte Carlo P10 burn-through: 0.01 km. "
                "Threat ERP grows at 1.2 dB/year — system obsolete by 2031 at current spec."
            ),
        )
        operational_context = st.text_area(
            "Operational context",
            height=80,
            placeholder="e.g. Self-protection jammer for F-35A against Baltic SAM threat. "
                        "NATO capability target DAN-EW-003.",
        )

    gen_btn = st.button("Generate kravspec section", type="primary")
    if not gen_btn:
        return

    if not sim_context.strip():
        st.error("Paste simulation context first.")
        return

    try:
        from workflow.llm import get_llm
        llm = get_llm(provider)
    except EnvironmentError as e:
        st.error(str(e))
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    _KRAV_PROMPT = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Danish defence acquisition technical writer at FMI TEW. "
            "Write a single kravspecifikation technical requirement section in the following format:\n\n"
            f"**{req_id}** [domain: {domain}]\n\n"
            "**Krav (Requirement):** A single, measurable performance statement. "
            "Use 'shall' language. Quantitative where possible.\n\n"
            "**Rationale:** One paragraph explaining the operational justification. "
            "Reference the simulation evidence provided.\n\n"
            "**Testmetode (Test method):** How compliance will be demonstrated. "
            "Specify test configuration, reference emulator, and measurement procedure.\n\n"
            "**Acceptancekriterium (Acceptance criterion):** Specific, measurable pass/fail criterion. "
            "Include uncertainty tolerance.\n\n"
            "**Risiko ved ikke-opfyldelse (Risk of non-compliance):** One sentence on operational consequence.\n\n"
            "Be concise and technically precise. Write for programme managers, not engineers."
        )),
        ("human", (
            "Simulation context:\n{sim_context}\n\n"
            "Operational context:\n{op_context}"
        )),
    ])

    try:
        with st.spinner("Generating kravspecifikation section…"):
            parser = StrOutputParser()
            result = (_KRAV_PROMPT | llm | parser).invoke({
                "sim_context": sim_context.strip(),
                "op_context": operational_context.strip() or "Not specified.",
            })

        st.markdown(result)

        st.download_button(
            "Download (.md)",
            data=result,
            file_name=f"{req_id.lower().replace('-', '_')}_krav.md",
            mime="text/markdown",
        )
    except Exception as e:
        st.error(f"LLM error: {e}")


def render():
    vt1, vt2 = st.tabs(["🔬 Vendor Stress-Test", "📄 Kravspec Generator"])
    with vt1:
        _render_stress_tester()
    with vt2:
        _render_kravspec_generator()
