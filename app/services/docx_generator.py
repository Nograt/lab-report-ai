from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from app.schemas.report import ReportSpecification
from app.services.excel_reader import (
    MeasurementTableData,
    get_measurement_table,
)

from app.services.word_equation import (
    append_formula_equation,
    append_substitution_equation,
    append_result_equation,
)

from app.services.report_style import (
    ReportStyle,
    DEFAULT_REPORT_STYLE,
)


def configure_document(
    document: Document,
    style: ReportStyle,
):
    section = document.sections[0]

    section.top_margin = style.margin_top
    section.bottom_margin = style.margin_bottom
    section.left_margin = style.margin_left
    section.right_margin = style.margin_right

    # ========================================================
    # NORMAL
    # ========================================================

    normal = document.styles["Normal"]

    normal.font.name = style.body_font
    normal.font.size = style.body_size

    normal.paragraph_format.line_spacing = (
        style.line_spacing
    )

    normal.paragraph_format.space_before = (
        style.paragraph_space_before
    )

    normal.paragraph_format.space_after = (
        style.paragraph_space_after
    )

    normal.paragraph_format.first_line_indent = None

    # ========================================================
    # HEADING 1
    # ========================================================

    heading_1 = document.styles["Heading 1"]

    heading_1.font.name = style.body_font
    heading_1.font.size = style.heading_1_size
    heading_1.font.bold = True
    heading_1.font.color.rgb = None

    heading_1.paragraph_format.left_indent = Cm(0)
    heading_1.paragraph_format.first_line_indent = Cm(0)

    heading_1.paragraph_format.space_before = Pt(12)
    heading_1.paragraph_format.space_after = Pt(6)

    heading_1.paragraph_format.keep_with_next = True

    # ========================================================
    # HEADING 2
    # ========================================================

    heading_2 = document.styles["Heading 2"]

    heading_2.font.name = style.body_font
    heading_2.font.size = style.heading_2_size
    heading_2.font.bold = True
    heading_2.font.color.rgb = None

    heading_2.paragraph_format.left_indent = Cm(0)
    heading_2.paragraph_format.first_line_indent = Cm(0)

    heading_2.paragraph_format.space_before = Pt(10)
    heading_2.paragraph_format.space_after = Pt(4)

    heading_2.paragraph_format.keep_with_next = True

def set_cell_text(
    cell,
    value,
    bold: bool = False,
    font_size: float = 9,
):
    cell.text = ""

    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = paragraph.add_run(
        "" if value is None else str(value)
    )

    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(font_size)

    run._element.get_or_add_rPr().rFonts.set(
        qn("w:ascii"),
        "Times New Roman",
    )

    run._element.get_or_add_rPr().rFonts.set(
        qn("w:hAnsi"),
        "Times New Roman",
    )

    cell.vertical_alignment = (
        WD_CELL_VERTICAL_ALIGNMENT.CENTER
    )


def format_number(value):
    if value is None:
        return ""

    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")

    return str(value)


def add_table_borders(table):
    tbl = table._tbl
    tbl_pr = tbl.tblPr

    borders = tbl_pr.first_child_found_in(
        "w:tblBorders"
    )

    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)

    for edge in (
        "top",
        "left",
        "bottom",
        "right",
        "insideH",
        "insideV",
    ):
        tag = f"w:{edge}"

        element = borders.find(
            qn(tag)
        )

        if element is None:
            element = OxmlElement(tag)
            borders.append(element)

        element.set(
            qn("w:val"),
            "single",
        )

        element.set(
            qn("w:sz"),
            "4",
        )

        element.set(
            qn("w:space"),
            "0",
        )

        element.set(
            qn("w:color"),
            "000000",
        )


def add_measurement_table(
    document: Document,
    table_data: MeasurementTableData,
    columns: list[str],
    table_number: int,
    title: str | None,
):
    caption = document.add_paragraph()

    caption.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    run = caption.add_run(
        f"Tabela {table_number}. "
        f"{title or table_data.title or ''}"
    )

    run.italic = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(10)

    df = table_data.dataframe[
        columns
    ]

    table = document.add_table(
        rows=2,
        cols=len(columns),
    )

    table.alignment = (
        WD_TABLE_ALIGNMENT.CENTER
    )

    table.style = "Table Grid"

    # --------------------------------------------------------
    # Nagłówki
    # --------------------------------------------------------

    for index, column in enumerate(columns):

        set_cell_text(
            table.rows[0].cells[index],
            column,
            bold=True,
        )

        unit = table_data.units.get(
            column
        )

        set_cell_text(
            table.rows[1].cells[index],
            unit or "—",
            bold=False,
        )

    for _, row in df.iterrows():

        cells = table.add_row().cells

        for index, column in enumerate(columns):

            set_cell_text(
                cells[index],
                format_number(
                    row[column]
                ),
            )

    add_table_borders(table)

    document.add_paragraph()


