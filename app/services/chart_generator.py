from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from app.schemas.chart import ChartSpecification
from app.schemas.report import ReportSpecification

from app.services.excel_reader import (
    MeasurementTableData,
    get_chart_data,
    get_measurement_table,
)

def create_multi_table_chart_specifications(
    specification: ReportSpecification,
    tables: list[MeasurementTableData],
) -> list[ChartSpecification]:

    charts: list[ChartSpecification] = []

    assigned_figure_ids = {
        figure_id
        for section in specification.sections
        for figure_id in section.chart_figure_ids
    }

    for parsed_chart in specification.charts:

        if parsed_chart.figure_id not in assigned_figure_ids:
            raise ValueError(
                f"Chart figure_id={parsed_chart.figure_id} "
                "is not assigned to any report section."
            )

        table = get_measurement_table(
            tables=tables,
            table_id=parsed_chart.table_id,
        )

        available_columns = set(
            table.dataframe.columns
        )

        if parsed_chart.x not in available_columns:
            raise ValueError(
                f"Chart figure_id={parsed_chart.figure_id} "
                f"uses x column '{parsed_chart.x}', "
                f"but table_id={parsed_chart.table_id} "
                f"contains columns: "
                f"{table.dataframe.columns.tolist()}"
            )

        if parsed_chart.y not in available_columns:
            raise ValueError(
                f"Chart figure_id={parsed_chart.figure_id} "
                f"uses y column '{parsed_chart.y}', "
                f"but table_id={parsed_chart.table_id} "
                f"contains columns: "
                f"{table.dataframe.columns.tolist()}"
            )
            
     

        charts.append(
            ChartSpecification(
                figure_id=parsed_chart.figure_id,
                table_id=parsed_chart.table_id,
                x=parsed_chart.x,
                y=parsed_chart.y,
                filter_column=parsed_chart.filter_column,
                filter_value=parsed_chart.filter_value,
                label=parsed_chart.label,
            )
        )

    return charts
        

def match_column_name(column_name:str, df) -> str:
    if column_name in df:
        return column_name
    
    matches = [
        col for col in df.columns if col.lower() == column_name.lower()
    ]
    
    if len(matches) == 1:
        return matches[0]
    
    raise ValueError(
        f"Unable to find column '{column_name}'. "
        f"Available columns: {df.columns.tolist()}")
    

