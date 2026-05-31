from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .context import DANISH_DEFENCE_CONTEXT
from .structured import ProductAnalysis, DanishAssessment

_ANALYZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a defence technology analyst. Extract a structured, technically precise "
        "analysis from the provided content. Focus on what the product or technology "
        "actually does, its claimed performance, and its intended operational use cases. "
        "Be concise. Flag anything that appears to be marketing language without "
        "substantive backing. For each flagged claim, provide a specific verification "
        "query — what you would search or request to independently validate it."
    )),
    ("human", (
        "Source type: {source_type}\n\n"
        "Content:\n{content}"
    )),
])

_COMPARE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a Danish defence acquisition advisor at FMI TEW "
        "(Team Lead, AI Modellering og Simulering). "
        "Assess products against the Danish defence context with acquisition-relevant directness. "
        "Flag ITAR, classification, interoperability, and industrial policy issues explicitly. "
        "Your audience is programme managers and senior FMI staff — not engineers. "
        "Be direct: if the product is not relevant, say so."
    )),
    ("human", (
        "Product analysis:\n{analysis}\n\n"
        "Danish Defence Context:\n{context}"
    )),
])

# Agentic step: for each flagged unsubstantiated claim, generate targeted counter-question
_VERIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a sceptical technical analyst reviewing a defence product claim. "
        "Generate a single, precise verification question or data request that would "
        "either substantiate or refute this claim. Be specific about what evidence is needed."
    )),
    ("human", "Claim: {claim}"),
])


_ADVERSARIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a sceptical senior military officer or programme manager reviewing a technical "
        "analysis or recommendation. Generate exactly 5 adversarial questions that a critical "
        "audience would ask to challenge the analysis — questions about assumptions, data quality, "
        "alternative explanations, resource implications, or operational relevance. "
        "For each question, provide a concise suggested answer and the most likely follow-up question. "
        "Format as a JSON array: "
        '[{"question": "...", "answer": "...", "follow_up": "..."}, ...]'
    )),
    ("human", "Analysis context:\n{context}"),
])


def generate_adversarial_qa(context: str, llm) -> list[dict]:
    """
    Generate 5 adversarial Q&A pairs for a given analysis context.
    Returns list of dicts with keys: question, answer, follow_up.
    """
    import json
    parser = StrOutputParser()
    raw = (_ADVERSARIAL_PROMPT | llm | parser).invoke({"context": context})
    # Extract JSON array from response
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    # Fallback: return raw as single item
    return [{"question": "Could not parse structured Q&A.", "answer": raw, "follow_up": ""}]


def run(content: str, source_type: str, llm) -> tuple[str, str]:
    """Legacy single-shot pipeline returning markdown strings."""
    parser = StrOutputParser()
    analysis = (_ANALYZE_PROMPT | llm | parser).invoke({
        "content": content,
        "source_type": source_type,
    })
    comparison = (_COMPARE_PROMPT | llm | parser).invoke({
        "analysis": analysis,
        "context": DANISH_DEFENCE_CONTEXT,
    })
    return analysis, comparison


def run_structured(
    content: str,
    source_type: str,
    llm,
) -> tuple[ProductAnalysis, DanishAssessment, list[tuple[str, str]]]:
    """
    Three-step agentic pipeline:
    1. Structured product analysis (Pydantic-enforced)
    2. Verification queries for each flagged/unsubstantiated claim
    3. Structured Danish defence assessment (Pydantic-enforced)

    Returns (analysis, assessment, verification_steps) where verification_steps is
    a list of (claim, verification_question) pairs for the visible reasoning trace.
    """
    # Step 1: Structured extraction
    analysis_llm = llm.with_structured_output(ProductAnalysis)
    analysis: ProductAnalysis = analysis_llm.invoke(
        _ANALYZE_PROMPT.format_messages(content=content, source_type=source_type)
    )

    # Step 2: For each claim marked unsubstantiated or marketing, generate a verification query
    parser = StrOutputParser()
    verification_steps: list[tuple[str, str]] = []
    for claim_check in analysis.flagged_claims:
        if claim_check.credibility in ("unsubstantiated", "marketing"):
            question = (_VERIFY_PROMPT | llm | parser).invoke({"claim": claim_check.claim})
            verification_steps.append((claim_check.claim, question.strip()))

    # Step 3: Structured assessment using the analysis + verification context
    analysis_text = (
        f"Product: {analysis.product_name}\n"
        f"Core capability: {analysis.core_capability}\n"
        f"Key specs: {'; '.join(analysis.key_specs)}\n"
        f"Use cases: {'; '.join(analysis.use_cases)}\n"
        f"Vendor positioning: {analysis.vendor_positioning}\n"
        f"Flagged claims: "
        + "; ".join(
            f"{c.claim} [{c.credibility}]" for c in analysis.flagged_claims
        )
    )
    assessment_llm = llm.with_structured_output(DanishAssessment)
    assessment: DanishAssessment = assessment_llm.invoke(
        _COMPARE_PROMPT.format_messages(
            analysis=analysis_text,
            context=DANISH_DEFENCE_CONTEXT,
        )
    )

    return analysis, assessment, verification_steps
