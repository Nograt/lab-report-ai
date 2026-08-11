from app.schemas.calculation import CalculationSpecification
from app.services.calculation_engine import (
    expression_to_sympy,
    get_expression_dependencies,
)


calculation = CalculationSpecification.model_validate(
    {
        "output": "PK",
        "unit": "W",
        "expression": {
            "type": "operation",
            "operation": "subtract",
            "args": [
                {
                    "type": "variable",
                    "name": "P"
                },
                {
                    "type": "variable",
                    "name": "Pap"
                }
            ]
        }
    }
)


sympy_expression = expression_to_sympy(
    calculation.expression
)

dependencies = get_expression_dependencies(
    calculation.expression
)


print("Wzór:")
print(sympy_expression)

print("Zależności:")
print(dependencies)


calculation_2 = CalculationSpecification.model_validate(
    {
        "output": "X",
        "unit": None,
        "expression": {
            "type": "operation",
            "operation": "divide",
            "args": [
                {
                    "type": "variable",
                    "name": "U"
                },
                {
                    "type": "operation",
                    "operation": "multiply",
                    "args": [
                        {
                            "type": "operation",
                            "operation": "sqrt",
                            "args": [
                                {
                                    "type": "constant",
                                    "value": 3
                                }
                            ]
                        },
                        {
                            "type": "variable",
                            "name": "I"
                        },
                        {
                            "type": "variable",
                            "name": "cosφ"
                        }
                    ]
                }
            ]
        }
    }
)


print()
print("Drugi wzór:")

expression_2 = expression_to_sympy(
    calculation_2.expression
)

print(expression_2)

print("Zależności:")
print(
    get_expression_dependencies(
        calculation_2.expression
    )
)


from app.schemas.calculation import CalculationSpecification
from app.services.calculation_engine import resolve_calculation_order


cos_phi = CalculationSpecification.model_validate(
    {
        "output": "cosφK",
        "unit": None,
        "expression": {
            "type": "operation",
            "operation": "divide",
            "args": [
                {
                    "type": "variable",
                    "name": "PK"
                },
                {
                    "type": "operation",
                    "operation": "multiply",
                    "args": [
                        {
                            "type": "operation",
                            "operation": "sqrt",
                            "args": [
                                {
                                    "type": "constant",
                                    "value": 3
                                }
                            ]
                        },
                        {
                            "type": "variable",
                            "name": "Uk"
                        },
                        {
                            "type": "variable",
                            "name": "I"
                        }
                    ]
                }
            ]
        }
    }
)


pk = CalculationSpecification.model_validate(
    {
        "output": "PK",
        "unit": "W",
        "expression": {
            "type": "operation",
            "operation": "subtract",
            "args": [
                {
                    "type": "variable",
                    "name": "P"
                },
                {
                    "type": "variable",
                    "name": "Pap"
                }
            ]
        }
    }
)

calculations = [
    cos_phi,
    pk,
]

available_columns = {
    "Lp",
    "Uk",
    "I",
    "P",
    "Pap",
    "PK",
    "cosφK",
    "Tl",
}

ordered = resolve_calculation_order(
    calculations,
    available_columns
)

for calculation in ordered:
    print(calculation.output)
    
    
import pandas as pd

from app.services.calculation_engine import execute_calculations


df = pd.DataFrame(
    {
        "Uk": [130, 124, 112],
        "I": [2.10, 1.80, 1.55],
        "P": [134, 120, 88],
        "Pap": [1.13, 1.03, 0.84],

        "PK": [None, None, None],
        "cosφK": [None, None, None],
    }
)


completed_df = execute_calculations(
    df=df,
    calculations=[
        cos_phi,   # CELOWO źle
        pk,
    ],
)


print(completed_df)