from typing import Literal

from pydantic import BaseModel


class ChartSpecification(BaseModel):
    figure_id: int
    x: str
    y: str

    connect_points: bool = True

    x_scale: Literal["linear", "log"] = "linear"
    y_scale: Literal["linear", "log"] = "linear"

    show_grid: bool = True
    show_legend: bool = True
    
class UpdateChartsRequest(BaseModel):
    charts: list[ChartSpecification]