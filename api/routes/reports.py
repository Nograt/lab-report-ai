from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.services.instruction_parser import parse_report_instruction
from app.services.excel_reader import read_meansurements
from app.services.chart_generator import create_chart_specifications, generate_chart
from app.services.storage import create_report_workspace



router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/analyze")
async def analyze_report(instruction: Annotated[str, Form()], measurements: Annotated[UploadFile, File()]):
   
    specification = parse_report_instruction(instruction)
    
    
    df, units = read_meansurements(measurements.file)
    
    
    try:
        charts = create_chart_specifications(specification,df)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    
    
    report_id, report_dir = create_report_workspace()
    
    print("REPORT DIR:", report_dir.resolve())
    print("CHARTS DIR:", (report_dir / "charts").resolve())
    
    generated_files = generate_chart(df=df, units=units,charts=charts,output_dir= report_dir/ "charts")
    
    print("GENERATED FILES:", generated_files)
    
    for file in generated_files:
        print(file.resolve(), file.exists())
    
   
   
    return {
    "report_id": report_id,
    "specification": specification.model_dump(),
    "charts": [
        chart.model_dump()
        for chart in charts
    ],
    "generated_charts": len(generated_files),
}