def generate_chart(
    tables: list[MeasurementTableData],
    charts: list[ChartSpecification],
    output_dir: Path,
) -> list[Path]:

    grouped_charts = defaultdict(list)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_files: list[Path] = []

    for chart in charts:
        grouped_charts[
            chart.figure_id
        ].append(
            chart
        )

    for figure_id, figure_charts in grouped_charts.items():

        if not figure_charts:
            continue

        shared_x = figure_charts[0].x

        for chart in figure_charts:

            if chart.x != shared_x:
                raise ValueError(
                    f"Figure {figure_id} requires "
                    f"a common x-axis, but found "
                    f"'{shared_x}' and '{chart.x}'."
                )

        first_table = get_measurement_table(
            tables=tables,
            table_id=figure_charts[0].table_id,
        )

        fig, ax = plt.subplots()

        ax.set_xscale(
            figure_charts[0].x_scale
        )

        if len(figure_charts) > 1:
            fig.subplots_adjust(
                right=0.75
            )

        axes = [ax]

        for index in range(
            1,
            len(figure_charts),
        ):

            new_ax = ax.twinx()

            if index > 1:
                new_ax.spines.right.set_position(
                    (
                        "axes",
                        1 + 0.2 * (index - 1),
                    )
                )

            axes.append(
                new_ax
            )

        lines = []
        title_variables: list[str] = []

        colors = (
            plt.rcParams[
                "axes.prop_cycle"
            ]
            .by_key()["color"]
        )

        for index, (
            chart,
            current_ax,
        ) in enumerate(
            zip(
                figure_charts,
                axes,
            )
        ):

            table = get_measurement_table(
                tables=tables,
                table_id=chart.table_id,
            )

            df = table.dataframe

            if chart.filter_column is not None:

                if chart.filter_column not in df.columns:
                    raise ValueError(
                        f"Chart figure_id={chart.figure_id} "
                        f"uses filter column "
                        f"'{chart.filter_column}', "
                        f"but table_id={chart.table_id} "
                        f"contains columns: "
                        f"{df.columns.tolist()}"
                    )

                if chart.filter_value is None:
                    raise ValueError(
                        f"Chart figure_id={chart.figure_id} "
                        "defines filter_column but "
                        "filter_value is missing."
                    )

                filter_series = df[
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

                    df = df[
                        np.isclose(
                            numeric_filter,
                            float(chart.filter_value),
                            rtol=1e-6,
                            atol=1e-9,
                            equal_nan=False,
                        )
                    ]

                else:

                    df = df[
                        filter_series.astype(str)
                        == str(chart.filter_value)
                    ]


            x, y = get_chart_data(
                df,
                chart.x,
                chart.y,
            )

            if len(x) == 0 or len(y) == 0:
                raise ValueError(
                    f"No valid data for chart "
                    f"{chart.y}({chart.x}) "
                    f"from table_id={chart.table_id}."
                )

            if (
                chart.y_scale == "log"
                and (y <= 0).any()
            ):
                raise ValueError(
                    f"Cannot use logarithmic "
                    f"scale for '{chart.y}' "
                    f"because values <= 0 exist."
                )

            current_ax.set_yscale(
                chart.y_scale
            )

            title_variables.append(
                chart.y
            )

            color = colors[
                index % len(colors)
            ]

            label = (
                chart.label
                or f"{chart.y}({chart.x})"
            )

            if chart.connect_points:

                line, = current_ax.plot(
                    x,
                    y,
                    marker="o",
                    color=color,
                    label=label,
                )

            else:

                line = current_ax.scatter(
                    x,
                    y,
                    color=color,
                    label=label,
                )


            if (
                chart.y_scale == "linear"
                and y.min() >= 0
            ):

                locator = MaxNLocator(
                    nbins=6
                )

                ticks = locator.tick_values(
                    0,
                    y.max(),
                )

                max_tick = ticks[-1]

                current_ax.set_ylim(
                    0,
                    max_tick,
                )

                current_ax.set_yticks(
                    ticks
                )

            y_unit = table.units.get(
                chart.y
            )

            if y_unit is None:
                y_label = (
                    f"{chart.y} [-]"
                )
            else:
                y_label = (
                    f"{chart.y} "
                    f"[{y_unit}]"
                )

            current_ax.set_ylabel(
                y_label,
                color=color,
            )

            current_ax.tick_params(
                axis="y",
                colors=color,
            )

            lines.append(
                line
            )


        unique_title_variables = list(
            dict.fromkeys(
                title_variables
            )
        )

        if len(
            unique_title_variables
        ) > 1:

            title = ", ".join(
                unique_title_variables
            )

            ax.set_title(
                f"Charakterystyki {title} "
                f"w funkcji {shared_x}"
            )

        else:

            title = (
                unique_title_variables[0]
            )

            ax.set_title(
                f"Charakterystyka {title} "
                f"w funkcji {shared_x}"
            )


        if figure_charts[0].show_grid:
            ax.grid()

        if figure_charts[0].show_legend:
            ax.legend(
                handles=lines
            )

        x_unit = first_table.units.get(
            shared_x
        )

        if x_unit is None:
            ax.set_xlabel(
                f"{shared_x} [-]"
            )

        else:
            ax.set_xlabel(
                f"{shared_x} "
                f"[{x_unit}]"
            )

        file_path = (
            output_dir
            / f"figure_{figure_id}.png"
        )

        fig.savefig(
            file_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(
            fig
        )

        generated_files.append(
            file_path
        )

    return generated_files

def generate_multi_table_charts(
    specification: ReportSpecification,
    tables: list[MeasurementTableData],
    charts: list[ChartSpecification],
    output_dir: Path,
) -> list[Path]:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_files: list[Path] = []

    processed_figure_ids: set[int] = set()

    for section in specification.sections:

        for figure_id in section.chart_figure_ids:

            if figure_id in processed_figure_ids:
                continue

            figure_charts = [
                chart
                for chart in charts
                if chart.figure_id == figure_id
            ]

            if not figure_charts:
                continue

            files = generate_chart(
                tables=tables,
                charts=figure_charts,
                output_dir=output_dir,
            )

            generated_files.extend(
                files
            )

            processed_figure_ids.add(
                figure_id
            )

    return generated_files
        

