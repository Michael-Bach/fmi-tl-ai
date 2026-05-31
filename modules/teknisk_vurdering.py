"""
Teknisk Vurdering — advisory report generator.

Addresses: "Udarbejde tekniske notater, vurderinger og rapporter
til beslutningstagere i FMI og Forsvaret."

Distinct from the kravspecifikation generator (which produces a procurement
requirement). A teknisk vurdering is a standing advisory product:
background → technical analysis → maturity assessment → recommendation → limitations.
"""
import datetime
import streamlit as st


_SYSTEM_PROMPT = (
    "Du er en teknisk rådgiver hos Forsvarsministeriets Materiel- og Indkøbsstyrelse (FMI), "
    "Taktisk Elektronisk Krigsførelse (TEW), AI Modellering og Simulering. "
    "Din opgave er at udarbejde en teknisk vurdering i FMI's standardformat. "
    "Produktet henvender sig til beslutningstagere: programledere, afdelingschefer og "
    "operative kapaciteter — ikke til ingeniører. "
    "Skriv præcist, kortfattet og på et niveau, der kan forstås af en erfaren officer "
    "uden teknisk baggrund, men som kræver teknisk underbygget dokumentation. "
    "Brug dansk som primært sprog. Tekniske termer kan angives på engelsk i parentes. "
    "Format: Baggrund → Teknisk analyse → Modenhedsvurdering → Risici og begrænsninger → Anbefaling."
)

_HUMAN_PROMPT = """
Teknologi / produkt / spørgsmål: {subject}

Kontekst og anskaffelsesrelevans: {context}

Simulerings- eller analyseresultater (hvis tilgængelig): {evidence}

Yderligere oplysninger: {additional}

Udarbejd en teknisk vurdering med følgende sektioner:

**1. Baggrund**
[Hvad er spørgsmålet? Hvem har stillet det og hvorfor?]

**2. Teknisk analyse**
[Hvad gør teknologien/produktet? Nøglespecifikationer og påstande. Hvad understøttes af fysik/data, hvad er marketingsprog?]

**3. Modenhedsvurdering (TRL)**
[Nuværende teknologisk modenhed. Hvad mangler for operationel deployment?]

**4. Risici og begrænsninger**
[ITAR, klassifikation, interoperabilitet, industripolitik, usikkerhed i analysen.]

**5. Anbefaling**
[Ét klart råd: evaluér videre / overvåg / afvis. Næste konkrete skridt — hvem gør hvad?]

**Analytisk tillid:** [Høj / Mellem / Lav — med begrundelse]
"""


def render():
    st.header("Teknisk Vurdering — Rådgivningsrapport")
    st.caption(
        "Genererer en teknisk vurdering i FMI-format: "
        "baggrund, teknisk analyse, modenhedsvurdering, risici, anbefaling. "
        "Til beslutningstagere — ikke ingeniører. "
        "Implementerer: 'Udarbejde tekniske notater, vurderinger og rapporter til beslutningstagere'."
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

        doc_id = st.text_input("Dokument ID", value="FMI-TEW-TV-001")
        classification = st.selectbox(
            "Klassifikation",
            ["IKKE-KLASSIFICERET", "TIL TJENESTEBRUG", "FORTROLIGT"],
        )

    with col_in:
        subject = st.text_input(
            "Teknologi / produkt / spørgsmål",
            placeholder="fx 'TERMA ALQ-213 self-protection jammer ERP claim' eller "
                        "'AI-baseret radaranomalidetektion til maritim ISR'",
        )
        context = st.text_area(
            "Kontekst og anskaffelsesrelevans",
            height=80,
            placeholder="fx 'F-35A EW upgrade programme. Programleder ønsker vurdering af "
                        "leverandørens J/S-påstand inden kravspec underskrives.'",
        )
        evidence = st.text_area(
            "Simulerings- eller analyseresultater",
            height=80,
            placeholder="fx 'Simulation viser J/S 85 dB ved 80 km mod 55 dBW radar. "
                        "Leverandørens påstand: J/S 15 dB ved 50 km — indebærer 125 dBW radar (urealistisk).'",
        )
        additional = st.text_area(
            "Yderligere oplysninger (valgfrit)",
            height=60,
            placeholder="fx 'FFI har lignende analyse. ITAR-kontrolleret teknologi.'",
        )

    gen_btn = st.button("Generer teknisk vurdering", type="primary")
    if not gen_btn:
        return

    if not subject.strip():
        st.error("Angiv teknologi/produkt/spørgsmål.")
        return

    try:
        from workflow.llm import get_llm
        llm = get_llm(provider)
    except EnvironmentError as e:
        st.error(str(e))
        return

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", _HUMAN_PROMPT),
    ])

    try:
        with st.spinner("Genererer teknisk vurdering…"):
            parser = StrOutputParser()
            result = (prompt | llm | parser).invoke({
                "subject":    subject.strip(),
                "context":    context.strip() or "Ikke specificeret.",
                "evidence":   evidence.strip() or "Ingen simuleringsdata vedlagt.",
                "additional": additional.strip() or "Ingen yderligere oplysninger.",
            })

        date_str = datetime.date.today().strftime("%d. %b %Y")
        header = (
            f"# Teknisk Vurdering\n\n"
            f"**Dokument:** {doc_id}  |  **Dato:** {date_str}  |  "
            f"**Klassifikation:** {classification}\n\n"
            f"**Emne:** {subject}\n\n---\n\n"
        )
        full_report = header + result

        st.markdown(full_report)
        st.divider()
        st.download_button(
            "Download teknisk vurdering (.md)",
            data=full_report,
            file_name=f"{doc_id.lower().replace('-', '_')}_{datetime.date.today().isoformat()}.md",
            mime="text/markdown",
        )

    except Exception as e:
        st.error(f"LLM fejl: {e}")
