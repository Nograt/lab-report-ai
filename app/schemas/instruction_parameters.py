from pydantic import BaseModel


class InstructionParameterValue(BaseModel):
    symbol: str
    value: float
    unit: str | None = None