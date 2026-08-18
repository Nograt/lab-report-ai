from types import SimpleNamespace

import pytest

import app.services.instruction_preparer as preparer
from app.schemas.measurement import MeasurementTableInfo


def measurement_table(
    table_id: int,
    title: str,
    sheet_name: str,
    columns: list[str],
    units: dict[str, str | None],
    column_has_values: dict[str, bool],
) -> MeasurementTableInfo:
    return MeasurementTableInfo(
        table_id=table_id,
        title=title,
        sheet_name=sheet_name,
        columns=columns,
        units=units,
        column_has_values=column_has_values,
    )


def test_prepare_instruction_returns_openai_result(
    monkeypatch,
):
    expected = object()

    fake_response = SimpleNamespace(
        output_parsed=expected,
    )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        lambda **kwargs: fake_response,
    )

    result = preparer.prepare_instruction(
        instruction_file_id="file_test",
        measurement_tables=[],
    )

    assert result is expected


def test_prepare_instruction_raises_when_result_is_none(
    monkeypatch,
):
    fake_response = SimpleNamespace(
        output_parsed=None,
    )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        lambda **kwargs: fake_response,
    )

    with pytest.raises(
        ValueError,
        match="Unable to prepare laboratory instruction",
    ):
        preparer.prepare_instruction(
            instruction_file_id="file_test",
            measurement_tables=[],
        )


def test_passes_pdf_file_id_to_openai(
    monkeypatch,
):
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            output_parsed=object(),
        )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        fake_parse,
    )

    preparer.prepare_instruction(
        instruction_file_id="file_123",
        measurement_tables=[],
    )

    user_message = captured["input"][1]

    content = user_message["content"]

    file_item = content[0]

    assert file_item["type"] == "input_file"
    assert file_item["file_id"] == "file_123"


def test_passes_measurement_columns_to_prompt(
    monkeypatch,
):
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            output_parsed=object(),
        )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        fake_parse,
    )

    tables = [
        measurement_table(
            table_id=1,
            title="Bieg jałowy",
            sheet_name="Sheet1",
            columns=[
                "U",
                "I",
                "P",
            ],
            units={
                "U": "V",
                "I": "A",
                "P": "W",
            },
            column_has_values={
                "U": True,
                "I": True,
                "P": False,
            },
        )
    ]

    preparer.prepare_instruction(
        instruction_file_id="file_test",
        measurement_tables=tables,
    )

    user_message = captured["input"][1]

    text_item = user_message["content"][1]

    prompt = text_item["text"]

    assert "TABLE ID: 1" in prompt
    assert "Bieg jałowy" in prompt
    assert "Sheet1" in prompt

    assert "['U', 'I', 'P']" in prompt

    assert "'U': 'V'" in prompt
    assert "'I': 'A'" in prompt
    assert "'P': 'W'" in prompt


def test_passes_column_has_values_to_prompt(
    monkeypatch,
):
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            output_parsed=object(),
        )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        fake_parse,
    )

    tables = [
        measurement_table(
            table_id=1,
            title="Pomiary",
            sheet_name="Pomiary",
            columns=[
                "U",
                "I",
                "P",
            ],
            units={
                "U": "V",
                "I": "A",
                "P": "W",
            },
            column_has_values={
                "U": True,
                "I": True,
                "P": False,
            },
        )
    ]

    preparer.prepare_instruction(
        instruction_file_id="file_test",
        measurement_tables=tables,
    )

    user_message = captured["input"][1]
    text_item = user_message["content"][1]
    prompt = text_item["text"]

    assert "'U': True" in prompt
    assert "'I': True" in prompt
    assert "'P': False" in prompt


def test_uses_instruction_preparation_schema(
    monkeypatch,
):
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            output_parsed=object(),
        )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        fake_parse,
    )

    preparer.prepare_instruction(
        instruction_file_id="file_test",
        measurement_tables=[],
    )

    assert (
        captured["text_format"]
        is preparer.InstructionPreparation
    )


def test_uses_configured_model(
    monkeypatch,
):
    captured = {}

    def fake_parse(**kwargs):
        captured.update(kwargs)

        return SimpleNamespace(
            output_parsed=object(),
        )

    monkeypatch.setattr(
        preparer.client.responses,
        "parse",
        fake_parse,
    )

    preparer.prepare_instruction(
        instruction_file_id="file_test",
        measurement_tables=[],
    )

    assert captured["model"] == preparer.MODEL