from typing import Annotated
import shutil
import pandas as pd
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.services.instruction_parser import parse_report_instruction
from app.services.chart_generator import (
    create_chart_specifications,
    generate_chart,
    match_column_name,
)
from fastapi.responses import FileResponse

from app.services.docx_generator import (
    generate_report_docx,
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

from app.services.excel_reader import (
    read_meansurements,
    read_measurement_tables,
    read_completed_measurement_tables,
    create_measurement_table_infos,
    get_measurement_table,
)

from app.services.calculation_engine import (
    execute_table_calculations,
)

from app.services.chart_generator import (
    create_multi_table_chart_specifications,
    generate_multi_table_charts,
)

from app.services.result_analyzer import (
    analyze_report_sections,
)

from app.services.example_calculations import (
    create_multi_table_example_calculations,
)

from app.services.report_text_generator import (
    generate_report_text,
)

from app.services.storage import (
    create_report_workspace,
    save_measurements,
    save_completed_measurement_tables,
    save_report_state,
)

from app.services.specification_validator import (
    validate_report_specification,
)

from app.services.instruction_parser import (
    parse_report_instruction_with_repair,
    repair_report_specification,
)

from app.schemas.chart import ChartSpecification

from app.services.storage import (
    overwrite_report_state,
)

from app.schemas.report_metadata import (
    ProfileSnapshot,
    SubjectSnapshot,
    ReportMetadata,
)

from app.services.profile_storage import (
    load_user_profile,
)

from app.services.subject_storage import (
    get_subject,
)

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/{report_id}/docx")
def get_report_docx(
    report_id: str,
):
    try:
        state = load_report_state(
            report_id
        )

        report_dir = get_report_dir(
            report_id
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    completed_file = (
        report_dir
        / state["completed_measurements_file"]
    )

    if not completed_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Completed measurements file "
                "does not exist."
            ),
        )

    try:
        tables = read_completed_measurement_tables(
            file=str(completed_file),
            metadata=state["measurement_tables"],
        )

        output_path = generate_report_docx(
            report_dir=report_dir,
            state=state,
            tables=tables,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    return FileResponse(
        path=output_path,
        filename="sprawozdanie.docx",
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
    )

@router.post("/analyze")
async def analyze_report(
    instruction: Annotated[str, Form()],
    measurements: Annotated[UploadFile, File()],

    subject_id: Annotated[str, Form()],
    execution_date: Annotated[str, Form()],

    team: Annotated[str, Form()] = "",
    members: Annotated[str | None, Form()] = None,
):
    
    profile = load_user_profile()

    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "User profile must be created "
                "before generating a report."
            ),
        )


    subject = get_subject(
        subject_id
    )

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail="Subject not found.",
        )

    if members:
        member_names = [
            name.strip()
            for name in members.split(",")
            if name.strip()
        ]

    else:
        member_names = [
            (
                f"{profile.first_name} "
                f"{profile.last_name}"
            ).strip()
        ]

    report_metadata = ReportMetadata(
        profile=ProfileSnapshot(
            first_name=profile.first_name,
            last_name=profile.last_name,
            university=profile.university,
            faculty=profile.faculty,
            field_of_study=profile.field_of_study,
            semester=profile.semester,
            group=profile.group,
            academic_year=profile.academic_year,
        ),

        subject=SubjectSnapshot(
            id=subject.id,
            name=subject.name,
            instructor_name=subject.instructor_name,
            department=subject.department,
            laboratory=subject.laboratory,
        ),

        members=member_names,
        team=team,
        execution_date=execution_date,
    )

    try:
        measurement_tables = read_measurement_tables(
            measurements.file
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    table_infos = create_measurement_table_infos(
        measurement_tables
    )

    try:
        specification = parse_report_instruction_with_repair(
        instruction=instruction,
        measurement_tables=table_infos,
    )

    except ValueError as error:
        raise HTTPException(
        status_code=422,
        detail=str(error),
    )


    try:
        validate_report_specification(
        specification=specification,
        measurement_tables=table_infos,
    )

    except ValueError as first_error:
        specification = repair_report_specification(
        specification=specification,
        validation_error=str(first_error),
        instruction=instruction,
        measurement_tables=table_infos,
    )
    try:
        validate_report_specification(
            specification=specification,
            measurement_tables=table_infos,
        )

    except ValueError as second_error:
        raise HTTPException(
            status_code=422,
            detail=(
                "Report specification remained invalid "
                f"after automatic repair: {second_error}"
            ),
        )

    try:
        completed_tables = execute_table_calculations(
            tables=measurement_tables,
            calculations=specification.calculations,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    try:
        charts = create_multi_table_chart_specifications(
            specification=specification,
            tables=completed_tables,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    try:
        section_analyses = analyze_report_sections(
            specification=specification,
            tables=completed_tables,
            charts=charts,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    try:
        example_calculations = (
            create_multi_table_example_calculations(
                specification=specification,
                tables=completed_tables,
                row_index=0,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


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


    report_id, report_dir = create_report_workspace()


    measurements.file.seek(0)

    save_measurements(
        measurements.file,
        report_dir,
    )

    save_completed_measurement_tables(
        tables=completed_tables,
        report_dir=report_dir,
    )

    generated_files = generate_multi_table_charts(
        specification=specification,
        tables=completed_tables,
        charts=charts,
        output_dir=report_dir / "charts",
    )


    save_report_state(
    report_dir=report_dir,
    report_id=report_id,
    specification=specification,
    charts=charts,

    units={},

    example_calculations=example_calculations,
    section_analyses=section_analyses,
    report_text=report_text,
    measurement_tables=completed_tables,

    report_metadata=report_metadata,
)


    return {
        "report_id": report_id,

        "specification": specification.model_dump(),

        "measurement_tables": [
            {
                "table_id": table.table_id,
                "title": table.title,
                "sheet_name": table.sheet_name,
                "columns": table.dataframe.columns.tolist(),
                "units": table.units,
                "rows": len(table.dataframe),
            }
            for table in completed_tables
        ],

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
    request: UpdateChartsRequest,
):
    

    try:
        state = load_report_state(report_id)
        report_dir = get_report_dir(report_id)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


    measurements_path = (
        report_dir
        / state["completed_measurements_file"]
    )

    if not measurements_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Completed measurements file does not exist.",
        )

    try:
        tables = read_completed_measurement_tables(
            file=str(measurements_path),
            metadata=state["measurement_tables"],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    specification = ReportSpecification.model_validate(
        state["specification"]
    )


    section_by_figure_id = {}

    for section in specification.sections:

        for figure_id in section.chart_figure_ids:

            if figure_id in section_by_figure_id:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Chart figure_id={figure_id} "
                        "belongs to more than one section."
                    ),
                )

            section_by_figure_id[
                figure_id
            ] = section



    charts_by_id = {
        chart.figure_id: ChartSpecification(
            figure_id=chart.figure_id,
            x=chart.x,
            y=chart.y,
        )
        for chart in specification.charts
    }

    for saved_chart_data in state.get(
        "charts",
        [],
    ):
        saved_chart = (
            ChartSpecification.model_validate(
                saved_chart_data
            )
        )

        charts_by_id[
            saved_chart.figure_id
        ] = saved_chart



    request_figure_ids = [
        chart.figure_id
        for chart in request.charts
    ]

    if len(request_figure_ids) != len(
        set(request_figure_ids)
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "The PATCH request contains duplicate "
                "figure_id values."
            ),
        )


    try:
        for chart in request.charts:

            section = section_by_figure_id.get(
                chart.figure_id
            )

            if section is None:
                raise ValueError(
                    f"Unknown figure_id={chart.figure_id}."
                )

            table = get_measurement_table(
                tables=tables,
                table_id=section.table_id,
            )

            x = match_column_name(
                chart.x,
                table.dataframe,
            )

            y = match_column_name(
                chart.y,
                table.dataframe,
            )

            normalized_chart = chart.model_copy(
                update={
                    "x": x,
                    "y": y,
                }
            )

            charts_by_id[
                chart.figure_id
            ] = normalized_chart

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )



    charts = sorted(
        charts_by_id.values(),
        key=lambda chart: chart.figure_id,
    )


    updated_specification_charts = []

    for parsed_chart in specification.charts:

        current_chart = charts_by_id.get(
            parsed_chart.figure_id
        )

        if current_chart is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Missing chart figure_id="
                    f"{parsed_chart.figure_id}."
                ),
            )

        updated_specification_charts.append(
            parsed_chart.model_copy(
                update={
                    "x": current_chart.x,
                    "y": current_chart.y,
                }
            )
        )

    specification = specification.model_copy(
        update={
            "charts": updated_specification_charts,
        }
    )


    temp_dir = (
        report_dir
        / "charts_temp"
    )

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    try:
        generated_files = (
            generate_multi_table_charts(
                specification=specification,
                tables=tables,
                charts=charts,
                output_dir=temp_dir,
            )
        )

    except ValueError as error:

        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    charts_dir = (
        report_dir
        / "charts"
    )

    if charts_dir.exists():
        shutil.rmtree(charts_dir)

    temp_dir.rename(
        charts_dir
    )



    state["charts"] = [
        chart.model_dump()
        for chart in charts
    ]

    state["specification"] = (
        specification.model_dump()
    )

    save_report_state_data(
        report_id,
        state,
    )


    return {
        "report_id": report_id,

        "charts": [
            chart.model_dump()
            for chart in charts
        ],

        "generated_charts": len(
            generated_files
        ),
    }
    
