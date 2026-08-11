from pydantic import BaseModel, Field
from typing import Literal
from app.schemas.calculation import CalculationSpecification
from app.schemas.section import ReportSection

class ParsedChartSpecification(BaseModel):
    figure_id: int
    x: str
    y: str


class ReportSpecification(BaseModel):
    report_title: str | None = None
    source_section: str | None = None

    include_purpose: bool = True
    include_theory: bool = False
    include_setup: bool = True
    include_conclusions: bool = True

    calculations: list[CalculationSpecification] = Field(
        default_factory=list
    )

    charts: list[ParsedChartSpecification] = Field(
        default_factory=list
    )

    sections: list[ReportSection] = Field(
        default_factory=list
    )
    
class UpdateExampleRowRequest(BaseModel):
    row_index: int
    
    

    
