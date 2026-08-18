from types import SimpleNamespace

import pytest

import app.services.instruction_parser as parser


def test_returns_original_specification_when_valid(
    monkeypatch,
):
    specification = object()

    monkeypatch.setattr(
        parser,
        "parse_report_instruction",
        lambda **kwargs: specification,
    )

    monkeypatch.setattr(
        parser,
        "validate_report_specification",
        lambda **kwargs: None,
    )

    def repair_should_not_run(**kwargs):
        raise AssertionError(
            "Repair should not be called "
            "for a valid specification."
        )

    monkeypatch.setattr(
        parser,
        "repair_report_specification",
        repair_should_not_run,
    )

    result = (
        parser.parse_report_instruction_with_repair(
            instruction="Test instruction",
            measurement_tables=[],
        )
    )

    assert result is specification


def test_repairs_invalid_specification(
    monkeypatch,
):
    original = object()
    repaired = object()

    monkeypatch.setattr(
        parser,
        "parse_report_instruction",
        lambda **kwargs: original,
    )

    validation_calls = 0

    def fake_validate(**kwargs):
        nonlocal validation_calls

        validation_calls += 1

        if validation_calls == 1:
            raise ValueError(
                "Initial validation error"
            )

    monkeypatch.setattr(
        parser,
        "validate_report_specification",
        fake_validate,
    )

    def fake_repair(**kwargs):
        assert (
            kwargs["specification"]
            is original
        )

        assert (
            kwargs["validation_error"]
            == "Initial validation error"
        )

        return repaired

    monkeypatch.setattr(
        parser,
        "repair_report_specification",
        fake_repair,
    )

    result = (
        parser.parse_report_instruction_with_repair(
            instruction="Test instruction",
            measurement_tables=[],
        )
    )

    assert result is repaired
    assert validation_calls == 2


def test_repair_failure_raises_combined_error(
    monkeypatch,
):
    original = object()
    repaired = object()

    monkeypatch.setattr(
        parser,
        "parse_report_instruction",
        lambda **kwargs: original,
    )

    monkeypatch.setattr(
        parser,
        "repair_report_specification",
        lambda **kwargs: repaired,
    )

    validation_calls = 0

    def fake_validate(**kwargs):
        nonlocal validation_calls

        validation_calls += 1

        if validation_calls == 1:
            raise ValueError(
                "First validation error"
            )

        raise ValueError(
            "Second validation error"
        )

    monkeypatch.setattr(
        parser,
        "validate_report_specification",
        fake_validate,
    )

    with pytest.raises(
        ValueError,
        match="remained invalid",
    ) as error:
        parser.parse_report_instruction_with_repair(
            instruction="Test instruction",
            measurement_tables=[],
        )

    message = str(
        error.value
    )

    assert (
        "First validation error"
        in message
    )

    assert (
        "Second validation error"
        in message
    )


def test_parse_raises_when_openai_returns_no_result(
    monkeypatch,
):
    fake_response = SimpleNamespace(
        output_parsed=None,
    )

    monkeypatch.setattr(
        parser.client.responses,
        "parse",
        lambda **kwargs: fake_response,
    )

    with pytest.raises(
        ValueError,
        match="Unable to parse report instruction",
    ):
        parser.parse_report_instruction(
            instruction="Test instruction",
            measurement_tables=[],
        )


def test_parse_returns_openai_result(
    monkeypatch,
):
    expected = object()

    fake_response = SimpleNamespace(
        output_parsed=expected,
    )

    monkeypatch.setattr(
        parser.client.responses,
        "parse",
        lambda **kwargs: fake_response,
    )

    result = parser.parse_report_instruction(
        instruction="Test instruction",
        measurement_tables=[],
    )

    assert result is expected


class FakeSpecification:
    def model_dump_json(
        self,
        indent=None,
    ):
        return "{}"


def test_repair_raises_when_openai_returns_no_result(
    monkeypatch,
):
    fake_response = SimpleNamespace(
        output_parsed=None,
    )

    monkeypatch.setattr(
        parser.client.responses,
        "parse",
        lambda **kwargs: fake_response,
    )

    with pytest.raises(
        ValueError,
        match="Unable to repair report specification",
    ):
        parser.repair_report_specification(
            specification=FakeSpecification(),
            validation_error="Some error",
            instruction="Test instruction",
            measurement_tables=[],
        )


def test_repair_returns_openai_result(
    monkeypatch,
):
    expected = object()

    fake_response = SimpleNamespace(
        output_parsed=expected,
    )

    monkeypatch.setattr(
        parser.client.responses,
        "parse",
        lambda **kwargs: fake_response,
    )

    result = parser.repair_report_specification(
        specification=FakeSpecification(),
        validation_error="Some error",
        instruction="Test instruction",
        measurement_tables=[],
    )

    assert result is expected