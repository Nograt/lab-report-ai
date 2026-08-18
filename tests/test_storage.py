import json
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest

import app.services.storage as storage
from app.services.excel_reader import MeasurementTableData


class FakeModel:
    def __init__(self, data: dict):
        self.data = data

    def model_dump(self):
        return self.data


def measurement_table(
    table_id: int,
    sheet_name: str,
    dataframe: pd.DataFrame,
) -> MeasurementTableData:
    return MeasurementTableData(
        table_id=table_id,
        title=sheet_name,
        sheet_name=sheet_name,
        dataframe=dataframe,
        units={},
    )


def test_create_report_workspace(
    tmp_path,
    monkeypatch,
):
    reports_dir = tmp_path / "reports"

    monkeypatch.setattr(
        storage,
        "STORAGE_DIR",
        reports_dir,
    )

    report_id, report_dir = (
        storage.create_report_workspace()
    )

    assert report_id
    assert report_dir.exists()

    assert (
        report_dir
        / "charts"
    ).exists()

    assert report_dir.parent == reports_dir


def test_save_measurements(
    tmp_path,
):
    report_dir = tmp_path / "report"
    report_dir.mkdir()

    source = BytesIO(
        b"example excel content"
    )

    file_path = storage.save_measurements(
        file=source,
        report_dir=report_dir,
    )

    assert file_path.exists()

    assert file_path.name == (
        "measurements.xlsx"
    )

    assert file_path.read_bytes() == (
        b"example excel content"
    )

    # Funkcja powinna przewinąć plik
    # z powrotem na początek.
    assert source.tell() == 0


def test_save_completed_measurement_tables(
    tmp_path,
):
    report_dir = tmp_path / "report"
    report_dir.mkdir()

    tables = [
        measurement_table(
            table_id=1,
            sheet_name="Bieg jalowy",
            dataframe=pd.DataFrame(
                {
                    "U": [100, 200],
                    "I": [1.0, 2.0],
                }
            ),
        ),
        measurement_table(
            table_id=2,
            sheet_name="Obciazenie",
            dataframe=pd.DataFrame(
                {
                    "P": [100, 200],
                    "n": [1500, 1400],
                }
            ),
        ),
    ]

    file_path = (
        storage.save_completed_measurement_tables(
            tables=tables,
            report_dir=report_dir,
        )
    )

    assert file_path.exists()

    excel = pd.ExcelFile(
        file_path
    )

    assert excel.sheet_names == [
        "Bieg jalowy",
        "Obciazenie",
    ]

    first_table = pd.read_excel(
        excel,
        sheet_name="Bieg jalowy",
    )

    second_table = pd.read_excel(
        excel,
        sheet_name="Obciazenie",
    )

    assert first_table.columns.tolist() == [
        "U",
        "I",
    ]

    assert second_table.columns.tolist() == [
        "P",
        "n",
    ]

    assert first_table["U"].tolist() == [
        100,
        200,
    ]

    assert second_table["n"].tolist() == [
        1500,
        1400,
    ]


def test_overwrite_report_state(
    tmp_path,
):
    report_dir = tmp_path / "report"
    report_dir.mkdir()

    state = {
        "report_id": "abc",
        "status": "completed",
    }

    storage.overwrite_report_state(
        report_dir=report_dir,
        state=state,
    )

    report_file = (
        report_dir
        / "report.json"
    )

    assert report_file.exists()

    loaded = json.loads(
        report_file.read_text(
            encoding="utf-8"
        )
    )

    assert loaded == state


def test_save_and_load_report_state_data(
    tmp_path,
    monkeypatch,
):
    reports_dir = tmp_path / "reports"

    monkeypatch.setattr(
        storage,
        "STORAGE_DIR",
        reports_dir,
    )

    report_id = "test-report"

    report_dir = (
        reports_dir
        / report_id
    )

    report_dir.mkdir(
        parents=True
    )

    state = {
        "report_id": report_id,
        "value": 123,
    }

    storage.save_report_state_data(
        report_id=report_id,
        state=state,
    )

    loaded = storage.load_report_state(
        report_id
    )

    assert loaded == state


def test_get_report_dir_unknown_report_raises_error(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        storage,
        "STORAGE_DIR",
        tmp_path / "reports",
    )

    with pytest.raises(
        FileNotFoundError,
        match="does not exist",
    ):
        storage.get_report_dir(
            "unknown-report"
        )


def test_load_report_state_without_json_raises_error(
    tmp_path,
    monkeypatch,
):
    reports_dir = tmp_path / "reports"

    monkeypatch.setattr(
        storage,
        "STORAGE_DIR",
        reports_dir,
    )

    report_dir = (
        reports_dir
        / "test-report"
    )

    report_dir.mkdir(
        parents=True
    )

    with pytest.raises(
        FileNotFoundError,
        match="State file",
    ):
        storage.load_report_state(
            "test-report"
        )


def test_save_complete_report_state(
    tmp_path,
):
    report_dir = tmp_path / "report"
    report_dir.mkdir()

    table = measurement_table(
        table_id=1,
        sheet_name="Pomiary",
        dataframe=pd.DataFrame(
            {
                "U": [100, 200],
                "I": [1.0, 2.0],
            }
        ),
    )

    table.units = {
        "U": "V",
        "I": "A",
    }

    specification = FakeModel(
        {
            "report_title": "Test",
            "sections": [],
        }
    )

    chart = FakeModel(
        {
            "figure_id": 1,
            "x": "U",
            "y": "I",
        }
    )

    analysis = FakeModel(
        {
            "section_id": 1,
            "columns": [],
            "charts": [],
        }
    )

    report_text = FakeModel(
        {
            "purpose": "Cel",
            "sections": [],
            "conclusions": "Wnioski",
        }
    )

    metadata = FakeModel(
        {
            "team": "1",
        }
    )

    file_path = storage.save_report_state(
        report_dir=report_dir,
        report_id="abc",
        specification=specification,
        charts=[chart],
        units={
            "U": "V",
            "I": "A",
        },
        example_calculations=[],
        section_analyses=[
            analysis
        ],
        report_text=report_text,
        measurement_tables=[
            table
        ],
        report_metadata=metadata,
    )

    assert file_path.exists()

    state = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    assert state["report_id"] == "abc"

    assert state["measurements_file"] == (
        "measurements.xlsx"
    )

    assert (
        state["completed_measurements_file"]
        == "completed_measurements.xlsx"
    )

    assert state["specification"][
        "report_title"
    ] == "Test"

    assert state["measurement_tables"][0][
        "table_id"
    ] == 1

    assert state["measurement_tables"][0][
        "columns"
    ] == [
        "U",
        "I",
    ]