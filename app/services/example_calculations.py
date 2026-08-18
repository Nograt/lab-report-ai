import pandas as pd

from app.schemas.calculation import (
    CalculationSpecification,
    ConstantExpression,
    Expression,
    OperationExpression,
    VariableExpression,
)
from app.schemas.report import ReportSpecification
from app.services.calculation_engine import (
    resolve_calculation_order,
)
from app.services.excel_reader import (
    MeasurementTableData,
    get_measurement_table,
)

def format_formula_number(
    value: float | int,
) -> str:

    value = float(value)

    if value == 0:
        return "0"

    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))

    formatted = f"{value:.6f}"

    return (
        formatted
        .rstrip("0")
        .rstrip(".")
    )
    
def create_multi_table_example_calculations(
    specification: ReportSpecification,
    tables: list[MeasurementTableData],
    row_index: int = 0,
) -> list[dict]:

    results = []

    for section in specification.sections:

        if not section.calculation_outputs:
            continue

        table = get_measurement_table(
            tables=tables,
            table_id=section.table_id,
        )

        section_calculations = [
            calculation
            for calculation in specification.calculations
            if (
                calculation.table_id == section.table_id
                and calculation.output
                in section.calculation_outputs
            )
        ]

        if not section_calculations:
            continue

        examples = create_example_calculations(
            df=table.dataframe,
            calculations=section_calculations,
            units=table.units,
            row_index=row_index,
        )

        results.append(
            {
                "section_id": section.section_id,
                "table_id": section.table_id,
                "row_index": row_index,
                "calculations": examples,
            }
        )

    return results

def format_number(
    value,
    decimal_places: int = 2
) -> str:

    number = float(value)

    formatted = f"{number:.{decimal_places}f}"

    return formatted.rstrip("0").rstrip(".")

GREEK_TO_LATEX = {
    # lowercase
    "α": r"{\alpha}",
    "β": r"{\beta}",
    "γ": r"{\gamma}",
    "δ": r"{\delta}",
    "ε": r"{\varepsilon}",
    "ζ": r"{\zeta}",
    "η": r"{\eta}",
    "θ": r"{\theta}",
    "ι": r"{\iota}",
    "κ": r"{\kappa}",
    "λ": r"{\lambda}",
    "μ": r"{\mu}",
    "ν": r"{\nu}",
    "ξ": r"{\xi}",
    "ο": r"{o}",
    "π": r"{\pi}",
    "ρ": r"{\rho}",
    "σ": r"{\sigma}",
    "ς": r"{\sigma}",
    "τ": r"{\tau}",
    "υ": r"{\upsilon}",
    "φ": r"{\varphi}",
    "χ": r"{\chi}",
    "ψ": r"{\psi}",
    "ω": r"{\omega}",

    # uppercase
    "Α": r"{A}",
    "Β": r"{B}",
    "Γ": r"{\Gamma}",
    "Δ": r"{\Delta}",
    "Ε": r"{E}",
    "Ζ": r"{Z}",
    "Η": r"{H}",
    "Θ": r"{\Theta}",
    "Ι": r"{I}",
    "Κ": r"{K}",
    "Λ": r"{\Lambda}",
    "Μ": r"{M}",
    "Ν": r"{N}",
    "Ξ": r"{\Xi}",
    "Ο": r"{O}",
    "Π": r"{\Pi}",
    "Ρ": r"{P}",
    "Σ": r"{\Sigma}",
    "Τ": r"{T}",
    "Υ": r"{\Upsilon}",
    "Φ": r"{\Phi}",
    "Χ": r"{X}",
    "Ψ": r"{\Psi}",
    "Ω": r"{\Omega}",
}

def format_variable(name: str) -> str:
    return "".join(
        GREEK_TO_LATEX.get(character, character)
        for character in name
    )

