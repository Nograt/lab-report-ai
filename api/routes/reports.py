from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.services.instruction_parser import parse_report_instruction
from app.services.excel_reader import read_meansurements
from app.services.chart_generator import create_chart_specifications


router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/analyze")
async def analyze_report(instruction: Annotated[str, Form()], measurements: Annotated[UploadFile, File()]):
   
    specification = parse_report_instruction(instruction)
    
    
    df, units = read_meansurements(measurements.file)
    
    try:
        charts = create_chart_specifications(specification,df)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
   
   
    return {
        "filename": measurements.filename,

        "specification": specification.model_dump(),

        "measurements": {
            "columns": df.columns.tolist(),
            "rows": len(df),
            "units": units,
        },
        "charts": [
    chart.model_dump()
    for chart in charts
],
    }