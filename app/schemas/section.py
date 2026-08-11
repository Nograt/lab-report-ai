from pydantic import BaseModel, Field


class TableSpecification(BaseModel):
    title: str | None = None

    columns: list[str] = Field(
        default_factory=list
    )


class ReportSection(BaseModel):
    section_id: int
    title: str

    table: TableSpecification | None = None

    calculation_outputs: list[str] = Field(
        default_factory=list
    )

    chart_figure_ids: list[int] = Field(
        default_factory=list
    )

    include_description: bool = True
    include_analysis: bool = True