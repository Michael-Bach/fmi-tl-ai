import streamlit as st
from workflow.llm import get_llm
from workflow.loaders import load_url, load_pdf_bytes, load_text
from workflow.pipeline import run

_PROVIDERS = {"anthropic": "Claude (Anthropic)", "mistral": "Mistral"}


def render():
    st.header("Defence Intelligence")
    st.caption(
        "Feed a URL, PDF, or text snippet — get a structured product analysis "
        "and an acquisition-relevant assessment against the Danish defence context."
    )

    col_in, col_cfg = st.columns([3, 1])

    with col_cfg:
        input_type = st.radio("Input", ["URL", "PDF", "Text"])
        provider = st.selectbox(
            "LLM",
            list(_PROVIDERS.keys()),
            format_func=lambda k: _PROVIDERS[k],
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
                height=220,
                placeholder="Product description, spec sheet excerpt, press release, RFI text...",
            )

    run_btn = st.button("Analyse", type="primary")

    if not run_btn:
        return

    # --- load ---
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

    with st.expander("Extracted content", expanded=False):
        preview = content[:3000]
        if len(content) > 3000:
            preview += f"\n\n… ({len(content) - 3000} more characters truncated)"
        st.text(preview)

    # --- analyse ---
    try:
        llm = get_llm(provider)
    except EnvironmentError as e:
        st.error(str(e))
        return

    try:
        with st.spinner("Analysing product / technology..."):
            analysis, comparison = run(content, source_type, llm)
    except Exception as e:
        st.error(f"LLM error: {e}")
        return

    st.subheader("Product / Technology Analysis")
    st.markdown(analysis)

    st.divider()

    st.subheader("Danish Defence Assessment")
    st.markdown(comparison)