def add_chart(
    document: Document,
    chart_path: Path,
    figure_id: int,
    x: str,
    y: str,
):
    paragraph = document.add_paragraph()

    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    run = paragraph.add_run()

    run.add_picture(
        str(chart_path),
        width=Cm(15),
    )

    caption = document.add_paragraph()

    caption.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    caption_run = caption.add_run(
        f"Rys. {figure_id}. "
        f"Zależność {y} = f({x})"
    )

    caption_run.italic = True
    caption_run.font.name = "Times New Roman"
    caption_run.font.size = Pt(10)


def add_example_calculations(
    document: Document,
    calculations: list[dict],
):
    if not calculations:
        return

    heading = document.add_paragraph()

    run = heading.add_run(
        "Przykładowe obliczenia"
    )

    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)

    for calculation in calculations:

        expression = calculation.get(
            "expression"
        )

        variables = calculation.get(
            "variables",
            {},
        )


        if expression is not None:


            formula_paragraph = (
                document.add_paragraph()
            )

            formula_paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER
            )

            append_formula_equation(
                paragraph=formula_paragraph,
                output=calculation["output"],
                expression=expression,
            )


            substitution_paragraph = (
                document.add_paragraph()
            )

            substitution_paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER
            )

            append_substitution_equation(
                paragraph=substitution_paragraph,
                output=calculation["output"],
                expression=expression,
                variables=variables,
            )

            result_paragraph = (
                document.add_paragraph()
            )

            result_paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER
            )

            append_result_equation(
                paragraph=result_paragraph,
                output=calculation["output"],
                result=calculation["result"],
                unit=calculation.get("unit"),
            )

            continue


        for key in (
            "formula_latex",
            "substitution_latex",
            "result_latex",
        ):

            value = calculation.get(key)

            if not value:
                continue

            value = (
                value
                .replace(
                    "\\cdot",
                    "·",
                )
                .replace(
                    "\\times",
                    "×",
                )
            )

            paragraph = (
                document.add_paragraph()
            )

            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER
            )

            run = paragraph.add_run(
                value
            )

            run.font.name = (
                "Times New Roman"
            )

            run.font.size = Pt(11)



from app.services.title_page import (
    TitlePageData,
    add_title_page,
)

