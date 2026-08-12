from pathlib import Path
from uuid import uuid4
import json
import shutil
from typing import BinaryIO
import pandas as pd
from app.services.excel_reader import MeasurementTableData



PROJECT_ROOT = Path(__file__).resolve().parents[2]

STORAGE_DIR = PROJECT_ROOT / "storage" / "reports"


def create_report_workspace() -> tuple[str, Path]:
    report_id = str(uuid4())

    report_dir = STORAGE_DIR / report_id
    charts_dir = report_dir / "charts"

    charts_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return report_id, report_dir

def save_measurements(file: BinaryIO, report_dir: Path) -> Path:
    file_path = report_dir /  "measurements.xlsx"
    
    file.seek(0)
    
    with file_path.open("wb") as destination:
        shutil.copyfileobj(file, destination)
        
    file.seek(0)
    
    return file_path

def save_report_state(
     report_dir: Path,
    report_id: str,
    specification,
    charts,
    units,
    example_calculations,
    section_analyses,
    report_text,
    measurement_tables,
) -> Path:

    state = {
    "report_id": report_id,

    "specification": specification.model_dump(),

    "charts": [
        chart.model_dump()
        for chart in charts
    ],

    "units": units,

    "example_calculations": example_calculations,

    "measurements_file": "measurements.xlsx",

    "completed_measurements_file":
        "completed_measurements.xlsx",
        
    "section_analyses": [
    analysis.model_dump()
    for analysis in section_analyses
],

"report_text": report_text.model_dump(),
"measurement_tables": [
    {
        "table_id": table.table_id,
        "title": table.title,
        "sheet_name": table.sheet_name,
        "columns": table.dataframe.columns.tolist(),
        "units": table.units,
    }
    for table in measurement_tables
],
}

    file_path = report_dir / "report.json"

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=4
        )

    return file_path

def load_report_state(report_id: str) -> dict:
    report_dir = STORAGE_DIR / report_id
    state_file = report_dir / "report.json"

    if not report_dir.exists():
        raise FileNotFoundError(
            f"Report '{report_id}' does not exist."
        )

    if not state_file.exists():
        raise FileNotFoundError(
            f"State file for report '{report_id}' does not exist."
        )

    with state_file.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)
    
    
def get_report_dir(report_id: str) -> Path:
    report_dir = STORAGE_DIR / report_id

    if not report_dir.exists():
        raise FileNotFoundError(
            f"Report '{report_id}' does not exist."
        )

    return report_dir

def save_report_state_data(
    report_id: str,
    state: dict
    
) -> Path:

    report_dir = get_report_dir(report_id)

    file_path = report_dir / "report.json"

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=4
        )

    return file_path

def save_completed_measurements(
    df: pd.DataFrame,
    report_dir: Path
) -> Path:

    file_path = (
        report_dir / "completed_measurements.xlsx"
    )

    df.to_excel(
        file_path,
        index=False
    )

    return file_path

def save_completed_measurement_tables(
    tables: list[MeasurementTableData],
    report_dir: Path,
) -> Path:

    file_path = (
        report_dir
        / "completed_measurements.xlsx"
    )

    with pd.ExcelWriter(
        file_path,
        engine="openpyxl",
    ) as writer:

        for table in tables:

            table.dataframe.to_excel(
                writer,
                sheet_name=table.sheet_name,
                index=False,
            )

    return file_path