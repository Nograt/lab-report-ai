from app.schemas.instruction_parameters import (
    InstructionParameterValue,
)
from app.services.instruction_parameter_resolver import (
    apply_instruction_parameters,
)


def test_returns_original_instruction_when_no_parameters():
    instruction = "Obliczyć moc P."

    result = apply_instruction_parameters(
        instruction=instruction,
        parameters=[],
    )

    assert result == instruction


def test_appends_parameter_with_unit():
    instruction = "Obliczyć prędkość synchroniczną."

    parameters = [
        InstructionParameterValue(
            symbol="f1",
            value=50,
            unit="Hz",
        ),
    ]

    result = apply_instruction_parameters(
        instruction=instruction,
        parameters=parameters,
    )

    assert "Dodatkowe dane do ćwiczenia:" in result
    assert "f1 = 50 Hz" in result


def test_appends_parameter_without_unit():
    instruction = "Obliczyć prędkość synchroniczną."

    parameters = [
        InstructionParameterValue(
            symbol="p",
            value=2,
            unit=None,
        ),
    ]

    result = apply_instruction_parameters(
        instruction=instruction,
        parameters=parameters,
    )

    assert "p = 2" in result


def test_appends_multiple_parameters():
    instruction = "Obliczyć parametry silnika."

    parameters = [
        InstructionParameterValue(
            symbol="f1",
            value=50,
            unit="Hz",
        ),
        InstructionParameterValue(
            symbol="p",
            value=2,
            unit=None,
        ),
        InstructionParameterValue(
            symbol="l",
            value=0.25,
            unit="m",
        ),
    ]

    result = apply_instruction_parameters(
        instruction=instruction,
        parameters=parameters,
    )

    assert "f1 = 50 Hz" in result
    assert "p = 2" in result
    assert "l = 0.25 m" in result


def test_instruction_is_not_modified_before_appended_data():
    instruction = (
        "Temat ćwiczenia: Silnik indukcyjny.\n"
        "Obliczyć poślizg."
    )

    parameters = [
        InstructionParameterValue(
            symbol="f1",
            value=50,
            unit="Hz",
        ),
    ]

    result = apply_instruction_parameters(
        instruction=instruction,
        parameters=parameters,
    )

    assert result.startswith(instruction)