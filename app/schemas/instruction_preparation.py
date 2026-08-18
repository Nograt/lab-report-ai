from pydantic import (
    BaseModel,
    Field,
)


class MissingParameter(BaseModel):
    name: str
    symbol: str

    unit: str | None = None
    description: str | None = None


class InstructionPreparation(BaseModel):
    instruction: str

    missing_parameters: list[
        MissingParameter
    ] = Field(
        default_factory=list
    )