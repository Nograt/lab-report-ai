from typing import Literal

from pydantic import BaseModel


class ChartSpecification(BaseModel):
    figure_id: int
    table_id: int

    x: str
    y: str

    filter_column: str | None = None
    filter_value: float | str | None = None
    label: str | None = None

    connect_points: bool = True

    x_scale: Literal["linear", "log"] = "linear"
    y_scale: Literal["linear", "log"] = "linear"

    show_grid: bool = True
    show_legend: bool = True
    
class UpdateChartsRequest(BaseModel):
    charts: list[ChartSpecification]