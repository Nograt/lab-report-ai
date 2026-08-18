from app.schemas.instruction_parameters import (
    InstructionParameterValue,
)


def format_parameter_value(
    value: float,
) -> str:

    if value.is_integer():
        return str(int(value))

    return str(value)


def apply_instruction_parameters(
    instruction: str,
    parameters: list[InstructionParameterValue],
) -> str:

    if not parameters:
        return instruction

    lines = [
        instruction.rstrip(),
        "",
        "Dodatkowe dane do ćwiczenia:",
        "",
    ]

    for parameter in parameters:

        value = format_parameter_value(
            parameter.value
        )

        if parameter.unit:
            value_text = (
                f"{parameter.symbol} = "
                f"{value} "
                f"{parameter.unit}"
            )

        else:
            value_text = (
                f"{parameter.symbol} = "
                f"{value}"
            )

        lines.append(value_text)

    return "\n".join(lines)