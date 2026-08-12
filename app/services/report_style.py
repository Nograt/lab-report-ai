from dataclasses import dataclass

from docx.shared import Cm, Pt


@dataclass(frozen=True)
class ReportStyle:

    # ========================================================
    # PAGE
    # ========================================================

    margin_top: Cm = Cm(2.5)
    margin_bottom: Cm = Cm(2.5)
    margin_left: Cm = Cm(2.5)
    margin_right: Cm = Cm(2.5)

    # ========================================================
    # BODY
    # ========================================================

    body_font: str = "Times New Roman"
    body_size: Pt = Pt(12)

    line_spacing: float = 1.15

    paragraph_space_before: Pt = Pt(0)
    paragraph_space_after: Pt = Pt(6)

    # NA RAZIE ZERO.
    # Nie narzucamy wszystkim akapitom wcięcia.
    first_line_indent: Cm = Cm(0)

    # ========================================================
    # HEADINGS
    # ========================================================

    heading_1_size: Pt = Pt(14)
    heading_2_size: Pt = Pt(12)

    # ========================================================
    # TABLES
    # ========================================================

    table_font_size: Pt = Pt(9)
    table_header_font_size: Pt = Pt(9)
    table_caption_size: Pt = Pt(10)

    # ========================================================
    # FIGURES
    # ========================================================

    chart_width: Cm = Cm(14.5)
    figure_caption_size: Pt = Pt(10)

    # ========================================================
    # EQUATIONS
    # ========================================================

    equation_label_size: Pt = Pt(11)


DEFAULT_REPORT_STYLE = ReportStyle()