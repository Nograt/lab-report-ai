import json
import shutil

from io import BytesIO
from typing import Annotated
from uuid import uuid4

import pandas as pd

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse

from PIL import (
    Image,
    UnidentifiedImageError,
)

from app.schemas.chart import (
    ChartSpecification,
    UpdateChartsRequest,
)
from app.schemas.instruction_parameters import (
    InstructionParameterValue,
)
from app.schemas.report import (
    ReportSpecification,
    UpdateExampleRowRequest,
    UpdateSetupImageSectionsRequest,
)
from app.schemas.report_metadata import (
    ProfileSnapshot,
    ReportMetadata,
    SubjectSnapshot,
)

from app.services.calculation_engine import (
    execute_table_calculations,
)
from app.services.chart_generator import (
    create_multi_table_chart_specifications,
    generate_multi_table_charts,
    match_column_name,
)
from app.services.docx_generator import (
    generate_report_docx,
)
from app.services.example_calculations import (
    create_multi_table_example_calculations,
)
from app.services.excel_reader import (
    create_measurement_table_infos,
    get_measurement_table,
    read_completed_measurement_tables,
    read_measurement_tables,
)
from app.services.instruction_parameter_resolver import (
    apply_instruction_parameters,
)
from app.services.instruction_parser import (
    parse_report_instruction_with_repair,
)
from app.services.instruction_preparer import (
    prepare_instruction,
)
from app.services.openai_file_service import (
    delete_openai_file,
    upload_instruction_pdf,
)
from app.services.profile_storage import (
    load_user_profile,
)
from app.services.report_text_generator import (
    generate_report_text,
)
from app.services.result_analyzer import (
    analyze_report_sections,
)
from app.services.storage import (
    create_report_workspace,
    get_report_dir,
    load_report_state,
    overwrite_report_state,
    save_completed_measurement_tables,
    save_measurements,
    save_report_state,
    save_report_state_data,
)
from app.services.subject_storage import (
    get_subject,
)

from app.schemas.report_text import (
    ReportTextContent,
    UpdateReportTextRequest,
)

router = APIRouter(prefix="/reports", tags=["reports"])
@router.post("/resolve-instruction")
async def resolve_instruction(
    instruction: Annotated[
        str,
        Form(),
    ],
    parameters: Annotated[
        str,
        Form(),
    ],
):
    try:
        raw_parameters = json.loads(
            parameters
        )

        parameter_values = [
            InstructionParameterValue.model_validate(
                item
            )
            for item in raw_parameters
        ]

    except (
        json.JSONDecodeError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid parameters: {error}"
            ),
        )

    resolved_instruction = (
        apply_instruction_parameters(
            instruction=instruction,
            parameters=parameter_values,
        )
    )

    return {
        "instruction": resolved_instruction,
    }

