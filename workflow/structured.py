from typing import Literal

from pydantic import BaseModel, Field


class ClaimCheck(BaseModel):
    claim: str = Field(description="The specific claim being assessed")
    credibility: Literal["substantiated", "plausible", "unsubstantiated", "marketing"] = Field(
        description="Credibility level of the claim"
    )
    verification_query: str = Field(
        description="What you would search or request to independently verify this claim"
    )


class ProductAnalysis(BaseModel):
    product_name: str = Field(description="Product or technology name extracted from content")
    core_capability: str = Field(description="What the product actually does in one sentence")
    key_specs: list[str] = Field(description="Technical specifications or claimed performance figures")
    use_cases: list[str] = Field(description="Intended operational use cases")
    vendor_positioning: str = Field(description="How the vendor or source frames this product")
    flagged_claims: list[ClaimCheck] = Field(description="Claims that require independent verification")


class DanishAssessment(BaseModel):
    relevance: str = Field(
        description="Which Danish capability gaps or Forsvarsforlig priorities this addresses"
    )
    fit: str = Field(
        description="Alignment with Danish systems and NATO/Nordic interoperability requirements"
    )
    acquisition_pathway: str = Field(
        description="Which FMI office would own this and whether a kravspecifikation exists or needs initiation"
    )
    itar_flag: bool = Field(description="True if US ITAR-controlled technology")
    dual_use_flag: bool = Field(description="True if EU dual-use export control (2021/821) applies")
    classification_concern: bool = Field(
        description="True if classified handling required for evaluation or integration"
    )
    recommendation: Literal["evaluate", "monitor", "reject"] = Field(
        description="Acquisition recommendation: evaluate = initiate formal assessment, "
                    "monitor = track but no action now, reject = not relevant or compliant"
    )
    next_step: str = Field(
        description="Concrete next action. Specific, actionable, names a responsible party."
    )
    risk_summary: str = Field(description="One-paragraph risk and compliance summary")
