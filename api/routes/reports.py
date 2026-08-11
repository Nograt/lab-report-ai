from typing import Annotated
import shutil
import pandas as pd
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.services.instruction_parser import parse_report_instruction
from app.services.excel_reader import read_meansurements
from app.services.chart_generator import (
    create_chart_specifications,
    generate_chart,
    match_column_name,
)
from app.services.storage import (
    create_report_workspace,
    save_measurements,
    save_report_state,
    load_report_state,
    get_report_dir,
    save_report_state_data,
    save_completed_measurements,
)
from app.schemas.chart import UpdateChartsRequest
from app.services.calculation_engine import execute_calculations




router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/analyze")
async def analyze_report(instruction: Annotated[str, Form()], measurements: Annotated[UploadFile, File()]):
   
    specification = parse_report_instruction(instruction
                                             )
    df, units = read_meansurements(measurements.file)
    
    try:
        completed_df = execute_calculations(df=df,calculations=specification.calculations,)

    except ValueError as error:
        raise HTTPException(
        status_code=422,
        detail=str(error)
    )
        
    for calculation in specification.calculations:
        if calculation.output not in units:
            units[calculation.output] = calculation.unit
        
        elif units[calculation.output] is None:
            units[calculation.output] = calculation.unit
            
    try:
        charts = create_chart_specifications(specification,completed_df)

    except ValueError as error:
        raise HTTPException(status_code=422,detail=str(error))
    
    report_id, report_dir = create_report_workspace()
    
    save_measurements( measurements.file, report_dir)
    
    save_completed_measurements(completed_df,report_dir)
    
    
    generated_files = generate_chart(df=completed_df, units=units,charts=charts,output_dir= report_dir/ "charts")
    
    print("REPORT ID:", report_id)
    print("REPORT DIR:", report_dir.resolve())
    print("GENERATED FILES:", generated_files)

    for file in generated_files:
        print("FILE:", file.resolve())
        print("EXISTS:", file.exists())
    
    save_report_state(report_dir=report_dir,report_id=report_id,specification=specification,charts=charts,units=units)

   
   
    return {
    "report_id": report_id,
    "specification": specification.model_dump(),
    "charts": [
        chart.model_dump()
        for chart in charts
    ],
    "generated_charts": len(generated_files),
}
    
@router.get("/{report_id}")
def get_report(report_id:str):
    try:
        state = load_report_state(report_id)
        
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    
    return state

@router.patch("/{report_id}/charts")
def update_report_charts(
    report_id: str,
    request: UpdateChartsRequest
):
    try:
        state = load_report_state(report_id)
        report_dir = get_report_dir(report_id)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    measurements_path = (
        report_dir / state["completed_measurements_file"]
    )

    df, units = read_meansurements(
        str(measurements_path)
    )

    charts = []

    try:
        for chart in request.charts:

            x = match_column_name(
                chart.x,
                df
            )

            y = match_column_name(
                chart.y,
                df
            )

            normalized_chart = chart.model_copy(
                update={
                    "x": x,
                    "y": y,
                }
            )

            charts.append(normalized_chart)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )
        
    temp_dir = report_dir / "charts_temp"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        
    try:
        generated_files = generate_chart(
            df=df,
            units=units,
            charts=charts,
            output_dir=temp_dir
        )

    except ValueError as error:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )
        
    charts_dir = report_dir / "charts"

    if charts_dir.exists():
        shutil.rmtree(charts_dir)

    temp_dir.rename(charts_dir)
    
    state["charts"] = [
        chart.model_dump()
        for chart in charts
    ]

    state["units"] = units

    save_report_state_data(
        report_id,
        state
        )
    
    return {
        "report_id": report_id,
        "charts": [
            chart.model_dump()
            for chart in charts
        ],
        "generated_charts": len(generated_files),
    }
    
@router.get("/{report_id}/data")
def get_report_data(report_id: str):
    try:
        state = load_report_state(report_id)
        report_dir = get_report_dir(report_id)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    completed_file = (
        report_dir
        / state["completed_measurements_file"]
    )

    if not completed_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Completed measurements file does not exist."
        )

    df, _ = read_meansurements(
        str(completed_file)
    )

    clean_df = (
        df.astype(object)
        .where(pd.notna(df), None)
    )

    return {
        "report_id": report_id,
        "columns": df.columns.tolist(),
        "units": state["units"],
        "rows": clean_df.to_dict(
            orient="records"
        ),
    }