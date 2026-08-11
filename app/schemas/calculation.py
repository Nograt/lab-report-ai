from typing import Literal, Union

from pydantic import BaseModel


class VariableExpression(BaseModel):
    type: Literal["variable"]
    name: str


class ConstantExpression(BaseModel):
    type: Literal["constant"]
    value: int | float


class OperationExpression(BaseModel):
    type: Literal["operation"]

    operation: Literal[
        "add",
        "subtract",
        "multiply",
        "divide",
        "power",
        "sqrt",
        "sin",
        "cos",
        "tan",
        "log",
        "ln",
        "abs",
    ]

    args: list["Expression"]


Expression = Union[
    VariableExpression,
    ConstantExpression,
    OperationExpression,
]


OperationExpression.model_rebuild(
    _types_namespace={
        "Expression": Expression
    }
)


class CalculationSpecification(BaseModel):
    output: str
    unit: str | None
    expression: Expression