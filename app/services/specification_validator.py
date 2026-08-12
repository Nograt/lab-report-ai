from app.schemas.report import ReportSpecification
from app.schemas.measurement import MeasurementTableInfo


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


    for calculation in specification.calculations:

        if calculation.table_id not in available_table_ids:
            raise ValueError(
                f"Calculation '{calculation.output}' references "
                f"unknown table_id={calculation.table_id}."
            )


    global_figure_ids = [
        chart.figure_id
        for chart in specification.charts
    ]

    if len(global_figure_ids) != len(set(global_figure_ids)):
        raise ValueError(
            "Duplicate figure_id exists in specification.charts."
        )


    assigned_figure_ids: set[int] = set()

    for section in specification.sections:

        for figure_id in section.chart_figure_ids:

            if figure_id in assigned_figure_ids:
                raise ValueError(
                    f"Chart figure_id={figure_id} is assigned "
                    "to more than one report section."
                )

            assigned_figure_ids.add(figure_id)



    global_figure_id_set = set(global_figure_ids)

    missing = global_figure_id_set - assigned_figure_ids

    if missing:
        raise ValueError(
            "Charts not assigned to any section: "
            f"{sorted(missing)}."
        )

    unknown = assigned_figure_ids - global_figure_id_set

    if unknown:
        raise ValueError(
            "Sections reference unknown figure_id values: "
            f"{sorted(unknown)}."
        )


    calculation_outputs_by_table: dict[int, set[str]] = {}

    for calculation in specification.calculations:
        calculation_outputs_by_table.setdefault(
            calculation.table_id,
            set(),
        ).add(calculation.output)

    for section in specification.sections:

        if section.table is None:
            continue

        table = tables_by_id[section.table_id]

        available_columns = set(table.columns)

        available_columns.update(
            calculation_outputs_by_table.get(
                section.table_id,
                set(),
            )
        )

        missing_columns = [
            column
            for column in section.table.columns
            if column not in available_columns
        ]

        if missing_columns:
            raise ValueError(
                f"Section {section.section_id} uses columns "
                f"{missing_columns} which are not available "
                f"in table_id={section.table_id}."
            )

    for section in specification.sections:

        valid_outputs = calculation_outputs_by_table.get(
            section.table_id,
            set(),
        )

        for output in section.calculation_outputs:

            if output not in valid_outputs:
                raise ValueError(
                    f"Section {section.section_id} references "
                    f"calculation output '{output}', but it does "
                    f"not belong to table_id={section.table_id}."
                )