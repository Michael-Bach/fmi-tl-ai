from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .context import DANISH_DEFENCE_CONTEXT

_ANALYZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a defence technology analyst. Extract a structured, technically precise "
        "analysis from the provided content. Focus on what the product or technology "
        "actually does, its claimed performance, and its intended operational use cases. "
        "Be concise. Flag anything that appears to be marketing language without "
        "substantive backing."
    )),
    ("human", (
        "Source type: {source_type}\n\n"
        "Content:\n{content}\n\n"
        "Provide a structured analysis covering:\n"
        "1. Core capability — what this does\n"
        "2. Key technical specifications or claims\n"
        "3. Intended use cases and operational scenarios\n"
        "4. Vendor or source positioning\n"
        "5. Notable gaps, uncertainties, or unsubstantiated claims"
    )),
])

_COMPARE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a Danish defence acquisition advisor at FMI TEW "
        "(Team Lead, AI Modellering og Simulering). "
        "Assess products and technologies against the Danish defence context with "
        "acquisition-relevant directness. "
        "Flag ITAR, classification, interoperability, and industrial policy issues explicitly. "
        "Your audience is programme managers and senior FMI staff — not engineers."
    )),
    ("human", (
        "Product analysis:\n{analysis}\n\n"
        "Danish Defence Context:\n{context}\n\n"
        "Assess this against the Danish defence context:\n"
        "1. Relevance — which Danish capability gaps or Forsvarsforlig priorities does this address?\n"
        "2. Fit — alignment with existing Danish systems and NATO/Nordic interoperability requirements\n"
        "3. Acquisition pathway — which FMI office or Forsvaret entity would own this; "
        "does a kravspecifikation process exist or need to be initiated?\n"
        "4. Risk and compliance — ITAR, dual-use, classification level, industrial policy\n"
        "5. Recommendation — is further evaluation warranted? If yes, what is the next concrete step?"
    )),
])


def run(content: str, source_type: str, llm) -> tuple[str, str]:
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
