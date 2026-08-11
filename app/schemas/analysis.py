from typing import Literal
from pydantic import BaseModel, Field


class ColumnAnalysis(BaseModel):
    column: str
    unit: str | None = None

    minimum: float
    maximum: float
    mean: float

    first_value: float
    last_value: float


class ChartRelationshipAnalysis(BaseModel):
    figure_id: int

    x: str
    y: str

    x_min: float
    x_max: float

    y_min: float
    y_max: float

    y_at_min_x: float
    y_at_max_x: float

    correlation: float | None

    overall_direction: Literal[
        "increasing",
        "decreasing",
        "constant",
    ]

    monotonic: bool

class SectionAnalysis(BaseModel):
    section_id: int

    columns: list[ColumnAnalysis] = Field(
        default_factory=list
    )

    charts: list[ChartRelationshipAnalysis] = Field(
        default_factory=list
    )