@router.get("/{report_id}/data")
def get_report_data(report_id: str):

    try:
        state = load_report_state(report_id)
        report_dir = get_report_dir(report_id)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    completed_file = (
        report_dir
        / state["completed_measurements_file"]
    )

    if not completed_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Completed measurements file does not exist.",
        )

    try:
        tables = read_completed_measurement_tables(
            file=str(completed_file),
            metadata=state["measurement_tables"],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    result_tables = []

    for table in tables:

        clean_df = (
            table.dataframe.astype(object)
            .where(
                pd.notna(table.dataframe),
                None,
            )
        )

        result_tables.append(
            {
                "table_id": table.table_id,
                "title": table.title,
                "sheet_name": table.sheet_name,
                "columns": table.dataframe.columns.tolist(),
                "units": table.units,
                "rows": clean_df.to_dict(
                    orient="records",
                ),
            }
        )

    return {
        "report_id": report_id,
        "tables": result_tables,
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
            detail=str(error),
        )


    completed_file = (
        report_dir
        / state["completed_measurements_file"]
    )

    if not completed_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Completed measurements file does not exist.",
        )


    try:
        tables = read_completed_measurement_tables(
            file=str(completed_file),
            metadata=state["measurement_tables"],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    specification = ReportSpecification.model_validate(
        state["specification"]
    )



    try:
        examples = create_multi_table_example_calculations(
            specification=specification,
            tables=tables,
            row_index=request.row_index,
        )

    except (ValueError, IndexError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    state["example_calculations"] = examples
    state["example_row_index"] = request.row_index

    save_report_state_data(
        report_id,
        state,
    )

    return {
        "report_id": report_id,
        "row_index": request.row_index,
        "example_calculations": examples,
    }
    
from io import BytesIO
from uuid import uuid4

from fastapi import (
    UploadFile,
    File,
    Form,
)

from PIL import (
    Image,
    UnidentifiedImageError,
)
    
    
@router.post(
    "/{report_id}/setup-images"
)
async def upload_setup_image(
    report_id: str,
    image: UploadFile = File(...),
    section_ids: str = Form(...),
    caption: str | None = Form(None),
):
    # ========================================================
    # WCZYTANIE RAPORTU
    # ========================================================

    try:
        state = load_report_state(
            report_id
        )

        report_dir = get_report_dir(
            report_id
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    specification = (
        ReportSpecification.model_validate(
            state["specification"]
        )
    )

    # ========================================================
    # SECTION IDS
    #
    # Frontend wysyła np.
    #
    # "1"
    # albo
    # "1,2"
    # albo
    # "1,2,3"
    # ========================================================

    try:
        parsed_section_ids = [
            int(value.strip())
            for value in section_ids.split(",")
            if value.strip()
        ]

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=(
                "section_ids must contain "
                "comma-separated integers."
            ),
        )

    if not parsed_section_ids:
        raise HTTPException(
            status_code=422,
            detail=(
                "At least one section_id "
                "must be provided."
            ),
        )

    valid_section_ids = {
        section.section_id
        for section
        in specification.sections
    }

    unknown_section_ids = (
        set(parsed_section_ids)
        - valid_section_ids
    )

    if unknown_section_ids:
        raise HTTPException(
            status_code=422,
            detail=(
                "Unknown section ids: "
                f"{sorted(unknown_section_ids)}"
            ),
        )

    # ========================================================
    # WCZYTANIE OBRAZU
    # ========================================================

    content = await image.read()

    if not content:
        raise HTTPException(
            status_code=422,
            detail="Uploaded image is empty.",
        )

    # na razie limit 10 MB
    max_size = 10 * 1024 * 1024

    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=(
                "Setup image is too large. "
                "Maximum size is 10 MB."
            ),
        )

    # ========================================================
    # WALIDACJA + KONWERSJA DO PNG
    # ========================================================

    setup_dir = (
        report_dir
        / "setup"
    )

    setup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    unique_id = uuid4().hex

    image_id = (
        f"setup_{unique_id[:12]}"
    )

    filename = (
        f"{image_id}.png"
    )

    output_path = (
        setup_dir
        / filename
    )

    try:
        with Image.open(
            BytesIO(content)
        ) as pil_image:

            pil_image.load()

            # Zachowujemy przezroczystość,
            # jeżeli obraz ją posiada.
            if pil_image.mode not in (
                "RGB",
                "RGBA",
            ):
                pil_image = (
                    pil_image.convert(
                        "RGBA"
                    )
                )

            pil_image.save(
                output_path,
                format="PNG",
            )

    except (
        UnidentifiedImageError,
        OSError,
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Uploaded file is not "
                "a valid image."
            ),
        )

    # ========================================================
    # STATE
    # ========================================================

    setup_images = state.setdefault(
        "setup_images",
        [],
    )

    section_setup_images = (
        state.setdefault(
            "section_setup_images",
            {},
        )
    )

    image_metadata = {
        "image_id": image_id,
        "filename": filename,
        "caption": (
            caption
            or "Schemat układu pomiarowego"
        ),
    }

    setup_images.append(
        image_metadata
    )

    # Ten sam obraz może należeć
    # do kilku sekcji.
    for section_id in parsed_section_ids:
        section_setup_images[
            str(section_id)
        ] = image_id

    overwrite_report_state(
        report_dir=report_dir,
        state=state,
    )

    return {
        "report_id": report_id,
        "image": image_metadata,
        "section_ids": parsed_section_ids,
    }
    
    
