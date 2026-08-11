from app.schemas.section import ReportSection


section = ReportSection.model_validate(
    {
        "section_id": 3,
        "title": "Pomiary charakterystyk w stanie zwarcia",

        "table": {
            "title": "Wyniki pomiarów w stanie zwarcia",
            "columns": [
                "Lp",
                "Uk",
                "I",
                "P",
                "Pap",
                "PK",
                "cosφK",
                "Tl",
            ]
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


print(
    section.model_dump_json(
        indent=2
    )
)