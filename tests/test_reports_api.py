from io import BytesIO
from types import SimpleNamespace

import pandas as pd
from fastapi.testclient import TestClient

import api.routes.reports as report_routes
from app.main import app
from app.schemas.instruction_preparation import (
    InstructionPreparation,
    MissingParameter,
)


client = TestClient(app)


def create_excel_file() -> bytes:
    buffer = BytesIO()

    dataframe = pd.DataFrame(
        {
            "U [V]": [100, 200],
            "I [A]": [1.0, 2.0],
            "P [W]": [None, None],
        }
    )

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl",
    ) as writer:
        dataframe.to_excel(
            writer,
            sheet_name="Pomiary",
            index=False,
        )

    buffer.seek(0)

    return buffer.read()


def test_resolve_instruction_without_parameters():
    response = client.post(
        "/reports/resolve-instruction",
        data={
            "instruction": (
                "Obliczyć moc."
            ),
            "parameters": "[]",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "instruction": "Obliczyć moc.",
    }


def test_resolve_instruction_with_parameters():
    response = client.post(
        "/reports/resolve-instruction",
        data={
            "instruction": (
                "Obliczyć prędkość."
            ),
            "parameters": (
                '[{"symbol":"f1",'
                '"value":50,'
                '"unit":"Hz"}]'
            ),
        },
    )

    assert response.status_code == 200

    result = response.json()[
        "instruction"
    ]

    assert (
        result.startswith(
            "Obliczyć prędkość."
        )
    )

    assert (
        "Dodatkowe dane do ćwiczenia:"
        in result
    )

    assert "f1 = 50 Hz" in result


def test_resolve_instruction_invalid_json():
    response = client.post(
        "/reports/resolve-instruction",
        data={
            "instruction": "Test",
            "parameters": (
                "this is not json"
            ),
        },
    )

    assert response.status_code == 422

    assert (
        "Invalid parameters"
        in response.json()["detail"]
    )


def test_resolve_instruction_invalid_parameter():
    response = client.post(
        "/reports/resolve-instruction",
        data={
            "instruction": "Test",
            "parameters": (
                '[{"symbol":"f1"}]'
            ),
        },
    )

    assert response.status_code == 422

    assert (
        "Invalid parameters"
        in response.json()["detail"]
    )


def test_prepare_instruction(
    monkeypatch,
):
    excel_content = (
        create_excel_file()
    )

    captured = {}

    def fake_upload(
        instruction_file,
    ):
        captured[
            "uploaded_filename"
        ] = instruction_file.filename

        return "file_123"

    def fake_prepare(
        instruction_file_id,
        measurement_tables,
    ):
        captured[
            "instruction_file_id"
        ] = instruction_file_id

        captured[
            "measurement_tables"
        ] = measurement_tables

        return InstructionPreparation(
            instruction=(
                "Obliczyć moc P = U * I."
            ),
            missing_parameters=[
                MissingParameter(
                    name="Częstotliwość",
                    symbol="f1",
                    unit="Hz",
                    description=(
                        "Częstotliwość zasilania"
                    ),
                )
            ],
        )

    deleted = {}

    def fake_delete(
        file_id,
    ):
        deleted["file_id"] = (
            file_id
        )

    monkeypatch.setattr(
        report_routes,
        "upload_instruction_pdf",
        fake_upload,
    )

    monkeypatch.setattr(
        report_routes,
        "prepare_instruction",
        fake_prepare,
    )

    monkeypatch.setattr(
        report_routes,
        "delete_openai_file",
        fake_delete,
    )

    response = client.post(
        "/reports/prepare-instruction",
        files={
            "instruction_file": (
                "instruction.pdf",
                b"%PDF-fake-content",
                "application/pdf",
            ),
            "measurements": (
                "measurements.xlsx",
                excel_content,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            ),
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["instruction"] == (
        "Obliczyć moc P = U * I."
    )

    assert len(
        result["missing_parameters"]
    ) == 1

    assert result[
        "missing_parameters"
    ][0]["symbol"] == "f1"

    assert (
        captured[
            "uploaded_filename"
        ]
        == "instruction.pdf"
    )

    assert (
        captured[
            "instruction_file_id"
        ]
        == "file_123"
    )

    assert (
        deleted["file_id"]
        == "file_123"
    )


def test_prepare_instruction_passes_excel_metadata(
    monkeypatch,
):
    excel_content = (
        create_excel_file()
    )

    captured = {}

    monkeypatch.setattr(
        report_routes,
        "upload_instruction_pdf",
        lambda instruction_file: (
            "file_123"
        ),
    )

    def fake_prepare(
        instruction_file_id,
        measurement_tables,
    ):
        captured["tables"] = (
            measurement_tables
        )

        return InstructionPreparation(
            instruction="Test",
            missing_parameters=[],
        )

    monkeypatch.setattr(
        report_routes,
        "prepare_instruction",
        fake_prepare,
    )

    monkeypatch.setattr(
        report_routes,
        "delete_openai_file",
        lambda file_id: None,
    )

    response = client.post(
        "/reports/prepare-instruction",
        files={
            "instruction_file": (
                "instruction.pdf",
                b"%PDF-fake",
                "application/pdf",
            ),
            "measurements": (
                "measurements.xlsx",
                excel_content,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            ),
        },
    )

    assert response.status_code == 200

    tables = captured["tables"]

    assert len(tables) == 1

    table = tables[0]

    assert table.table_id == 1

    assert table.columns == [
        "U",
        "I",
        "P",
    ]

    assert table.units == {
        "U": "V",
        "I": "A",
        "P": "W",
    }

    assert (
        table.column_has_values
        == {
            "U": True,
            "I": True,
            "P": False,
        }
    )


def test_prepare_instruction_deletes_file_when_preparer_fails(
    monkeypatch,
):
    excel_content = (
        create_excel_file()
    )

    deleted = {}

    monkeypatch.setattr(
        report_routes,
        "upload_instruction_pdf",
        lambda instruction_file: (
            "file_123"
        ),
    )

    def fake_prepare(
        **kwargs,
    ):
        raise ValueError(
            "AI preparation failed"
        )

    monkeypatch.setattr(
        report_routes,
        "prepare_instruction",
        fake_prepare,
    )

    def fake_delete(
        file_id,
    ):
        deleted["file_id"] = (
            file_id
        )

    monkeypatch.setattr(
        report_routes,
        "delete_openai_file",
        fake_delete,
    )

    response = client.post(
        "/reports/prepare-instruction",
        files={
            "instruction_file": (
                "instruction.pdf",
                b"%PDF-fake",
                "application/pdf",
            ),
            "measurements": (
                "measurements.xlsx",
                excel_content,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            ),
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "AI preparation failed"
        ),
    }

    # Najważniejsze:
    # finally nadal musi usunąć
    # plik z OpenAI.
    assert (
        deleted["file_id"]
        == "file_123"
    )


def test_prepare_instruction_upload_error_returns_422(
    monkeypatch,
):
    excel_content = (
        create_excel_file()
    )

    def fake_upload(
        instruction_file,
    ):
        raise ValueError(
            "Instruction file must be a PDF."
        )

    monkeypatch.setattr(
        report_routes,
        "upload_instruction_pdf",
        fake_upload,
    )

    response = client.post(
        "/reports/prepare-instruction",
        files={
            "instruction_file": (
                "instruction.txt",
                b"not pdf",
                "text/plain",
            ),
            "measurements": (
                "measurements.xlsx",
                excel_content,
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            ),
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Instruction file must be a PDF."
        ),
    }
    
    
def test_analyze_report_pipeline(
    monkeypatch,
    tmp_path,
):
    profile = SimpleNamespace(
        first_name="Jan",
        last_name="Kowalski",
        university="Politechnika Lubelska",
        faculty="WEiI",
        field_of_study="Informatyka",
        semester="4",
        group="1",
        academic_year="2025/2026",
    )

    subject = SimpleNamespace(
        id="subject-1",
        name="Maszyny elektryczne",
        instructor_name="Jan Nowak",
        department="Katedra",
        laboratory="Lab 1",
    )

    table = SimpleNamespace(
        table_id=1,
        title="Pomiary",
        sheet_name="Pomiary",
        dataframe=pd.DataFrame(
            {
                "U": [100.0, 200.0],
                "I": [1.0, 2.0],
                "P": [100.0, 400.0],
            }
        ),
        units={
            "U": "V",
            "I": "A",
            "P": "W",
        },
    )

    specification = SimpleNamespace(
        calculations=[],
        charts=[],
        sections=[],
        model_dump=lambda: {
            "report_title": "Test report",
            "calculations": [],
            "charts": [],
            "sections": [],
        },
    )

    report_text = SimpleNamespace(
        model_dump=lambda: {
            "purpose": "Cel ćwiczenia",
            "sections": [],
            "conclusions": "Wnioski",
        },
    )

    captured = {}

    monkeypatch.setattr(
        report_routes,
        "load_user_profile",
        lambda: profile,
    )

    monkeypatch.setattr(
        report_routes,
        "get_subject",
        lambda subject_id: subject,
    )

    monkeypatch.setattr(
        report_routes,
        "read_measurement_tables",
        lambda file: [table],
    )

    monkeypatch.setattr(
        report_routes,
        "create_measurement_table_infos",
        lambda tables: ["table-info"],
    )

    def fake_parse(
        instruction,
        measurement_tables,
    ):
        captured["instruction"] = (
            instruction
        )

        captured[
            "measurement_tables"
        ] = measurement_tables

        return specification

    monkeypatch.setattr(
        report_routes,
        "parse_report_instruction_with_repair",
        fake_parse,
    )

    monkeypatch.setattr(
        report_routes,
        "execute_table_calculations",
        lambda tables, calculations: [
            table
        ],
    )

    monkeypatch.setattr(
        report_routes,
        "create_multi_table_chart_specifications",
        lambda specification, tables: [],
    )

    monkeypatch.setattr(
        report_routes,
        "analyze_report_sections",
        lambda specification, tables, charts: [],
    )

    monkeypatch.setattr(
        report_routes,
        "create_multi_table_example_calculations",
        lambda specification, tables, row_index: [],
    )

    monkeypatch.setattr(
        report_routes,
        "generate_report_text",
        lambda **kwargs: report_text,
    )

    report_dir = (
        tmp_path
        / "test-report"
    )

    report_dir.mkdir()

    (
        report_dir
        / "charts"
    ).mkdir()

    monkeypatch.setattr(
        report_routes,
        "create_report_workspace",
        lambda: (
            "test-report",
            report_dir,
        ),
    )

    monkeypatch.setattr(
        report_routes,
        "save_measurements",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        report_routes,
        "save_completed_measurement_tables",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        report_routes,
        "generate_multi_table_charts",
        lambda **kwargs: [],
    )

    def fake_save_state(**kwargs):
        captured["metadata"] = (
            kwargs["report_metadata"]
        )

    monkeypatch.setattr(
        report_routes,
        "save_report_state",
        fake_save_state,
    )

    response = client.post(
        "/reports/analyze",
        data={
            "instruction": (
                "Obliczyć moc."
            ),
            "subject_id": "subject-1",
            "execution_date": "2026-08-18",
            "team": "1",
        },
        files={
            "measurements": (
                "measurements.xlsx",
                b"fake excel",
                (
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            ),
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result["report_id"]
        == "test-report"
    )

    assert result[
        "specification"
    ]["report_title"] == (
        "Test report"
    )

    assert len(
        result["measurement_tables"]
    ) == 1

    result_table = (
        result[
            "measurement_tables"
        ][0]
    )

    assert result_table[
        "table_id"
    ] == 1

    assert result_table[
        "columns"
    ] == [
        "U",
        "I",
        "P",
    ]

    assert result_table[
        "rows"
    ] == 2

    assert result[
        "generated_charts"
    ] == 0

    metadata = captured[
        "metadata"
    ]

    assert (
        metadata.profile.first_name
        == "Jan"
    )

    assert (
        metadata.subject.id
        == "subject-1"
    )

    assert metadata.members == [
        "Jan Kowalski"
    ]

    assert metadata.team == "1"

    assert (
        metadata.execution_date
        == "2026-08-18"
    )
    
def test_analyze_applies_parameters_before_parser(
    monkeypatch,
    tmp_path,
):
    profile = SimpleNamespace(
        first_name="Jan",
        last_name="Kowalski",
        university="PL",
        faculty="WEiI",
        field_of_study="IZI",
        semester="4",
        group="1",
        academic_year="2025/2026",
    )

    subject = SimpleNamespace(
        id="subject-1",
        name="Maszyny",
        instructor_name="Prowadzący",
        department=None,
        laboratory=None,
    )

    table = SimpleNamespace(
        table_id=1,
        title="Pomiary",
        sheet_name="Pomiary",
        dataframe=pd.DataFrame(
            {
                "U": [100],
            }
        ),
        units={
            "U": "V",
        },
    )

    specification = SimpleNamespace(
        calculations=[],
        charts=[],
        sections=[],
        model_dump=lambda: {
            "calculations": [],
            "charts": [],
            "sections": [],
        },
    )

    report_text = SimpleNamespace(
        model_dump=lambda: {
            "purpose": None,
            "sections": [],
            "conclusions": None,
        },
    )

    captured = {}

    monkeypatch.setattr(
        report_routes,
        "load_user_profile",
        lambda: profile,
    )

    monkeypatch.setattr(
        report_routes,
        "get_subject",
        lambda subject_id: subject,
    )

    monkeypatch.setattr(
        report_routes,
        "read_measurement_tables",
        lambda file: [table],
    )

    monkeypatch.setattr(
        report_routes,
        "create_measurement_table_infos",
        lambda tables: [],
    )

    def fake_parse(
        instruction,
        measurement_tables,
    ):
        captured["instruction"] = (
            instruction
        )

        return specification

    monkeypatch.setattr(
        report_routes,
        "parse_report_instruction_with_repair",
        fake_parse,
    )

    monkeypatch.setattr(
        report_routes,
        "execute_table_calculations",
        lambda tables, calculations: [
            table
        ],
    )

    monkeypatch.setattr(
        report_routes,
        "create_multi_table_chart_specifications",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        report_routes,
        "analyze_report_sections",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        report_routes,
        "create_multi_table_example_calculations",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        report_routes,
        "generate_report_text",
        lambda **kwargs: report_text,
    )

    report_dir = (
        tmp_path
        / "report"
    )

    report_dir.mkdir()
    (
        report_dir
        / "charts"
    ).mkdir()

    monkeypatch.setattr(
        report_routes,
        "create_report_workspace",
        lambda: (
            "report-1",
            report_dir,
        ),
    )

    monkeypatch.setattr(
        report_routes,
        "save_measurements",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        report_routes,
        "save_completed_measurement_tables",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        report_routes,
        "generate_multi_table_charts",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        report_routes,
        "save_report_state",
        lambda **kwargs: None,
    )

    response = client.post(
        "/reports/analyze",
        data={
            "instruction": (
                "Obliczyć prędkość."
            ),
            "subject_id": "subject-1",
            "execution_date": "2026-08-18",
            "parameters": (
                '[{"symbol":"f1",'
                '"value":50,'
                '"unit":"Hz"}]'
            ),
        },
        files={
            "measurements": (
                "measurements.xlsx",
                b"fake",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 200

    assert (
        "Obliczyć prędkość."
        in captured["instruction"]
    )

    assert (
        "Dodatkowe dane do ćwiczenia:"
        in captured["instruction"]
    )

    assert (
        "f1 = 50 Hz"
        in captured["instruction"]
    )
    
    
def test_analyze_requires_profile(
    monkeypatch,
):
    monkeypatch.setattr(
        report_routes,
        "load_user_profile",
        lambda: None,
    )

    response = client.post(
        "/reports/analyze",
        data={
            "instruction": "Test",
            "subject_id": "subject-1",
            "execution_date": "2026-08-18",
        },
        files={
            "measurements": (
                "measurements.xlsx",
                b"fake",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "User profile must be created "
            "before generating a report."
        ),
    }


def test_analyze_unknown_subject(
    monkeypatch,
):
    profile = SimpleNamespace(
        first_name="Jan",
        last_name="Kowalski",
        university="PL",
        faculty="WEiI",
        field_of_study="IZI",
        semester="4",
        group="1",
        academic_year="2025/2026",
    )

    monkeypatch.setattr(
        report_routes,
        "load_user_profile",
        lambda: profile,
    )

    monkeypatch.setattr(
        report_routes,
        "get_subject",
        lambda subject_id: None,
    )

    response = client.post(
        "/reports/analyze",
        data={
            "instruction": "Test",
            "subject_id": "unknown",
            "execution_date": "2026-08-18",
        },
        files={
            "measurements": (
                "measurements.xlsx",
                b"fake",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Subject not found.",
    }


def test_analyze_invalid_parameters(
    monkeypatch,
):
    profile = SimpleNamespace(
        first_name="Jan",
        last_name="Kowalski",
        university="PL",
        faculty="WEiI",
        field_of_study="IZI",
        semester="4",
        group="1",
        academic_year="2025/2026",
    )

    monkeypatch.setattr(
        report_routes,
        "load_user_profile",
        lambda: profile,
    )

    response = client.post(
        "/reports/analyze",
        data={
            "instruction": "Test",
            "subject_id": "subject-1",
            "execution_date": "2026-08-18",
            "parameters": "not-json",
        },
        files={
            "measurements": (
                "measurements.xlsx",
                b"fake",
                "application/octet-stream",
            ),
        },
    )

    assert response.status_code == 422

    assert (
        "Invalid parameters"
        in response.json()["detail"]
    )
    
    
def test_get_report(
    monkeypatch,
):
    state = {
        "report_id": "report-1",
        "specification": {
            "report_title": "Test",
        },
    }

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    response = client.get(
        "/reports/report-1"
    )

    assert response.status_code == 200
    assert response.json() == state


def test_get_unknown_report_returns_404(
    monkeypatch,
):
    def fake_load(
        report_id,
    ):
        raise FileNotFoundError(
            "Report does not exist."
        )

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        fake_load,
    )

    response = client.get(
        "/reports/unknown"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Report does not exist.",
    }


def test_get_report_docx(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    completed_file = (
        report_dir
        / "completed_measurements.xlsx"
    )

    completed_file.write_bytes(
        b"fake excel"
    )

    state = {
        "report_id": "report-1",
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [
            {
                "table_id": 1,
                "title": "Pomiary",
                "sheet_name": "Pomiary",
                "columns": [
                    "U",
                    "I",
                ],
                "units": {
                    "U": "V",
                    "I": "A",
                },
            }
        ],
    }

    captured = {}

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    def fake_read(
        file,
        metadata,
    ):
        captured["file"] = file
        captured["metadata"] = metadata

        return [
            "fake-table"
        ]

    monkeypatch.setattr(
        report_routes,
        "read_completed_measurement_tables",
        fake_read,
    )

    output_path = (
        report_dir
        / "sprawozdanie.docx"
    )

    output_path.write_bytes(
        b"fake docx content"
    )

    def fake_generate(
        report_dir,
        state,
        tables,
    ):
        captured["tables"] = tables

        return output_path

    monkeypatch.setattr(
        report_routes,
        "generate_report_docx",
        fake_generate,
    )

    response = client.get(
        "/reports/report-1/docx"
    )

    assert response.status_code == 200

    assert response.content == (
        b"fake docx content"
    )

    assert response.headers[
        "content-type"
    ] == (
        "application/vnd.openxmlformats-"
        "officedocument.wordprocessingml.document"
    )

    assert (
        "sprawozdanie.docx"
        in response.headers[
            "content-disposition"
        ]
    )

    assert captured["metadata"] == (
        state["measurement_tables"]
    )

    assert captured["tables"] == [
        "fake-table"
    ]


def test_get_report_docx_unknown_report_returns_404(
    monkeypatch,
):
    def fake_load(
        report_id,
    ):
        raise FileNotFoundError(
            "Report does not exist."
        )

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        fake_load,
    )

    response = client.get(
        "/reports/unknown/docx"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Report does not exist.",
    }


def test_get_report_docx_missing_measurements_returns_404(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [],
    }

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    response = client.get(
        "/reports/report-1/docx"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Completed measurements file "
            "does not exist."
        ),
    }


def test_get_report_docx_invalid_measurements_returns_422(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    completed_file = (
        report_dir
        / "completed_measurements.xlsx"
    )

    completed_file.write_bytes(
        b"fake excel"
    )

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [],
    }

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    def fake_read(
        **kwargs,
    ):
        raise ValueError(
            "Invalid completed measurements."
        )

    monkeypatch.setattr(
        report_routes,
        "read_completed_measurement_tables",
        fake_read,
    )

    response = client.get(
        "/reports/report-1/docx"
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Invalid completed measurements."
        ),
    }


def test_get_report_docx_generation_error_returns_422(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    completed_file = (
        report_dir
        / "completed_measurements.xlsx"
    )

    completed_file.write_bytes(
        b"fake excel"
    )

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [],
    }

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    monkeypatch.setattr(
        report_routes,
        "read_completed_measurement_tables",
        lambda **kwargs: [],
    )

    def fake_generate(
        **kwargs,
    ):
        raise ValueError(
            "DOCX generation failed."
        )

    monkeypatch.setattr(
        report_routes,
        "generate_report_docx",
        fake_generate,
    )

    response = client.get(
        "/reports/report-1/docx"
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "DOCX generation failed."
        ),
    }
def test_get_report_data(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    completed_file = (
        report_dir
        / "completed_measurements.xlsx"
    )

    completed_file.write_bytes(
        b"fake excel"
    )

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [
            {
                "table_id": 1,
                "title": "Pomiary",
                "sheet_name": "Pomiary",
                "columns": [
                    "U",
                    "I",
                    "P",
                ],
                "units": {
                    "U": "V",
                    "I": "A",
                    "P": "W",
                },
            }
        ],
    }

    table = SimpleNamespace(
        table_id=1,
        title="Pomiary",
        sheet_name="Pomiary",
        dataframe=pd.DataFrame(
            {
                "U": [
                    100.0,
                    200.0,
                ],
                "I": [
                    1.0,
                    2.0,
                ],
                "P": [
                    100.0,
                    None,
                ],
            }
        ),
        units={
            "U": "V",
            "I": "A",
            "P": "W",
        },
    )

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    monkeypatch.setattr(
        report_routes,
        "read_completed_measurement_tables",
        lambda **kwargs: [table],
    )

    response = client.get(
        "/reports/report-1/data"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["report_id"] == (
        "report-1"
    )

    assert len(
        result["tables"]
    ) == 1

    result_table = (
        result["tables"][0]
    )

    assert result_table[
        "table_id"
    ] == 1

    assert result_table[
        "columns"
    ] == [
        "U",
        "I",
        "P",
    ]

    assert result_table[
        "units"
    ] == {
        "U": "V",
        "I": "A",
        "P": "W",
    }

    assert result_table[
        "rows"
    ] == [
        {
            "U": 100.0,
            "I": 1.0,
            "P": 100.0,
        },
        {
            "U": 200.0,
            "I": 2.0,
            "P": None,
        },
    ]


def test_get_report_data_unknown_report_returns_404(
    monkeypatch,
):
    def fake_load(
        report_id,
    ):
        raise FileNotFoundError(
            "Report does not exist."
        )

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        fake_load,
    )

    response = client.get(
        "/reports/unknown/data"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Report does not exist.",
    }


def test_get_report_data_missing_file_returns_404(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [],
    }

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    response = client.get(
        "/reports/report-1/data"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Completed measurements file "
            "does not exist."
        ),
    }


def test_update_example_calculations(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    completed_file = (
        report_dir
        / "completed_measurements.xlsx"
    )

    completed_file.write_bytes(
        b"fake excel"
    )

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [],
        "specification": {
            "report_title": "Test",
            "calculations": [],
            "charts": [],
            "sections": [],
        },
    }

    captured = {}

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    monkeypatch.setattr(
        report_routes,
        "read_completed_measurement_tables",
        lambda **kwargs: [
            "fake-table"
        ],
    )

    examples = [
        {
            "output": "P",
            "row_index": 1,
            "result": 400,
        }
    ]

    def fake_examples(
        specification,
        tables,
        row_index,
    ):
        captured["row_index"] = (
            row_index
        )

        return examples

    monkeypatch.setattr(
        report_routes,
        "create_multi_table_example_calculations",
        fake_examples,
    )

    def fake_save(
        report_id,
        state,
    ):
        captured["saved_state"] = (
            state.copy()
        )

    monkeypatch.setattr(
        report_routes,
        "save_report_state_data",
        fake_save,
    )

    response = client.patch(
        "/reports/report-1/example-calculations",
        json={
            "row_index": 1,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["report_id"] == (
        "report-1"
    )

    assert result[
        "row_index"
    ] == 1

    assert result[
        "example_calculations"
    ] == examples

    assert (
        captured["row_index"]
        == 1
    )

    saved_state = captured[
        "saved_state"
    ]

    assert saved_state[
        "example_row_index"
    ] == 1

    assert saved_state[
        "example_calculations"
    ] == examples


def test_update_example_calculations_invalid_row_returns_422(
    monkeypatch,
    tmp_path,
):
    report_dir = (
        tmp_path
        / "report-1"
    )

    report_dir.mkdir()

    completed_file = (
        report_dir
        / "completed_measurements.xlsx"
    )

    completed_file.write_bytes(
        b"fake excel"
    )

    state = {
        "completed_measurements_file": (
            "completed_measurements.xlsx"
        ),
        "measurement_tables": [],
        "specification": {
            "report_title": "Test",
            "calculations": [],
            "charts": [],
            "sections": [],
        },
    }

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        lambda report_id: state,
    )

    monkeypatch.setattr(
        report_routes,
        "get_report_dir",
        lambda report_id: report_dir,
    )

    monkeypatch.setattr(
        report_routes,
        "read_completed_measurement_tables",
        lambda **kwargs: [],
    )

    def fake_examples(
        **kwargs,
    ):
        raise ValueError(
            "Invalid measurement row."
        )

    monkeypatch.setattr(
        report_routes,
        "create_multi_table_example_calculations",
        fake_examples,
    )

    response = client.patch(
        "/reports/report-1/example-calculations",
        json={
            "row_index": 999,
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Invalid measurement row."
        ),
    }


def test_update_example_calculations_missing_report_returns_404(
    monkeypatch,
):
    def fake_load(
        report_id,
    ):
        raise FileNotFoundError(
            "Report does not exist."
        )

    monkeypatch.setattr(
        report_routes,
        "load_report_state",
        fake_load,
    )

    response = client.patch(
        "/reports/unknown/example-calculations",
        json={
            "row_index": 0,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Report does not exist."
        ),
    }