from app.schemas.report import (
    ReportSpecification,
    UpdateSetupImageSectionsRequest,
)

@router.patch(
    "/{report_id}/setup-images/{image_id}/sections"
)
def update_setup_image_sections(
    report_id: str,
    image_id: str,
    request: UpdateSetupImageSectionsRequest,
):
    try:
        state = load_report_state(
            report_id
        )

        report_dir = get_report_dir(
            report_id
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    specification = (
        ReportSpecification.model_validate(
            state["specification"]
        )
    )

    # ========================================================
    # CZY OBRAZ ISTNIEJE
    # ========================================================

    setup_images = state.get(
        "setup_images",
        [],
    )

    image_metadata = next(
        (
            image
            for image in setup_images
            if image["image_id"] == image_id
        ),
        None,
    )

    if image_metadata is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Setup image '{image_id}' "
                "does not exist."
            ),
        )

    # ========================================================
    # WALIDACJA SEKCJI
    # ========================================================

    section_ids = list(
        dict.fromkeys(
            request.section_ids
        )
    )

    valid_section_ids = {
        section.section_id
        for section in specification.sections
    }

    unknown_section_ids = (
        set(section_ids)
        - valid_section_ids
    )

    if unknown_section_ids:
        raise HTTPException(
            status_code=422,
            detail=(
                "Unknown section ids: "
                f"{sorted(unknown_section_ids)}"
            ),
        )

    section_setup_images = (
        state.setdefault(
            "section_setup_images",
            {},
        )
    )

    # ========================================================
    # USUWAMY STARE PRZYPISANIA TEGO OBRAZU
    # ========================================================

    for section_id, assigned_image_id in list(
        section_setup_images.items()
    ):
        if assigned_image_id == image_id:
            del section_setup_images[
                section_id
            ]

    # ========================================================
    # DODAJEMY NOWE
    # ========================================================

    for section_id in section_ids:
        section_setup_images[
            str(section_id)
        ] = image_id

    overwrite_report_state(
        report_dir=report_dir,
        state=state,
    )

    return {
        "report_id": report_id,
        "image_id": image_id,
        "section_ids": section_ids,
    }
    
    
