from pydantic import BaseModel, Field
from typing import Literal
from app.schemas.calculation import CalculationSpecification


class ParsedChartSpecification(BaseModel):
    figure_id: int
    x: str
    y: str


class ReportSpecification(BaseModel):
    source_section: str | None = None

    calculations: list[CalculationSpecification] = Field(
        default_factory=list
    )

    charts: list[ParsedChartSpecification] = Field(
        default_factory=list
    )
    
class UpdateExampleRowRequest(BaseModel):
    row_index: int
    
    

    