def generate_report_docx(
    report_dir: Path,
    state: dict,
    tables: list[MeasurementTableData],
    style: ReportStyle = DEFAULT_REPORT_STYLE,
) -> Path:

    specification = (
        ReportSpecification.model_validate(
            state["specification"]
        )
    )

    report_text = state[
        "report_text"
    ]

    document = Document()

    configure_document(
        document=document,
        style=style,
    )

    # ========================================================
    # TABELA TYTUŁOWA / NAGŁÓWEK PIERWSZEJ STRONY
    # ========================================================

    title_page_data = TitlePageData(
        faculty=(
            "WYDZIAŁ ELEKTROTECHNIKI I "
            "INFORMATYKI PL"
        ),
        department=(
            "Katedra Napędów i Maszyn "
            "Elektrycznych"
        ),
        laboratory=(
            "Laboratorium elektromaszynowych "
            "układów wykonawczych"
        ),
        members=[
            "Wojciech Targoński",
            "Jan Walczyński",
            "Marcin Piela",
            "Miłosz Pietrak",
        ],
        semester="4",
        group="IZI 4.2/3",
        team="1",
        academic_year="2025/2026",
        topic=specification.report_title,
        execution_date="26.05.2026",
        grade="",
    )

    add_title_page(
        document=document,
        data=title_page_data,
    )

    # UWAGA:
    # Nie robimy document.add_page_break().
    #
    # We wzorcowym sprawozdaniu pierwsza sekcja
    # zaczyna się na tej samej stronie pod tabelą.

    spacer = document.add_paragraph()

    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(10)

    # ========================================================
    # 1. CEL ĆWICZENIA
    # ========================================================

    document.add_heading(
        "1. Cel ćwiczenia",
        level=1,
    )

    document.add_paragraph(
        report_text["purpose"]
    )

    # ========================================================
    # 2. BADANY OBWÓD / STANOWISKO
    # ========================================================

    document.add_heading(
        "2. Badany obwód i stanowisko pomiarowe",
        level=1,
    )

    document.add_paragraph(
        report_text["setup_description"]
    )

    # ========================================================
    # TEORIA
    # ========================================================

    theory = report_text.get(
        "theory"
    )

    if theory:
        document.add_heading(
            "3. Podstawy teoretyczne",
            level=1,
        )

        document.add_paragraph(
            theory
        )

        results_number = 4
        conclusions_number = 5

    else:
        results_number = 3
        conclusions_number = 4

    # ========================================================
    # OPRACOWANIE WYNIKÓW
    # ========================================================

    document.add_heading(
        f"{results_number}. Opracowanie wyników",
        level=1,
    )

    text_by_section_id = {
        section["section_id"]: section
        for section in report_text["sections"]
    }

    examples_by_section_id = {
        item["section_id"]: item
        for item in state.get(
            "example_calculations",
            [],
        )
    }

    charts_by_figure_id = {
        chart["figure_id"]: chart
        for chart in state.get(
            "charts",
            [],
        )
    }

    table_number = 1

    # ========================================================
    # SEKCJE OPRACOWANIA WYNIKÓW
    # ========================================================

    for section_index, section in enumerate(
        specification.sections,
        start=1,
    ):

        document.add_heading(
            (
                f"{results_number}.{section_index}. "
                f"{section.title}"
            ),
            level=2,
        )

        section_text = (
            text_by_section_id.get(
                section.section_id,
                {},
            )
        )

        # ----------------------------------------------------
        # OPIS
        # ----------------------------------------------------

        if (
            section.include_description
            and section_text.get("description")
        ):
            document.add_paragraph(
                section_text["description"]
            )

        # ----------------------------------------------------
        # TABELA
        # ----------------------------------------------------

        if section.table is not None:

            table_data = get_measurement_table(
                tables=tables,
                table_id=section.table_id,
            )

            add_measurement_table(
                document=document,
                table_data=table_data,
                columns=section.table.columns,
                table_number=table_number,
                title=section.table.title,
            )

            table_number += 1

        # ----------------------------------------------------
        # PRZYKŁADOWE OBLICZENIA
        # ----------------------------------------------------

        section_examples = (
            examples_by_section_id.get(
                section.section_id
            )
        )

        if section_examples:

            add_example_calculations(
                document=document,
                calculations=section_examples[
                    "calculations"
                ],
            )

        # ----------------------------------------------------
        # WYKRESY
        # ----------------------------------------------------

        for figure_id in section.chart_figure_ids:

            chart = charts_by_figure_id.get(
                figure_id
            )

            if chart is None:
                continue

            chart_path = (
                report_dir
                / "charts"
                / f"figure_{figure_id}.png"
            )

            if not chart_path.exists():
                continue

            add_chart(
                document=document,
                chart_path=chart_path,
                figure_id=figure_id,
                x=chart["x"],
                y=chart["y"],
            )

        # ----------------------------------------------------
        # ANALIZA
        # ----------------------------------------------------

        if (
            section.include_analysis
            and section_text.get("analysis")
        ):
            analysis_heading = (
                document.add_paragraph()
            )

            analysis_heading.paragraph_format.space_before = Pt(6)
            analysis_heading.paragraph_format.space_after = Pt(3)

            run = analysis_heading.add_run(
                "Analiza wyników"
            )

            run.bold = True
            run.font.name = style.body_font
            run.font.size = Pt(11)

            document.add_paragraph(
                section_text["analysis"]
            )

    # ========================================================
    # WNIOSKI
    # ========================================================

    document.add_heading(
        f"{conclusions_number}. Wnioski",
        level=1,
    )

    document.add_paragraph(
        report_text["conclusions"]
    )

    # ========================================================
    # ZAPIS
    # ========================================================

    output_path = (
        report_dir
        / "report.docx"
    )

    document.save(
        output_path
    )

    return output_path