@router.delete(
    "/{report_id}/setup-images/{image_id}"
)
def delete_setup_image(
    report_id: str,
    image_id: str,
):
    try:
        state = load_report_state(
            report_id
        )

        report_dir = get_report_dir(
            report_id
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    setup_images = state.get(
        "setup_images",
        [],
    )

    image_metadata = next(
        (
            image
            for image in setup_images
            if image["image_id"] == image_id
        ),
        None,
    )

    if image_metadata is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Setup image '{image_id}' "
                "does not exist."
            ),
        )

    # ========================================================
    # USUNIĘCIE PLIKU
    # ========================================================

    image_path = (
        report_dir
        / "setup"
        / image_metadata["filename"]
    )

    if image_path.exists():
        image_path.unlink()

    # ========================================================
    # USUNIĘCIE METADANYCH
    # ========================================================

    state["setup_images"] = [
        image
        for image in setup_images
        if image["image_id"] != image_id
    ]

    # ========================================================
    # USUNIĘCIE PRZYPISAŃ DO SEKCJI
    # ========================================================

    section_setup_images = state.get(
        "section_setup_images",
        {},
    )

    for section_id, assigned_image_id in list(
        section_setup_images.items()
    ):
        if assigned_image_id == image_id:
            del section_setup_images[
                section_id
            ]

    overwrite_report_state(
        report_dir=report_dir,
        state=state,
    )

    return {
        "report_id": report_id,
        "deleted_image_id": image_id,
    }
    
