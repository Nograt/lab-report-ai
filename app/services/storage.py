from pathlib import Path
from uuid import uuid4


STORAGE_DIR = Path("storage/reports")


def create_report_workspace() -> tuple[str, Path]:
    report_id = str(uuid4())

    report_dir = STORAGE_DIR / report_id
    charts_dir = report_dir / "charts"

    charts_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return report_id, report_dir
    
    
    
    