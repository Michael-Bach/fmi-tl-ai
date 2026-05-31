import pandas as pd
import streamlit as st

from workflow.llm import get_llm
from workflow.loaders import load_url, load_pdf_bytes, load_text
from workflow.pipeline import run_structured
from workflow.structured import DanishAssessment, ProductAnalysis

_PROVIDERS = {"anthropic": "Claude (Anthropic)", "mistral": "Mistral"}

_REC_COLOR = {"evaluate": "🟢", "monitor": "🟡", "reject": "🔴"}
_REC_LABEL = {
    "evaluate": "Evaluate — initiate formal assessment",
    "monitor": "Monitor — track, no immediate action",
    "reject": "Reject — not relevant or not compliant",
}


def _render_confidence_banner(source_type: str):
    # Intelligence confidence depends on source quality
    tier = "Medium"
    basis = f"Open-source {source_type}. LLM-extracted claims. No independent verification."
    what_changes = (
        "Corroboration from a second independent source, or FE confirmation of "
        "technical claims, would move to High confidence."
    )
    tier_color = {"High": "#39d353", "Medium": "#e3b341", "Low": "#f85149"}[tier]
    st.markdown(
        f"<div style='border-left: 3px solid {tier_color}; padding: 6px 12px; margin-bottom: 8px;'>"
        f"<small><b style='color:{tier_color}'>ANALYTIC CONFIDENCE: {tier.upper()}</b><br>"
        f"{basis}<br>"
        f"<i>What would change it:</i> {what_changes}</small>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_assessment_card(name: str, analysis: ProductAnalysis, assessment: DanishAssessment,
                             source_type: str = ""):
    briefing = st.session_state.get("briefing_mode", False)

    if briefing:
        # Briefing mode: clean decision-ready card, no technical detail
        rec = assessment.recommendation
        st.markdown(f"### {name}")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**What it does:** {analysis.core_capability}")
            st.markdown(f"**Why it matters for Denmark:** {assessment.relevance}")
            st.markdown(f"**Next step:** {assessment.next_step}")
        with col2:
            st.markdown(f"**{_REC_COLOR[rec]} {_REC_LABEL[rec]}**")
            flags = []
            if assessment.itar_flag:
                flags.append("🇺🇸 ITAR")
            if assessment.dual_use_flag:
                flags.append("🇪🇺 Dual-use")
            if assessment.classification_concern:
                flags.append("🔒 Classification")
            if flags:
                st.markdown("  ".join(flags))
        _render_confidence_banner(source_type or "document")
        return

    st.markdown(f"### {name}")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Core capability:** {analysis.core_capability}")
        st.markdown(f"**Relevance:** {assessment.relevance}")
        st.markdown(f"**Fit:** {assessment.fit}")
        st.markdown(f"**Acquisition pathway:** {assessment.acquisition_pathway}")
        st.markdown(f"**Next step:** {assessment.next_step}")

    with col2:
        rec = assessment.recommendation
        st.markdown(f"**Recommendation**\n\n{_REC_COLOR[rec]} {_REC_LABEL[rec]}")
        flags = []
        if assessment.itar_flag:
            flags.append("🇺🇸 ITAR")
        if assessment.dual_use_flag:
            flags.append("🇪🇺 Dual-use")
        if assessment.classification_concern:
            flags.append("🔒 Classification")
        st.markdown("**Compliance flags**\n\n" + ("  ".join(flags) if flags else "None flagged"))

    with st.expander("Risk & compliance summary"):
        st.markdown(assessment.risk_summary)

    if analysis.flagged_claims:
        with st.expander(f"Flagged claims ({len(analysis.flagged_claims)})"):
            for c in analysis.flagged_claims:
                badge = {"substantiated": "✅", "plausible": "🔵",
                         "unsubstantiated": "⚠️", "marketing": "📣"}[c.credibility]
                st.markdown(f"{badge} **{c.credibility.upper()}** — {c.claim}")
                if c.verification_query:
                    st.caption(f"Verification: {c.verification_query}")


