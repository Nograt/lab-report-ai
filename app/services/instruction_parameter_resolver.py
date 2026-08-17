from app.schemas.instruction_parameters import (
    InstructionParameterValue,
)


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

        if parameter.unit:
            value_text = (
                f"{parameter.symbol} = "
                f"{parameter.value} "
                f"{parameter.unit}"
            )

        else:
            value_text = (
                f"{parameter.symbol} = "
                f"{parameter.value}"
            )

        lines.append(
            value_text
        )

    return "\n".join(lines)