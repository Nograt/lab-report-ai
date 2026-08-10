from pathlib import Path
from uuid import uuid4
import json
import shutil
from typing import BinaryIO



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
    file_path = report_dir / "mesaurements.xlsx"
    
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
    units
) -> Path:

    state = {
        "report_id": report_id,
        "specification": specification.model_dump(),
        "charts": [
            chart.model_dump()
            for chart in charts
        ],
        "units": units,
        "measurements_file": "measurements.xlsx",
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
    
    
    
    