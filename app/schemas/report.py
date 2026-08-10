from pydantic import BaseModel


class ParsedChartSpecification(BaseModel):
    figure_id: int
    x: str
    y: str


class ReportSpecification(BaseModel):
    source_section: str | None = None
    charts: list[ParsedChartSpecification]