def _render_comparison_table(products: list[dict]):
    st.subheader("Multi-Product Comparison")
    rows = []
    for p in products:
        a: DanishAssessment = p["assessment"]
        rows.append({
            "Product": p["name"],
            "Recommendation": f"{_REC_COLOR[a.recommendation]} {a.recommendation.upper()}",
            "ITAR": "Yes" if a.itar_flag else "No",
            "Dual-use": "Yes" if a.dual_use_flag else "No",
            "Class. concern": "Yes" if a.classification_concern else "No",
            "Next step": a.next_step[:80] + ("…" if len(a.next_step) > 80 else ""),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render():
    st.header("Defence Intelligence")
    st.caption(
        "Feed a URL, PDF, or text snippet — get a structured product analysis "
        "and acquisition-relevant Danish defence assessment. "
        "Accumulate multiple products to compare side-by-side."
    )

    if "products" not in st.session_state:
        st.session_state["products"] = []

    col_in, col_cfg = st.columns([3, 1])

    with col_cfg:
        input_type = st.radio("Input", ["URL", "PDF", "Text"])
        provider = st.selectbox(
            "LLM",
            list(_PROVIDERS.keys()),
            format_func=lambda k: _PROVIDERS[k],
        )
        product_label = st.text_input(
            "Product label (for comparison table)",
            placeholder="e.g. TERMA ALQ-213",
        )

    with col_in:
        url_val = pdf_val = text_val = None
        if input_type == "URL":
            url_val = st.text_input("URL", placeholder="https://...")
        elif input_type == "PDF":
            pdf_val = st.file_uploader("Upload PDF", type=["pdf"])
        else:
            text_val = st.text_area(
                "Paste content",
                height=180,
                placeholder="Product description, spec sheet excerpt, press release, RFI text...",
            )

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        run_btn = st.button("Analyse", type="primary")
    with col_btn2:
        if st.button("Clear all products") and st.session_state["products"]:
            st.session_state["products"] = []
            st.rerun()

    if not run_btn:
        # Show any previously accumulated products
        if st.session_state["products"]:
            if len(st.session_state["products"]) > 1:
                _render_comparison_table(st.session_state["products"])
                st.divider()
            for p in st.session_state["products"]:
                _render_assessment_card(p["name"], p["analysis"], p["assessment"],
                                        p.get("source_type", "document"))
                st.divider()
        return

    # Load content
    try:
        with st.spinner("Loading content..."):
            if input_type == "URL":
                if not url_val or not url_val.strip():
                    st.error("Enter a URL.")
                    return
                content = load_url(url_val.strip())
                source_type = "web page"
            elif input_type == "PDF":
                if not pdf_val:
                    st.error("Upload a PDF.")
                    return
                content = load_pdf_bytes(pdf_val.read())
                source_type = "PDF document"
            else:
                if not text_val or not text_val.strip():
                    st.error("Paste some content.")
                    return
                content = load_text(text_val)
                source_type = "text snippet"
    except Exception as e:
        st.error(f"Failed to load content: {e}")
        return

    with st.expander("Extracted content preview", expanded=False):
        preview = content[:3000]
        if len(content) > 3000:
            preview += f"\n\n… ({len(content) - 3000} more characters truncated)"
        st.text(preview)

    try:
        llm = get_llm(provider)
    except EnvironmentError as e:
        st.error(str(e))
        return

    # Three-step agentic pipeline with visible reasoning trace
    analysis = assessment = None
    verification_steps = []

    progress = st.empty()

    try:
        progress.info("Step 1/3 — Extracting structured product analysis…")
        analysis, assessment, verification_steps = run_structured(content, source_type, llm)
        progress.empty()
    except Exception as e:
        progress.empty()
        st.error(f"Pipeline error: {e}")
        return

    # Show reasoning trace if there were verification steps
    if verification_steps:
        with st.expander(f"Reasoning trace — {len(verification_steps)} claims verified", expanded=True):
            st.caption("Claims marked unsubstantiated or marketing triggered a targeted verification query.")
            for i, (claim, question) in enumerate(verification_steps, 1):
                st.markdown(f"**Claim {i}:** {claim}")
                st.markdown(f"**Verification query:** {question}")
                st.divider()

    # Store and display
    label = product_label.strip() if product_label.strip() else analysis.product_name
    st.session_state["products"].append({
        "name": label,
        "analysis": analysis,
        "assessment": assessment,
        "source_type": source_type,
    })

    if len(st.session_state["products"]) > 1:
        _render_comparison_table(st.session_state["products"])
        st.divider()

    for p in st.session_state["products"]:
        _render_assessment_card(p["name"], p["analysis"], p["assessment"],
                                p.get("source_type", "document"))
        st.divider()