@router.put(
    "/{report_id}/setup-images/{image_id}"
)
async def replace_setup_image(
    report_id: str,
    image_id: str,
    image: UploadFile = File(...),
    caption: str | None = Form(None),
):
    try:
        state = load_report_state(
            report_id
        )

        report_dir = get_report_dir(
            report_id
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    setup_images = state.get(
        "setup_images",
        [],
    )

    image_metadata = next(
        (
            item
            for item in setup_images
            if item["image_id"] == image_id
        ),
        None,
    )

    if image_metadata is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Setup image '{image_id}' "
                "does not exist."
            ),
        )

    content = await image.read()

    if not content:
        raise HTTPException(
            status_code=422,
            detail="Uploaded image is empty.",
        )

    max_size = 10 * 1024 * 1024

    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=(
                "Setup image is too large. "
                "Maximum size is 10 MB."
            ),
        )

    output_path = (
        report_dir
        / "setup"
        / image_metadata["filename"]
    )

    try:
        with Image.open(
            BytesIO(content)
        ) as pil_image:

            pil_image.load()

            if pil_image.mode not in (
                "RGB",
                "RGBA",
            ):
                pil_image = (
                    pil_image.convert(
                        "RGBA"
                    )
                )

            pil_image.save(
                output_path,
                format="PNG",
            )

    except (
        UnidentifiedImageError,
        OSError,
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Uploaded file is not "
                "a valid image."
            ),
        )

    if caption is not None:
        image_metadata["caption"] = caption

    overwrite_report_state(
        report_dir=report_dir,
        state=state,
    )

    return {
        "report_id": report_id,
        "image": image_metadata,
    }