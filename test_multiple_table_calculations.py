from app.services.excel_reader import (
    read_measurement_tables,
    create_measurement_table_infos,
    get_measurement_table,
)

from app.services.instruction_parser import (
    parse_report_instruction,
)

from app.services.calculation_engine import (
    execute_calculations,
)


# ============================================================
# 1. Excel
# ============================================================

measurement_tables = read_measurement_tables(
    "test_multiple.xlsx"
)

table_infos = create_measurement_table_infos(
    measurement_tables
)


# ============================================================
# 2. Instrukcja
# ============================================================

instruction = """
Temat ćwiczenia: Badanie silnika indukcyjnego.

1. Próba biegu jałowego.

Przedstawić tabelę:
U₀, I₀, P₀, n₀, s₀, cosφ₀.

Obliczyć:
X0 = U₀ * I₀

Wykonać wykresy:
I₀(U₀)
P₀(U₀)
cosφ₀(U₀)


2. Charakterystyka momentu.

Przedstawić tabelę:
Uₖ, Iₖ, Pₖ, cosφₖ, Fₗ, Tₗ.

Obliczyć:
Xk = Uₖ * Iₖ

Wykonać wykresy:
Tₗ(Iₖ)
cosφₖ(Iₖ)


3. Próba obciążenia.

Przedstawić tabelę:
I, Pin, cosφ, Ia, Ui, Pi, POH, P, n, s, η, Ts.

Wykonać wykresy:
n(Ts)
I(Ts)
η(Ts)
cosφ(Ts)

Każdą część należy opisać i przeanalizować.
Na końcu przedstawić wnioski.
"""


# ============================================================
# 3. Parser AI
# ============================================================

specification = parse_report_instruction(
    instruction=instruction,
    measurement_tables=table_infos,
)


# ============================================================
# 4. Obliczenia osobno dla każdego arkusza
# ============================================================

from app.services.calculation_engine import (
    execute_table_calculations,
)

completed_tables = execute_table_calculations(
    tables=measurement_tables,
    calculations=specification.calculations,
)


for table in completed_tables:

    print("\n====================================")
    print(f"TABLE ID: {table.table_id}")
    print(f"SHEET: {table.sheet_name}")
    print("====================================")

    print(
        "COLUMNS:",
        table.dataframe.columns.tolist(),
    )

    print(
        "UNITS:",
        table.units,
    )

    print("\nDATA:")
    print(
        table.dataframe.head()
    )
    
from app.services.chart_generator import (
    create_multi_table_chart_specifications,
)


charts = create_multi_table_chart_specifications(
    specification=specification,
    tables=completed_tables,
)


print("\n=== CHART ROUTING ===\n")


for section in specification.sections:

    table = get_measurement_table(
        tables=completed_tables,
        table_id=section.table_id,
    )

    section_charts = [
        chart
        for chart in charts
        if chart.figure_id
        in section.chart_figure_ids
    ]

    print(
        f"\nSECTION {section.section_id}: "
        f"{section.title}"
    )

    print(
        f"TABLE {table.table_id}: "
        f"{table.sheet_name}"
    )

    for chart in section_charts:
        print(
            f"FIGURE {chart.figure_id}: "
            f"{chart.y}({chart.x})"
        )
        
from pathlib import Path

from app.services.chart_generator import (
    create_multi_table_chart_specifications,
    generate_multi_table_charts,
    
)


output_dir = Path(
    "test_output/multi_table_charts"
)


generated_files = generate_multi_table_charts(
    specification=specification,
    tables=completed_tables,
    charts=charts,
    output_dir=output_dir,
)


print("\n=== GENERATED CHARTS ===\n")

for file in generated_files:
    print(file)


print(
    f"\nGenerated charts: "
    f"{len(generated_files)}"
)

from app.services.result_analyzer import (
    analyze_report_sections,
)

section_analyses = analyze_report_sections(
    specification=specification,
    tables=completed_tables,
    charts=charts,
)


print("\n=== SECTION ANALYSES ===\n")

for analysis in section_analyses:

    section = next(
        section
        for section in specification.sections
        if section.section_id == analysis.section_id
    )

    table = get_measurement_table(
        tables=completed_tables,
        table_id=section.table_id,
    )

    print("\n====================================")
    print(
        f"SECTION {section.section_id}: "
        f"{section.title}"
    )
    print(
        f"TABLE {table.table_id}: "
        f"{table.sheet_name}"
    )
    print("====================================")

    print(
        analysis.model_dump_json(
            indent=2,
        )
    )
    
from app.services.example_calculations import (
    create_multi_table_example_calculations,
)

example_calculations = create_multi_table_example_calculations(
    specification=specification,
    tables=completed_tables,
    row_index=0,
)


print("\n=== EXAMPLE CALCULATIONS ===\n")


for section_examples in example_calculations:

    print(
        f"\nSECTION {section_examples['section_id']} "
        f"/ TABLE {section_examples['table_id']}"
    )

    for calculation in section_examples["calculations"]:

        print(
            calculation
        )