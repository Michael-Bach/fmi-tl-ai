"""
Teknisk Notat Generator

Drafts structured Danish defence technical notes (tekniske notater) for FMI TEW
decision-makers and programme managers.

Uses claude-opus-4-8 with extended thinking so the reasoning chain behind
each assessment is visible — the thinking blocks are rendered in a collapsible
expander alongside the finished document.

Prompt caching is applied to DANISH_DEFENCE_CONTEXT so the ~750-token system
block is served from cache on repeat calls within the 5-minute window.
"""
import json
import re

import streamlit as st

_CLASSIFICATION_LEVELS = [
    "NATO UNCLASSIFIED",
    "TIL TJENESTEBRUG (NATO RESTRICTED)",
    "FORTROLIGT (NATO CONFIDENTIAL)",
]

_URGENCY_LABELS = ["Routine", "Priority", "Immediate"]

_EXAMPLE_TOPICS = [
    "AI-based ELINT classification readiness for maritime patrol aircraft",
    "Technology readiness of RL-adaptive jamming for F-35A EW upgrade",
    "Procurement risk: SHORAD C-UAS capability gap — cost of continued inaction",
    "Allied M&S overlap assessment: Denmark vs. FFI ALERT suite",
    "EMCON tooling gap — JEMSO staff skill requirement vs. available software",
]

