import pandas as pd
import pytest

from app.schemas.calculation import (
    CalculationSpecification,
    ConstantExpression,
    OperationExpression,
    VariableExpression,
)
from app.services.calculation_engine import execute_calculations


def variable(name: str) -> VariableExpression:
    return VariableExpression(
        type="variable",
        name=name,
    )


def constant(value: int | float) -> ConstantExpression:
    return ConstantExpression(
        type="constant",
        value=value,
    )


def operation(
    name: str,
    *args,
) -> OperationExpression:
    return OperationExpression(
        type="operation",
        operation=name,
        args=list(args),
    )


def test_calculates_new_output_column():
    df = pd.DataFrame(
        {
            "U": [10, 20],
            "I": [2, 4],
        }
    )

    calculation = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=operation(
            "multiply",
            variable("U"),
            variable("I"),
        ),
    )

    result = execute_calculations(
        df=df,
        calculations=[calculation],
    )

    assert result["P"].tolist() == [
        20.0,
        80.0,
    ]


def test_fills_only_missing_values():
    df = pd.DataFrame(
        {
            "U": [10, 20],
            "I": [2, 4],
            "P": [999.0, None],
        }
    )

    calculation = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=operation(
            "multiply",
            variable("U"),
            variable("I"),
        ),
    )

    result = execute_calculations(
        df=df,
        calculations=[calculation],
    )

    assert result["P"].tolist() == [
        999.0,
        80.0,
    ]


def test_resolves_calculation_dependencies():
    df = pd.DataFrame(
        {
            "U": [10, 20],
        }
    )

    calculation_b = CalculationSpecification(
        table_id=1,
        output="B",
        unit=None,
        expression=operation(
            "add",
            variable("A"),
            constant(1),
        ),
    )

    calculation_a = CalculationSpecification(
        table_id=1,
        output="A",
        unit=None,
        expression=operation(
            "multiply",
            variable("U"),
            constant(2),
        ),
    )

    result = execute_calculations(
        df=df,
        calculations=[
            calculation_b,
            calculation_a,
        ],
    )

    assert result["A"].tolist() == [
        20.0,
        40.0,
    ]

    assert result["B"].tolist() == [
        21.0,
        41.0,
    ]


def test_missing_variable_raises_error():
    df = pd.DataFrame(
        {
            "U": [10, 20],
        }
    )

    calculation = CalculationSpecification(
        table_id=1,
        output="P",
        unit="W",
        expression=operation(
            "multiply",
            variable("U"),
            variable("I"),
        ),
    )

    with pytest.raises(
        ValueError,
        match="missing variables",
    ):
        execute_calculations(
            df=df,
            calculations=[calculation],
        )


def test_circular_dependency_raises_error():
    df = pd.DataFrame(
        {
            "U": [10, 20],
        }
    )

    calculation_a = CalculationSpecification(
        table_id=1,
        output="A",
        unit=None,
        expression=operation(
            "add",
            variable("B"),
            constant(1),
        ),
    )

    calculation_b = CalculationSpecification(
        table_id=1,
        output="B",
        unit=None,
        expression=operation(
            "add",
            variable("A"),
            constant(1),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Possible circular dependency",
    ):
        execute_calculations(
            df=df,
            calculations=[
                calculation_a,
                calculation_b,
            ],
        )


def test_duplicate_output_raises_error():
    df = pd.DataFrame(
        {
            "U": [10, 20],
        }
    )

    calculation_1 = CalculationSpecification(
        table_id=1,
        output="P",
        unit=None,
        expression=variable("U"),
    )

    calculation_2 = CalculationSpecification(
        table_id=1,
        output="P",
        unit=None,
        expression=operation(
            "multiply",
            variable("U"),
            constant(2),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Duplicate calculation output",
    ):
        execute_calculations(
            df=df,
            calculations=[
                calculation_1,
                calculation_2,
            ],
        )