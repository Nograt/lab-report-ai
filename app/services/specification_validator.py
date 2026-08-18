from app.schemas.measurement import MeasurementTableInfo
from app.schemas.report import ReportSpecification
from app.services.calculation_engine import (
    get_expression_dependencies,
)


def validate_report_specification(
    specification: ReportSpecification,
    measurement_tables: list[MeasurementTableInfo],
) -> None:

    available_table_ids = {
        table.table_id
        for table in measurement_tables
    }

    tables_by_id = {
        table.table_id: table
        for table in measurement_tables
    }

    for section in specification.sections:

        if section.table_id not in available_table_ids:
            raise ValueError(
                f"Section {section.section_id} references "
                f"unknown table_id={section.table_id}."
            )

    calculation_outputs_by_table: dict[
        int,
        set[str],
    ] = {}

    for calculation in specification.calculations:

        if calculation.table_id not in available_table_ids:
            raise ValueError(
                f"Calculation '{calculation.output}' references "
                f"unknown table_id={calculation.table_id}."
            )

        table_outputs = calculation_outputs_by_table.setdefault(
            calculation.table_id,
            set(),
        )

        if calculation.output in table_outputs:
            raise ValueError(
                f"Duplicate calculation output "
                f"'{calculation.output}' "
                f"for table_id={calculation.table_id}."
            )

        table_outputs.add(
            calculation.output
        )

    for calculation in specification.calculations:

        table = tables_by_id[
            calculation.table_id
        ]

        available_variables = set(
            table.columns
        )

        available_variables.update(
            calculation_outputs_by_table.get(
                calculation.table_id,
                set(),
            )
        )

        dependencies = get_expression_dependencies(
            calculation.expression
        )

        missing_variables = (
            dependencies
            - available_variables
        )

        if missing_variables:
            raise ValueError(
                f"Calculation '{calculation.output}' "
                f"for table_id={calculation.table_id} "
                f"uses unavailable variables: "
                f"{sorted(missing_variables)}."
            )

    for chart in specification.charts:

        if chart.table_id not in available_table_ids:
            raise ValueError(
                f"Chart figure_id={chart.figure_id} references "
                f"unknown table_id={chart.table_id}."
            )

        table = tables_by_id[
            chart.table_id
        ]

        available_columns = set(
            table.columns
        )

        available_columns.update(
            calculation_outputs_by_table.get(
                chart.table_id,
                set(),
            )
        )

        if chart.x not in available_columns:
            raise ValueError(
                f"Chart figure_id={chart.figure_id} "
                f"uses unavailable x variable "
                f"'{chart.x}' in table_id={chart.table_id}."
            )

        if chart.y not in available_columns:
            raise ValueError(
                f"Chart figure_id={chart.figure_id} "
                f"uses unavailable y variable "
                f"'{chart.y}' in table_id={chart.table_id}."
            )

        if (
            chart.filter_column is not None
            and chart.filter_column not in available_columns
        ):
            raise ValueError(
                f"Chart figure_id={chart.figure_id} "
                f"uses unavailable filter column "
                f"'{chart.filter_column}' "
                f"in table_id={chart.table_id}."
            )

        if (
            chart.filter_column is not None
            and chart.filter_value is None
        ):
            raise ValueError(
                f"Chart figure_id={chart.figure_id} "
                "defines filter_column but "
                "filter_value is missing."
            )

    global_figure_id_set = {
        chart.figure_id
        for chart in specification.charts
    }

    assigned_figure_ids: set[int] = set()

    for section in specification.sections:

        if len(
            section.chart_figure_ids
        ) != len(
            set(section.chart_figure_ids)
        ):
            raise ValueError(
                f"Section {section.section_id} contains "
                "duplicate figure_id values."
            )

        for figure_id in section.chart_figure_ids:

            if figure_id in assigned_figure_ids:
                raise ValueError(
                    f"Chart figure_id={figure_id} is assigned "
                    "to more than one report section."
                )

            assigned_figure_ids.add(
                figure_id
            )

    missing_figure_ids = (
        global_figure_id_set
        - assigned_figure_ids
    )

    if missing_figure_ids:
        raise ValueError(
            "Charts not assigned to any section: "
            f"{sorted(missing_figure_ids)}."
        )

    unknown_figure_ids = (
        assigned_figure_ids
        - global_figure_id_set
    )

    if unknown_figure_ids:
        raise ValueError(
            "Sections reference unknown figure_id values: "
            f"{sorted(unknown_figure_ids)}."
        )

    for section in specification.sections:

        if section.table is None:
            continue

        table = tables_by_id[
            section.table_id
        ]

        if section.table.columns != table.columns:
            raise ValueError(
                f"Section {section.section_id} does not preserve "
                f"the exact column structure of "
                f"table_id={section.table_id}. "
                f"Expected: {table.columns}. "
                f"Received: {section.table.columns}."
            )


    for section in specification.sections:

        valid_outputs = (
            calculation_outputs_by_table.get(
                section.table_id,
                set(),
            )
        )

        for output in section.calculation_outputs:

            if output not in valid_outputs:
                raise ValueError(
                    f"Section {section.section_id} references "
                    f"calculation output '{output}', but it does "
                    f"not belong to table_id={section.table_id}."
                )