# Template uses {{ }} to escape literal JSON braces; single { } are Python format args.
_NOTAT_PROMPT = """\
You are the Team Lead for AI, Modelling and Simulation at FMI TEW \
(Danish Defence Acquisition and Logistics Organisation — Electronic Warfare section). \
Your task is to draft a Teknisk Notat — a structured advisory memo for Danish defence \
acquisition decision-makers and programme managers. \
The audience is NOT engineers: they need clear findings, explicit risk flags, \
and numbered actionable recommendations.

Topic: {topic}
Classification: {classification}
Requesting unit: {requesting_unit}
Urgency: {urgency}
Additional context: {context}

Return ONLY a JSON object with this exact structure. \
No markdown fences, no other text before or after the JSON:
{{
  "classification": "{classification}",
  "from_unit": "FMI TEW — AI, Modellering og Simulering",
  "to_unit": "{requesting_unit}",
  "subject": "<concise subject line, max 12 words>",
  "executive_summary": "<STRICTLY ≤ 150 words. Self-contained. Decision-ready. Define all acronyms.>",
  "background": "<1–2 paragraphs. Operational and technical context. Why this matters now.>",
  "technical_analysis": "<Detailed analysis. Cite specific technologies, performance parameters, Allied capability context, and gaps. Flag ITAR, dual-use, and classification concerns explicitly.>",
  "findings": [
    "<specific, evidence-backed finding 1>",
    "<specific, evidence-backed finding 2>"
  ],
  "recommendations": [
    "1. <Actionable recommendation. Name the responsible party, e.g. FMI TEW / programme office / FFI bilateral.>",
    "2. <Next recommendation>",
    "3. <Third if warranted>"
  ],
  "limitations_and_uncertainties": [
    "<Data gap, assumption, or unclassified boundary that constrains this assessment>",
    "<Second limitation if applicable>"
  ],
  "classification_handling_note": "<Handling instructions matching the stated classification level>"
}}

Hard constraints:
• executive_summary MUST be ≤ 150 words (count carefully)
• recommendations MUST name a responsible party
• findings MUST be specific, not generic platitudes
• Flag ITAR, dual-use, and classification issues explicitly in technical_analysis
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Extract a JSON object from LLM output, handling common wrapping patterns."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


def _word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def _render_notat(doc: dict):
    """Render a parsed notat dict as a formatted document in Streamlit."""
    exec_sum  = doc.get("executive_summary", "")
    wc        = _word_count(exec_sum)
    wc_color  = "#e3b341" if wc > 150 else "#39d353"

    # Classification banner
    cls = doc.get("classification", "—")
    banner_bg = "#3d1a1a" if "FORTROLIGT" in cls else (
                "#2a2a0d" if "TJENESTEBRUG" in cls else "#0d1a0d")
    st.markdown(
        f"<div style='background:{banner_bg}; padding:6px 12px; border-radius:4px; "
        f"font-family:Courier New; font-size:13px; letter-spacing:1px; margin-bottom:12px;'>"
        f"&#9632; {cls}</div>",
        unsafe_allow_html=True,
    )

    col_from, col_to = st.columns(2)
    with col_from:
        st.markdown(f"**FRA:** {doc.get('from_unit', '—')}")
    with col_to:
        st.markdown(f"**TIL:** {doc.get('to_unit', '—')}")
    st.markdown(f"**EMNE:** {doc.get('subject', '—')}")
    st.divider()

    # Executive summary with word-count badge
    st.markdown(
        f"<div style='background:#161b22; padding:12px 16px; "
        f"border-left:3px solid {wc_color}; border-radius:0 4px 4px 0; margin-bottom:16px;'>"
        f"<span style='font-family:Courier New; font-size:11px; color:{wc_color};'>"
        f"RESUMÉ &nbsp;·&nbsp; {wc} ord</span><br><br>"
        f"<span style='font-size:14px;'>{exec_sum}</span></div>",
        unsafe_allow_html=True,
    )

    # Main sections
    with st.expander("1. BAGGRUND", expanded=True):
        st.markdown(doc.get("background", "—"))

    with st.expander("2. TEKNISK ANALYSE", expanded=True):
        st.markdown(doc.get("technical_analysis", "—"))

    # Findings
    findings = doc.get("findings", [])
    if findings:
        st.subheader("3. FUND")
        for i, f in enumerate(findings, 1):
            st.markdown(
                f"<div style='background:#161b22; padding:8px 12px; margin-bottom:6px; "
                f"border-radius:4px; border-left:2px solid #58a6ff;'>"
                f"<b>F{i}</b> &nbsp; {f}</div>",
                unsafe_allow_html=True,
            )

    # Recommendations
    recs = doc.get("recommendations", [])
    if recs:
        st.subheader("4. ANBEFALINGER")
        for r in recs:
            st.markdown(
                f"<div style='background:#0f2a1a; padding:8px 12px; margin-bottom:6px; "
                f"border-radius:4px; border-left:2px solid #39d353;'>{r}</div>",
                unsafe_allow_html=True,
            )

    # Limitations
    lims = doc.get("limitations_and_uncertainties", [])
    if lims:
        with st.expander("5. FORBEHOLD OG USIKKERHEDER"):
            for lim in lims:
                st.markdown(f"- {lim}")

    handling = doc.get("classification_handling_note", "")
    if handling:
        st.caption(f"Håndteringsvejledning: {handling}")


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def _generate(topic, classification, requesting_unit, urgency, context):
    from workflow.llm import get_native_client, THINKING_MODEL
    from workflow.context import get_cached_system_blocks

    client = get_native_client()
    prompt = _NOTAT_PROMPT.format(
        topic=topic,
        classification=classification,
        requesting_unit=requesting_unit,
        urgency=urgency,
        context=context,
    )

    with st.spinner(f"Generating — {THINKING_MODEL} with extended thinking…"):
        response = client.messages.create(
            model=THINKING_MODEL,
            max_tokens=16000,
            thinking={"type": "enabled", "budget_tokens": 8000},
            system=get_cached_system_blocks(),
            messages=[{"role": "user", "content": prompt}],
        )

    thinking_blocks = [b for b in response.content if b.type == "thinking"]
    text_blocks     = [b for b in response.content if b.type == "text"]

    # Cache / usage metrics
    usage = response.usage
    cache_read    = getattr(usage, "cache_read_input_tokens", 0)
    cache_created = getattr(usage, "cache_creation_input_tokens", 0)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Input tokens", f"{usage.input_tokens:,}")
    col_m2.metric("Output tokens", f"{usage.output_tokens:,}")
    col_m3.metric("Cache read", f"{cache_read:,}",
                  help="Tokens served from prompt cache (no cost)")
    col_m4.metric("Cache created", f"{cache_created:,}",
                  help="Tokens written to cache this call")

    # Thinking trace
    if thinking_blocks:
        total_chars = sum(len(b.thinking) for b in thinking_blocks)
        with st.expander(
            f"Model reasoning — {THINKING_MODEL} extended thinking "
            f"({total_chars:,} chars)",
            expanded=False,
        ):
            for i, tb in enumerate(thinking_blocks, 1):
                if len(thinking_blocks) > 1:
                    st.caption(f"Thinking block {i}")
                st.markdown(
                    f"<pre style='font-size:11px; color:#8b949e; background:#161b22; "
                    f"padding:10px; border-radius:4px; overflow-x:auto; "
                    f"white-space:pre-wrap;'>{tb.thinking}</pre>",
                    unsafe_allow_html=True,
                )

    # Parse and render document
    raw_text = "".join(b.text for b in text_blocks)
    doc = _extract_json(raw_text)

    if not doc:
        st.error("Could not parse structured output from model response.")
        with st.expander("Raw response"):
            st.code(raw_text, language="text")
        return

    st.divider()
    _render_notat(doc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def render():
    st.header("Teknisk Notat Generator")
    st.caption(
        "AI-assisted drafting of structured technical notes for FMI TEW decision-makers. "
        f"Model: claude-opus-4-8 with extended thinking. "
        "Reasoning trace is shown below the finished document."
    )

    col_left, col_right = st.columns([3, 2])

    with col_left:
        topic = st.text_area(
            "Topic / question",
            height=110,
            placeholder=_EXAMPLE_TOPICS[0],
            key="notat_topic_input",
            help="Describe the technology, capability, or procurement question.",
        )

    with col_right:
        classification    = st.selectbox("Classification", _CLASSIFICATION_LEVELS)
        requesting_unit   = st.text_input("Requesting unit", value="FMI Programme Office")
        urgency           = st.selectbox("Urgency", _URGENCY_LABELS)

    extra = st.text_area(
        "Additional context (optional)",
        height=60,
        placeholder="Relevant programme, budget constraint, Allied context, deadline…",
        key="notat_extra_input",
    )

    with st.expander("Example topics — click to load"):
        for ex in _EXAMPLE_TOPICS:
            if st.button(ex, key=f"notat_ex_{hash(ex)}"):
                st.session_state["notat_topic_input"] = ex
                st.rerun()

    effective_topic = st.session_state.get("notat_topic_input", "") or topic

    if st.button(
        "Generate Teknisk Notat",
        type="primary",
        disabled=not effective_topic.strip(),
    ):
        _generate(
            effective_topic.strip(),
            classification,
            requesting_unit,
            urgency,
            extra.strip() or "None provided",
        )
