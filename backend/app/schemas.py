from pydantic import BaseModel, Field
from enum import Enum

class DueDiligenceType(str, Enum):
    INVESTMENT = "Investment"
    ACQUISITION = "Acquisition"
    PARTNERSHIP = "Partnership"


class DueDiligenceRequest(BaseModel):
    company: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of the company to analyze"
    )

    due_diligence_type: DueDiligenceType