def expression_to_latex(
    expression: Expression,
    row: pd.Series | None = None,
    decimal_places: int = 2,
) -> str:

    if isinstance(expression, VariableExpression):

        if row is None:
            return format_variable(
                expression.name
            )

        if expression.name not in row.index:
            raise ValueError(
                f"Missing variable '{expression.name}' "
                "in measurement row."
            )

        value = row[expression.name]

        if pd.isna(value):
            raise ValueError(
                f"Variable '{expression.name}' "
                "has no value in measurement row."
            )

        return format_number(
            value,
            decimal_places
        )

    if isinstance(expression, ConstantExpression):
        return format_formula_number(
            expression.value,
        )

    if not isinstance(expression, OperationExpression):
        raise ValueError(
            "Unsupported expression type."
        )

    args = [
        expression_to_latex(
            arg,
            row=row,
            decimal_places=decimal_places,
        )
        for arg in expression.args
    ]

    operation = expression.operation

    if operation == "add":
        return " + ".join(args)

    if operation == "subtract":
        return f"{args[0]} - {args[1]}"

    if operation == "multiply":
        return r" \cdot ".join(args)

    if operation == "divide":
        return (
            rf"\frac{{{args[0]}}}"
            rf"{{{args[1]}}}"
        )

    if operation == "power":
        return (
            rf"{{{args[0]}}}"
            rf"^{{{args[1]}}}"
        )

    if operation == "sqrt":
        return rf"\sqrt{{{args[0]}}}"

    if operation == "sin":
        return (
            rf"\sin\left({args[0]}\right)"
        )

    if operation == "cos":
        return (
            rf"\cos\left({args[0]}\right)"
        )

    if operation == "tan":
        return (
            rf"\tan\left({args[0]}\right)"
        )

    if operation == "log":
        return (
            rf"\log\left({args[0]}\right)"
        )

    if operation == "ln":
        return (
            rf"\ln\left({args[0]}\right)"
        )

    if operation == "abs":
        return (
            rf"\left|{args[0]}\right|"
        )

    raise ValueError(
        f"Unsupported operation: {operation}"
    )
 
 
def get_expression_variables(
    expression: Expression,
) -> set[str]:

    if isinstance(expression, VariableExpression):
        return {
            expression.name
        }

    if isinstance(expression, ConstantExpression):
        return set()

    if isinstance(expression, OperationExpression):
        variables = set()

        for arg in expression.args:
            variables.update(
                get_expression_variables(arg)
            )

        return variables

    raise ValueError(
        "Unsupported expression type."
    )
    
       
def create_example_calculations(
    df: pd.DataFrame,
    calculations: list[CalculationSpecification],
    units: dict[str, str | None],
    row_index: int = 0,
    decimal_places: int = 2,
) -> list[dict]:

    if row_index < 0 or row_index >= len(df):
        raise ValueError(
            f"Invalid measurement row: {row_index}"
        )

    row = df.iloc[row_index]

    ordered_calculations = resolve_calculation_order(
        calculations=calculations,
        available_columns=set(df.columns),
    )

    examples = []

    for calculation in ordered_calculations:

        if calculation.output not in df.columns:
            raise ValueError(
                f"Calculated column "
                f"'{calculation.output}' does not exist."
            )

        result = row[
            calculation.output
        ]

        if pd.isna(result):
            raise ValueError(
                f"Calculated value "
                f"'{calculation.output}' is empty."
            )

        output = format_variable(
            calculation.output
        )

        formula = expression_to_latex(
            calculation.expression
        )

        substitution = expression_to_latex(
            calculation.expression,
            row=row,
            decimal_places=decimal_places,
        )

        result_number = format_result_number(
    result
)

        unit = units.get(
            calculation.output
        )

        if unit:
            result_latex = (
                rf"{output} = "
                rf"{result_number}\,"
                rf"\mathrm{{{unit}}}"
            )
        else:
            result_latex = (
                f"{output} = {result_number}"
            )

        examples.append(
            {
                "output": calculation.output,
                "row_index": row_index,
                "formula_latex": (
                    f"{output} = {formula}"
                ),
                "substitution_latex": (
                    f"{output} = {substitution}"
                ),
                "result_latex": result_latex,
                "result": float(result),
                "unit": unit,
                "expression": calculation.expression.model_dump(),
                "variables": {
                    variable_name: float(row[variable_name])
                    for variable_name in get_expression_variables(
                        calculation.expression
                        )
                        },
            }
        )

    return examples
def format_result_number(
    value: float | int,
) -> str:

    value = float(value)


    if value == 0:
        return "0"

    absolute = abs(value)


    if absolute < 0.01:
        formatted = f"{value:.6f}"

    elif absolute < 1:
        formatted = f"{value:.4f}"


    elif absolute < 100:
        formatted = f"{value:.3f}"

    else:
        formatted = f"{value:.2f}"

    return (
        formatted
        .rstrip("0")
        .rstrip(".")
    )