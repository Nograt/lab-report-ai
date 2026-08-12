from app.services.excel_reader import read_meansurements
from app.services.result_analyzer import analyze_section
from app.services.report_text_generator import generate_report_text

from app.schemas.report import ReportSpecification
from app.schemas.section import ReportSection
from app.schemas.chart import ChartSpecification


# ============================================================
# 1. Gotowe dane po obliczeniach
# ============================================================

df, _ = read_meansurements(
    "storage/reports/4c363147-d7c4-4872-8938-e86984d26411/"
    "completed_measurements.xlsx"
)


units = {
    "Lp": None,
    "Uk": "V",
    "I": "A",
    "P": "W",
    "Pap": "W",
    "PK": "W",
    "cosφK": None,
    "Tl": "Nm",
}


# ============================================================
# 2. Sekcja raportu
# ============================================================

section = ReportSection.model_validate(
    {
        "section_id": 1,
        "table_id": 1,
        "title": "Pomiary charakterystyk w stanie zwarcia",

        "table": {
            "title": "Wyniki pomiarów charakterystyk w stanie zwarcia",
            "columns": [
                "Lp",
                "Uk",
                "I",
                "P",
                "Pap",
                "PK",
                "cosφK",
                "Tl",
            ],
        },

        "calculation_outputs": [
            "PK",
            "cosφK",
        ],

        "chart_figure_ids": [
            1,
            2,
        ],

        "include_description": True,
        "include_analysis": True,
    }
)


# ============================================================
# 3. Wykresy należące do sekcji
# ============================================================

charts = [
    ChartSpecification(
        figure_id=1,
        x="I",
        y="PK",
    ),

    ChartSpecification(
        figure_id=2,
        x="I",
        y="cosφK",
    ),
]


# ============================================================
# 4. Deterministyczna analiza danych przez Python
# ============================================================

analysis = analyze_section(
    df=df,
    section=section,
    units=units,
    charts=charts,
)


# ============================================================
# 5. Instrukcja laboratoryjna
# ============================================================

instruction = """
Temat ćwiczenia: Badanie silnika uniwersalnego.

Pomiary charakterystyk w stanie zwarcia.

W trakcie pomiaru zmieniano wartość prądu silnika.
Mierzono napięcie zwarcia Uk, prąd I, moc P oraz moment Tl.

Tabela wyników powinna zawierać:
Lp, Uk, I, P, Pap, PK, cosφK, Tl.

Obliczyć współczynnik mocy:

cosφK = PK / (Uk * I)

oraz moc:

PK = P - Pap

Następnie wykonać dwa osobne wykresy:

1. PK(I)
2. cosφK(I)

W tej części sprawozdania należy krótko opisać wykonane pomiary
oraz przeanalizować otrzymane wyniki i wykresy.

Sprawozdanie powinno zawierać:
- cel ćwiczenia,
- opis badanego obwodu / stanowiska,
- opracowanie wyników,
- wnioski.
"""


# ============================================================
# 6. Specyfikacja całego raportu
# ============================================================

specification = ReportSpecification.model_validate(
    {
        "report_title": "Badanie silnika uniwersalnego",
        "source_section": None,

        "include_purpose": True,
        "include_theory": False,
        "include_setup": True,
        "include_conclusions": True,

        # W tym teście interesuje nas warstwa tekstowa,
        # dlatego nie musimy ponownie budować pełnych
        # CalculationSpecification i ParsedChartSpecification.
        "calculations": [],
        "charts": [],

        "sections": [
            section.model_dump()
        ],
    }
)


# ============================================================
# 7. Generowanie całej treści raportu przez LLM
# ============================================================

report_text = generate_report_text(
    specification=specification,
    analyses=[
        analysis
    ],
    instruction=instruction,
)


# ============================================================
# 8. Wyniki
# ============================================================

print("\n=== ANALIZA PYTHONA ===\n")

print(
    analysis.model_dump_json(
        indent=2
    )
)


print("\n=== TEKST CAŁEGO SPRAWOZDANIA ===\n")

print(
    report_text.model_dump_json(
        indent=2
    )
)