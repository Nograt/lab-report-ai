import numpy as np
import pandas as pd

from app.schemas.analysis import (
    ChartRelationshipAnalysis,
    ColumnAnalysis,
    SectionAnalysis,
)
from app.schemas.chart import ChartSpecification
from app.schemas.report import ReportSpecification
from app.schemas.section import ReportSection
from app.services.excel_reader import (
    MeasurementTableData,
    get_measurement_table,
)


def analyze_report_sections(
    specification: ReportSpecification,
    tables: list[MeasurementTableData],
    charts: list[ChartSpecification],
) -> list[SectionAnalysis]:

    analyses: list[SectionAnalysis] = []

    for section in specification.sections:

        section_table = get_measurement_table(
            tables=tables,
            table_id=section.table_id,
        )

        section_charts = [
            chart
            for chart in charts
            if chart.figure_id
            in section.chart_figure_ids
        ]

        analysis = analyze_section(
            df=section_table.dataframe,
            section=section,
            units=section_table.units,
            charts=section_charts,
            tables=tables,
        )

        analyses.append(
            analysis
        )

    return analyses


def analyze_section(
    df: pd.DataFrame,
    section: ReportSection,
    units: dict[str, str | None],
    charts: list[ChartSpecification],
    tables: list[MeasurementTableData],
) -> SectionAnalysis:

    column_analyses: list[
        ColumnAnalysis
    ] = []

    if section.table is not None:

        for column in section.table.columns:

            if column not in df.columns:
                continue

            numeric = pd.to_numeric(
                df[column],
                errors="coerce",
            ).dropna()

            if numeric.empty:
                continue

            column_analyses.append(
                ColumnAnalysis(
                    column=column,
                    unit=units.get(
                        column
                    ),
                    minimum=float(
                        numeric.min()
                    ),
                    maximum=float(
                        numeric.max()
                    ),
                    mean=float(
                        numeric.mean()
                    ),
                    first_value=float(
                        numeric.iloc[0]
                    ),
                    last_value=float(
                        numeric.iloc[-1]
                    ),
                )
            )

    chart_analyses: list[
        ChartRelationshipAnalysis
    ] = []

    for chart in charts:

        chart_table = get_measurement_table(
            tables=tables,
            table_id=chart.table_id,
        )

        chart_df = chart_table.dataframe
        
        if chart.filter_column is not None:

            if (
                chart.filter_column
                not in chart_df.columns
            ):
                raise ValueError(
                    f"Chart figure_id="
                    f"{chart.figure_id} "
                    f"uses filter column "
                    f"'{chart.filter_column}', "
                    f"but table_id="
                    f"{chart.table_id} "
                    f"contains columns: "
                    f"{chart_df.columns.tolist()}"
                )

            if chart.filter_value is None:
                raise ValueError(
                    f"Chart figure_id="
                    f"{chart.figure_id} "
                    "defines filter_column but "
                    "filter_value is missing."
                )

            filter_series = chart_df[
                chart.filter_column
            ]

            if isinstance(
                chart.filter_value,
                (int, float),
            ):

                numeric_filter = pd.to_numeric(
                    filter_series,
                    errors="coerce",
                )

                chart_df = chart_df[
                    np.isclose(
                        numeric_filter,
                        float(
                            chart.filter_value
                        ),
                        rtol=1e-6,
                        atol=1e-9,
                        equal_nan=False,
                    )
                ]

            else:

                chart_df = chart_df[
                    filter_series.astype(str)
                    == str(
                        chart.filter_value
                    )
                ]

        chart_analysis = (
            analyze_chart_relationship(
                df=chart_df,
                chart=chart,
            )
        )

        chart_analyses.append(
            chart_analysis
        )

    return SectionAnalysis(
        section_id=section.section_id,
        columns=column_analyses,
        charts=chart_analyses,
    )


def analyze_chart_relationship(
    df: pd.DataFrame,
    chart: ChartSpecification,
) -> ChartRelationshipAnalysis:

    if chart.x not in df.columns:
        raise ValueError(
            f"Chart figure_id="
            f"{chart.figure_id} "
            f"uses x column "
            f"'{chart.x}', "
            f"but table_id="
            f"{chart.table_id} "
            f"contains columns: "
            f"{df.columns.tolist()}"
        )

    if chart.y not in df.columns:
        raise ValueError(
            f"Chart figure_id="
            f"{chart.figure_id} "
            f"uses y column "
            f"'{chart.y}', "
            f"but table_id="
            f"{chart.table_id} "
            f"contains columns: "
            f"{df.columns.tolist()}"
        )

    data = pd.DataFrame(
        {
            "x": pd.to_numeric(
                df[chart.x],
                errors="coerce",
            ),
            "y": pd.to_numeric(
                df[chart.y],
                errors="coerce",
            ),
        }
    ).dropna()

    if data.empty:
        raise ValueError(
            f"No valid data for chart "
            f"{chart.y}({chart.x}) "
            f"from table_id="
            f"{chart.table_id}."
        )

    data = data.sort_values(
        "x"
    )

    x = data["x"]
    y = data["y"]

    differences = np.diff(
        y.to_numpy()
    )

    tolerance = 1e-12

    is_increasing = np.all(
        differences >= -tolerance
    )

    is_decreasing = np.all(
        differences <= tolerance
    )

    is_constant = np.all(
        np.abs(
            differences
        ) <= tolerance
    )

    monotonic = bool(
        is_increasing
        or is_decreasing
        or is_constant
    )

    if len(data) >= 2:

        slope = np.polyfit(
            x.to_numpy(),
            y.to_numpy(),
            1,
        )[0]

        if abs(slope) <= tolerance:
            overall_direction = (
                "constant"
            )

        elif slope > 0:
            overall_direction = (
                "increasing"
            )

        else:
            overall_direction = (
                "decreasing"
            )

    else:
        overall_direction = (
            "constant"
        )

    correlation: float | None = None

    if len(data) >= 2:

        value = x.corr(
            y
        )

        if pd.notna(
            value
        ):
            correlation = float(
                value
            )

    return ChartRelationshipAnalysis(
        figure_id=chart.figure_id,
        x=chart.x,
        y=chart.y,
        x_min=float(
            x.min()
        ),
        x_max=float(
            x.max()
        ),
        y_min=float(
            y.min()
        ),
        y_max=float(
            y.max()
        ),
        y_at_min_x=float(
            y.iloc[0]
        ),
        y_at_max_x=float(
            y.iloc[-1]
        ),
        correlation=correlation,
        overall_direction=(
            overall_direction
        ),
        monotonic=monotonic,
    )