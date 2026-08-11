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

from app.services.example_calculations import (
    create_example_calculations,
)

from app.schemas.report import (
    ReportSpecification,
    UpdateExampleRowRequest,
)

from app.services.result_analyzer import analyze_section
from app.services.report_text_generator import generate_report_text


router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/analyze")
async def analyze_report(
    instruction: Annotated[str, Form()],
    measurements: Annotated[UploadFile, File()],
):
    # --------------------------------------------------------
    # 1. Excel
    # --------------------------------------------------------

    df, units = read_meansurements(
        measurements.file
    )

    # --------------------------------------------------------
    # 2. Analiza instrukcji przez AI
    # --------------------------------------------------------

    specification = parse_report_instruction(
        instruction=instruction,
        available_columns=df.columns.tolist(),
        units=units,
    )

    # --------------------------------------------------------
    # 3. Obliczenia
    # --------------------------------------------------------

    try:
        completed_df = execute_calculations(
            df=df,
            calculations=specification.calculations,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    # --------------------------------------------------------
    # 4. Jednostki obliczonych kolumn
    # --------------------------------------------------------

    for calculation in specification.calculations:

        if calculation.output not in units:
            units[calculation.output] = calculation.unit

        elif units[calculation.output] is None:
            units[calculation.output] = calculation.unit

    # --------------------------------------------------------
    # 5. Przykładowe obliczenia
    # --------------------------------------------------------

    try:
        example_calculations = create_example_calculations(
            df=completed_df,
            calculations=specification.calculations,
            units=units,
            row_index=0,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    # --------------------------------------------------------
    # 6. Specyfikacja wykresów
    # --------------------------------------------------------

    try:
        charts = create_chart_specifications(
            specification,
            completed_df,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    # --------------------------------------------------------
    # 7. Deterministyczna analiza każdej sekcji
    # --------------------------------------------------------

    section_analyses = []

    for section in specification.sections:

        section_analysis = analyze_section(
            df=completed_df,
            section=section,
            units=units,
            charts=charts,
        )

        section_analyses.append(
            section_analysis
        )

    # --------------------------------------------------------
    # 8. Generowanie całego tekstu sprawozdania
    # --------------------------------------------------------

    # WAŻNE:
    # to jest POZA pętlą for section

    try:
        report_text = generate_report_text(
            specification=specification,
            analyses=section_analyses,
            instruction=instruction,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    # --------------------------------------------------------
    # 9. Workspace raportu
    # --------------------------------------------------------

    report_id, report_dir = create_report_workspace()

    # --------------------------------------------------------
    # 10. Zapis plików Excel
    # --------------------------------------------------------

    save_measurements(
        measurements.file,
        report_dir,
    )

    save_completed_measurements(
        completed_df,
        report_dir,
    )

    # --------------------------------------------------------
    # 11. Generowanie wykresów PNG
    # --------------------------------------------------------

    generated_files = generate_chart(
        df=completed_df,
        units=units,
        charts=charts,
        output_dir=report_dir / "charts",
    )

    # --------------------------------------------------------
    # 12. Zapis całego stanu raportu
    # --------------------------------------------------------

    save_report_state(
        report_dir=report_dir,
        report_id=report_id,
        specification=specification,
        charts=charts,
        units=units,
        example_calculations=example_calculations,
        section_analyses=section_analyses,
        report_text=report_text,
    )

    # --------------------------------------------------------
    # 13. Response
    # --------------------------------------------------------

    return {
        "report_id": report_id,

        "specification": specification.model_dump(),

        "charts": [
            chart.model_dump()
            for chart in charts
        ],

        "example_calculations": example_calculations,

        "section_analyses": [
            analysis.model_dump()
            for analysis in section_analyses
        ],

        "report_text": report_text.model_dump(),

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
    
    
@router.patch("/{report_id}/example-calculations")
def update_example_calculations(
    report_id: str,
    request: UpdateExampleRowRequest,
):
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

    df, _ = read_meansurements(
        str(completed_file)
    )

    specification = ReportSpecification.model_validate(
        state["specification"]
    )

    try:
        examples = create_example_calculations(
            df=df,
            calculations=specification.calculations,
            units=state["units"],
            row_index=request.row_index,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    state["example_calculations"] = examples
    state["example_row_index"] = request.row_index

    save_report_state_data(
        report_id,
        state
    )

    return {
        "report_id": report_id,
        "row_index": request.row_index,
        "example_calculations": examples,
    }