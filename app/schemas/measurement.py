from pydantic import BaseModel

class MeasurementTableInfo(BaseModel):
    table_id: int

    title: str | None = None

    sheet_name: str | None = None

    columns: list[str]

    units: dict[str, str | None]
    
    column_has_values: dict[str, bool]
    
    
