import sympy as sp
import pandas as pd

from app.schemas.calculation import (
    CalculationSpecification,
    Expression,
    VariableExpression,
    ConstantExpression,
    OperationExpression,
)

from app.services.excel_reader import MeasurementTableData

def execute_table_calculations(
    tables: list[MeasurementTableData],
    calculations: list[CalculationSpecification],
) -> list[MeasurementTableData]:

    completed_tables = []

    for table in tables:

        table_calculations = [
            calculation
            for calculation in calculations
            if calculation.table_id == table.table_id
        ]

        completed_df = execute_calculations(
            df=table.dataframe,
            calculations=table_calculations,
        )

        completed_units = table.units.copy()

        for calculation in table_calculations:

            if calculation.output not in completed_units:
                completed_units[calculation.output] = calculation.unit

            elif completed_units[calculation.output] is None:
                completed_units[calculation.output] = calculation.unit

        completed_tables.append(
            MeasurementTableData(
                table_id=table.table_id,
                title=table.title,
                sheet_name=table.sheet_name,
                dataframe=completed_df,
                units=completed_units,
            )
        )

    return completed_tables


def expression_to_sympy(expression: Expression) -> sp.Expr:
    if isinstance(expression, VariableExpression):
        return sp.Symbol(expression.name)

    if isinstance(expression, ConstantExpression):
        if isinstance(expression.value, int):
            return sp.Integer(expression.value)
        return sp.Float(expression.value)

    if not isinstance(expression, OperationExpression):
        raise ValueError("Unsupported expression type.")

    args = [
        expression_to_sympy(arg)
        for arg in expression.args
    ]

    operation = expression.operation

    if operation == "add":
        if len(args) < 2:
            raise ValueError("Add requires at least 2 arguments.")

        return sp.Add(*args)

    if operation == "subtract":
        if len(args) != 2:
            raise ValueError("Subtract requires exactly 2 arguments.")

        return args[0] - args[1]

    if operation == "multiply":
        if len(args) < 2:
            raise ValueError("Multiply requires at least 2 arguments.")

        return sp.Mul(*args)

    if operation == "divide":
        if len(args) != 2:
            raise ValueError("Divide requires exactly 2 arguments.")

        return args[0] / args[1]

    if operation == "power":
        if len(args) != 2:
            raise ValueError("Power requires exactly 2 arguments.")

        return args[0] ** args[1]

    if operation == "sqrt":
        if len(args) != 1:
            raise ValueError("Sqrt requires exactly 1 argument.")

        return sp.sqrt(args[0])

    if operation == "sin":
        if len(args) != 1:
            raise ValueError("Sin requires exactly 1 argument.")

        return sp.sin(args[0])

    if operation == "cos":
        if len(args) != 1:
            raise ValueError("Cos requires exactly 1 argument.")

        return sp.cos(args[0])

    if operation == "tan":
        if len(args) != 1:
            raise ValueError("Tan requires exactly 1 argument.")

        return sp.tan(args[0])

    if operation == "ln":
        if len(args) != 1:
            raise ValueError("Ln requires exactly 1 argument.")

        return sp.log(args[0])

    if operation == "log":
        if len(args) != 1:
            raise ValueError("Log requires exactly 1 argument.")

        return sp.log(args[0], 10)

    if operation == "abs":
        if len(args) != 1:
            raise ValueError("Abs requires exactly 1 argument.")

        return sp.Abs(args[0])

    raise ValueError(
        f"Unsupported operation: {operation}"
    )
    
def get_expression_dependencies(
    expression: Expression
) -> set[str]:

    sympy_expression = expression_to_sympy(
        expression
    )

    return {
        str(symbol)
        for symbol in sympy_expression.free_symbols
    }
    
def resolve_calculation_order(
    calculations: list[CalculationSpecification],
    available_columns: set[str],
) -> list[CalculationSpecification]:

    calculations_by_output = {}

    for calculation in calculations:
        if calculation.output in calculations_by_output:
            raise ValueError(
                f"Duplicate calculation output: '{calculation.output}'."
            )

        calculations_by_output[calculation.output] = calculation


    calculated_variables = set(calculations_by_output.keys())

    resolved_variables = (
        available_columns - calculated_variables
    )

    for calculation in calculations:
        dependencies = get_expression_dependencies(
            calculation.expression
        )

        missing = (
            dependencies
            - available_columns
            - calculated_variables
        )

        if missing:
            raise ValueError(
                f"Calculation '{calculation.output}' "
                f"requires missing variables: {sorted(missing)}"
            )


    pending = calculations.copy()
    ordered = []


    while pending:
        progress = False

        for calculation in pending.copy():

            dependencies = get_expression_dependencies(
                calculation.expression
            )

            if dependencies.issubset(resolved_variables):

                ordered.append(calculation)

                resolved_variables.add(
                    calculation.output
                )

                pending.remove(calculation)

                progress = True


        if not progress:
            unresolved = {}

            for calculation in pending:
                dependencies = get_expression_dependencies(
                    calculation.expression
                )

                unresolved[calculation.output] = sorted(
                    dependencies - resolved_variables
                )

            raise ValueError(
                f"Unable to resolve calculation order. "
                f"Possible circular dependency: {unresolved}"
            )


    return ordered


def execute_calculations(
    df: pd.DataFrame,
    calculations: list[CalculationSpecification],
) -> pd.DataFrame:

    result_df = df.copy()

    ordered_calculations = resolve_calculation_order(
        calculations=calculations,
        available_columns=set(result_df.columns),
    )

    for calculation in ordered_calculations:

        sympy_expression = expression_to_sympy(
            calculation.expression
        )

        symbols = sorted(
            sympy_expression.free_symbols,
            key=lambda symbol: str(symbol)
        )

        symbol_names = [
            str(symbol)
            for symbol in symbols
        ]

        for name in symbol_names:
            if name not in result_df.columns:
                raise ValueError(
                    f"Calculation '{calculation.output}' "
                    f"requires missing column '{name}'."
                )

        function = sp.lambdify(
            symbols,
            sympy_expression,
            modules="numpy",
        )

        values = [
            pd.to_numeric(
                result_df[name],
                errors="raise"
            ).to_numpy()
            for name in symbol_names
        ]

        calculated_values = function(*values)

        calculated_series = pd.Series(
            calculated_values,
            index=result_df.index,
            dtype="float64",
        )

        if calculation.output not in result_df.columns:
            result_df[calculation.output] = calculated_series

        else:
           
            missing_mask = result_df[
                calculation.output
            ].isna()

            result_df.loc[
                missing_mask,
                calculation.output
            ] = calculated_series[missing_mask]

    return result_df