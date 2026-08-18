from types import SimpleNamespace

import pytest

from app.schemas.calculation import (
    CalculationSpecification,
    OperationExpression,
    VariableExpression,
)
from app.services.specification_validator import (
    validate_report_specification,
)


def variable(name: str) -> VariableExpression:
    return VariableExpression(
        type="variable",
        name=name,
    )


def multiply(
    left,
    right,
) -> OperationExpression:
    return OperationExpression(
        type="operation",
        operation="multiply",
        args=[
            left,
            right,
        ],
    )


def measurement_table(
    table_id: int,
    columns: list[str],
):
    return SimpleNamespace(
        table_id=table_id,
        columns=columns,
    )


def section(
    section_id: int,
    table_id: int,
    columns: list[str] | None = None,
    calculation_outputs: list[str] | None = None,
    chart_figure_ids: list[int] | None = None,
):
    table = None

    if columns is not None:
        table = SimpleNamespace(
            columns=columns,
        )

    return SimpleNamespace(
        section_id=section_id,
        table_id=table_id,
        table=table,
        calculation_outputs=calculation_outputs or [],
        chart_figure_ids=chart_figure_ids or [],
    )


def chart(
    figure_id: int,
    table_id: int,
    x: str,
    y: str,
    filter_column: str | None = None,
    filter_value=None,
):
    return SimpleNamespace(
        figure_id=figure_id,
        table_id=table_id,
        x=x,
        y=y,
        filter_column=filter_column,
        filter_value=filter_value,
    )


def specification(
    sections=None,
    calculations=None,
    charts=None,
):
    return SimpleNamespace(
        sections=sections or [],
        calculations=calculations or [],
        charts=charts or [],
    )


def test_valid_specification_passes():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "I",
                "P",
            ],
        )
    ]

    calculation = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=multiply(
            variable("U"),
            variable("I"),
        ),
    )

    spec = specification(
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "U",
                    "I",
                    "P",
                ],
                calculation_outputs=["P"],
                chart_figure_ids=[1],
            )
        ],
        calculations=[
            calculation,
        ],
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="P",
            )
        ],
    )

    validate_report_specification(
        specification=spec,
        measurement_tables=tables,
    )


def test_unknown_section_table_raises_error():
    tables = [
        measurement_table(
            table_id=1,
            columns=["U"],
        )
    ]

    spec = specification(
        sections=[
            section(
                section_id=1,
                table_id=999,
                columns=["U"],
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="unknown table_id=999",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_calculation_with_unknown_variable_raises_error():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "P",
            ],
        )
    ]

    calculation = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=multiply(
            variable("U"),
            variable("I"),
        ),
    )

    spec = specification(
        calculations=[
            calculation,
        ],
    )

    with pytest.raises(
        ValueError,
        match="unavailable variables",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_duplicate_calculation_output_raises_error():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "P",
            ],
        )
    ]

    calculation_1 = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=variable("U"),
    )

    calculation_2 = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=variable("U"),
    )

    spec = specification(
        calculations=[
            calculation_1,
            calculation_2,
        ],
    )

    with pytest.raises(
        ValueError,
        match="Duplicate calculation output",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_chart_with_unknown_x_variable_raises_error():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "P",
            ],
        )
    ]

    spec = specification(
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="UNKNOWN",
                y="P",
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="unavailable x variable",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_chart_can_use_calculated_output():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "I",
                "P",
            ],
        )
    ]

    calculation = CalculationSpecification(
        table_id=1,
        output="T",
        unit="Nm",
        expression=variable("P"),
    )

    spec = specification(
        calculations=[
            calculation,
        ],
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="T",
            )
        ],
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "U",
                    "I",
                    "P",
                ],
                chart_figure_ids=[1],
            )
        ],
    )

    validate_report_specification(
        specification=spec,
        measurement_tables=tables,
    )


def test_section_cannot_omit_excel_column():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "I",
                "P",
            ],
        )
    ]

    spec = specification(
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "U",
                    "I",
                ],
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="does not preserve",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_section_must_preserve_excel_column_order():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "I",
                "P",
            ],
        )
    ]

    spec = specification(
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "I",
                    "U",
                    "P",
                ],
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="does not preserve",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_same_figure_can_contain_multiple_chart_series():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "P",
                "I",
                "n",
            ],
        )
    ]

    spec = specification(
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="P",
                y="I",
            ),
            chart(
                figure_id=1,
                table_id=1,
                x="P",
                y="n",
            ),
        ],
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "P",
                    "I",
                    "n",
                ],
                chart_figure_ids=[1],
            )
        ],
    )

    validate_report_specification(
        specification=spec,
        measurement_tables=tables,
    )


def test_same_figure_cannot_belong_to_two_sections():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "P",
                "I",
            ],
        )
    ]

    spec = specification(
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="P",
                y="I",
            )
        ],
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "P",
                    "I",
                ],
                chart_figure_ids=[1],
            ),
            section(
                section_id=2,
                table_id=1,
                columns=[
                    "P",
                    "I",
                ],
                chart_figure_ids=[1],
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="assigned to more than one report section",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_unassigned_chart_raises_error():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "I",
            ],
        )
    ]

    spec = specification(
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="I",
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="Charts not assigned to any section",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )


def test_invalid_section_calculation_output_raises_error():
    tables = [
        measurement_table(
            table_id=1,
            columns=[
                "U",
                "P",
            ],
        )
    ]

    spec = specification(
        sections=[
            section(
                section_id=1,
                table_id=1,
                columns=[
                    "U",
                    "P",
                ],
                calculation_outputs=[
                    "UNKNOWN",
                ],
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="does not belong to table_id=1",
    ):
        validate_report_specification(
            specification=spec,
            measurement_tables=tables,
        )