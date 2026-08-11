from app.services.excel_reader import read_meansurements
from app.services.result_analyzer import analyze_section

from app.schemas.section import ReportSection
from app.schemas.chart import ChartSpecification


import numpy as np
import pandas as pd

from app.schemas.section import ReportSection
from app.schemas.chart import ChartSpecification

from app.schemas.analysis import (
    ColumnAnalysis,
    ChartRelationshipAnalysis,
    SectionAnalysis,
)


df, _ = read_meansurements(
    "storage/reports/4c363147-d7c4-4872-8938-e86984d26411/"
    "completed_measurements.xlsx"
)


units = {
    "Lp": None,
    "Uk": "V",
    "I": "A",
    "P": "W",
    "Pap": "W",
    "PK": "W",
    "cosφK": None,
    "Tl": "Nm",
}



section = ReportSection.model_validate(
    {
        "section_id": 1,
        "title": "Pomiary charakterystyk w stanie zwarcia",

        "table": {
            "title": "Wyniki pomiarów charakterystyk w stanie zwarcia",
            "columns": [
                "Lp",
                "Uk",
                "I",
                "P",
                "Pap",
                "PK",
                "cosφK",
                "Tl",
            ],
        },

        "calculation_outputs": [
            "PK",
            "cosφK",
        ],

        "chart_figure_ids": [
            1,
            2,
        ],

        "include_description": True,
        "include_analysis": True,
    }
)



charts = [
    ChartSpecification(
        figure_id=1,
        x="I",
        y="PK",
        connect_points=True,
        x_scale="linear",
        y_scale="linear",
        show_grid=True,
        show_legend=True,
    ),

    ChartSpecification(
        figure_id=2,
        x="I",
        y="cosφK",
        connect_points=True,
        x_scale="linear",
        y_scale="linear",
        show_grid=True,
        show_legend=True,
    ),
]



analysis = analyze_section(
    df=df,
    section=section,
    units=units,
    charts=charts,
)


print(
    analysis.model_dump_json(
        indent=2
    )
)