@router.post("/prepare-instruction")
async def prepare_report_instruction(
    instruction_file: Annotated[
        UploadFile,
        File(),
    ],
    measurements: Annotated[
        UploadFile,
        File(),
    ],
):

    instruction_file_id = None

    try:

        try:
            measurement_tables = (
                read_measurement_tables(
                    measurements.file
                )
            )

        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            )

        table_infos = (
            create_measurement_table_infos(
                measurement_tables
            )
        )


        try:
            instruction_file_id = (
                upload_instruction_pdf(
                    instruction_file
                )
            )

        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            )

        try:
            preparation = prepare_instruction(
                instruction_file_id=instruction_file_id,
                measurement_tables=table_infos,
            )

        except ValueError as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            )

        return preparation.model_dump()

    finally:

        if instruction_file_id is not None:
            delete_openai_file(
                instruction_file_id
            )

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
    parameters: Annotated[str | None,Form(),] = None,
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
        
    resolved_instruction = instruction
    
    if parameters:

        try:
            raw_parameters = json.loads(
                parameters
            )

            parameter_values = [
                InstructionParameterValue.model_validate(
                    item
                )
                for item in raw_parameters
            ]

        except (
            json.JSONDecodeError,
            ValueError,
        ) as error:

            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid parameters: {error}"
                ),
            )

        resolved_instruction = (
            apply_instruction_parameters(
                instruction=resolved_instruction,
                parameters=parameter_values,
            )
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
        instruction=resolved_instruction,
        measurement_tables=table_infos,
    )

    except ValueError as error:
        raise HTTPException(
        status_code=422,
        detail=str(error),
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
            instruction=resolved_instruction,
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

    valid_figure_ids = {
        figure_id
        for section in specification.sections
        for figure_id in section.chart_figure_ids
    }

    if len(request.charts) != len(specification.charts):
        raise HTTPException(
            status_code=422,
            detail=(
                "The number of chart series cannot be changed. "
                f"Expected {len(specification.charts)}, "
                f"received {len(request.charts)}."
            ),
        )

    normalized_charts: list[ChartSpecification] = []

    try:
        for index, chart in enumerate(request.charts):
            original_chart = specification.charts[index]

            if chart.figure_id != original_chart.figure_id:
                raise ValueError(
                    "Chart series order or figure_id changed "
                    f"at index {index}."
                )

            if chart.table_id != original_chart.table_id:
                raise ValueError(
                    "Chart series table_id changed "
                    f"at index {index}."
                )

            if chart.figure_id not in valid_figure_ids:
                raise ValueError(
                    f"Unknown figure_id={chart.figure_id}."
                )

            table = get_measurement_table(
                tables=tables,
                table_id=chart.table_id,
            )

            x = match_column_name(
                chart.x,
                table.dataframe,
            )

            y = match_column_name(
                chart.y,
                table.dataframe,
            )

            normalized_charts.append(
                chart.model_copy(
                    update={
                        "x": x,
                        "y": y,
                    }
                )
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


    charts_by_figure: dict[
        int,
        list[ChartSpecification],
    ] = {}

    for chart in normalized_charts:
        charts_by_figure.setdefault(
            chart.figure_id,
            [],
        ).append(chart)

    for figure_id, figure_charts in charts_by_figure.items():
        shared_x = figure_charts[0].x

        if any(
            chart.x != shared_x
            for chart in figure_charts
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Figure {figure_id} requires "
                    "the same x-axis for all series."
                ),
            )


    updated_specification_charts = []

    for original_chart, current_chart in zip(
        specification.charts,
        normalized_charts,
    ):
        updated_specification_charts.append(
            original_chart.model_copy(
                update={
                    "x": current_chart.x,
                    "y": current_chart.y,
                    "filter_column": (
                        current_chart.filter_column
                    ),
                    "filter_value": (
                        current_chart.filter_value
                    ),
                    "label": current_chart.label,
                }
            )
        )

    specification = specification.model_copy(
        update={
            "charts": updated_specification_charts,
        }
    )

    temp_dir = report_dir / "charts_temp"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    try:
        generated_files = generate_multi_table_charts(
            specification=specification,
            tables=tables,
            charts=normalized_charts,
            output_dir=temp_dir,
        )

    except ValueError as error:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    charts_dir = report_dir / "charts"

    if charts_dir.exists():
        shutil.rmtree(charts_dir)

    temp_dir.rename(charts_dir)

    state["charts"] = [
        chart.model_dump()
        for chart in normalized_charts
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
            for chart in normalized_charts
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
      
    
@router.post(
    "/{report_id}/setup-images"
)
async def upload_setup_image(
    report_id: str,
    image: UploadFile = File(...),
    section_ids: str = Form(...),
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

    specification = (
        ReportSpecification.model_validate(
            state["specification"]
        )
    )


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


    for section_id, assigned_image_id in list(
        section_setup_images.items()
    ):
        if assigned_image_id == image_id:
            del section_setup_images[
                section_id
            ]

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

    image_path = (
        report_dir
        / "setup"
        / image_metadata["filename"]
    )

    if image_path.exists():
        image_path.unlink()

    state["setup_images"] = [
        image
        for image in setup_images
        if image["image_id"] != image_id
    ]

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
    
    
@router.get("/{report_id}/charts/{figure_id}/image")
def get_report_chart_image(
    report_id: str,
    figure_id: int,
):
    try:
        state = load_report_state(report_id)
        report_dir = get_report_dir(report_id)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    valid_figure_ids = {
        chart["figure_id"]
        for chart in state.get("charts", [])
    }

    if figure_id not in valid_figure_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Figure {figure_id} "
                "does not exist in this report."
            ),
        )

    image_path = (
        report_dir
        / "charts"
        / f"figure_{figure_id}.png"
    )

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Image for figure {figure_id} "
                "does not exist."
            ),
        )

    return FileResponse(
        path=image_path,
        media_type="image/png",
        filename=f"figure_{figure_id}.png",
    )
    
@router.patch("/{report_id}/text")
def update_report_text(
    report_id: str,
    request: UpdateReportTextRequest,
):
    try:
        state = load_report_state(report_id)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    specification = ReportSpecification.model_validate(
        state["specification"]
    )

    expected_section_ids = [
        section.section_id
        for section in specification.sections
    ]

    request_section_ids = [
        section.section_id
        for section in request.sections
    ]

    if request_section_ids != expected_section_ids:
        raise HTTPException(
            status_code=422,
            detail=(
                "Report text sections do not match "
                "report specification."
            ),
        )

    report_text = ReportTextContent(
        purpose=request.purpose,
        setup_description=request.setup_description,
        theory=request.theory,
        sections=request.sections,
        conclusions=request.conclusions,
    )

    state["report_text"] = report_text.model_dump()

    save_report_state_data(
        report_id,
        state,
    )

    return {
        "report_id": report_id,
        "report_text": report_text.model_dump(),
    }