from pydantic import BaseModel, Field


class SectionTextContent(BaseModel):
    section_id: int
    description: str
    analysis: str
    
class ReportTextContent(BaseModel):
    purpose: str

    setup_description: str

    theory: str | None = None

    sections: list[SectionTextContent] = Field(
        default_factory=list
    )

    conclusions: str
    
class UpdateReportTextRequest(BaseModel):
    purpose: str
    setup_description: str
    theory: str | None = None
    sections: list[SectionTextContent]
    conclusions: str