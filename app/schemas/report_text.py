from pydantic import BaseModel


class SectionTextContent(BaseModel):
    section_id: int
    description: str
    analysis: str