from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

class VariableExpression(BaseModel):
    type: Literal["variable"]
    name: str
    
class ConstantExpression(BaseModel):
    type: Literal["constant"]
    value: float
    
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
    
    
Expression = Annotated[
    Union[
        VariableExpression,
        ConstantExpression,
        OperationExpression,
    ],
    Field(discriminator="type"),
]

OperationExpression.model_rebuild(
    _types_namespace={
        "Expression": Expression
    }
)


class CalculationSpecification(BaseModel):
    output: str
    unit: str | None = None
    expression: Expression


