from pathlib import Path

from app.services.instruction_parser import parse_report_instruction
from app.services.excel_reader import read_meansurements
from app.services.chart_generator import (
    create_chart_specifications,
    generate_chart,
)


instruction = """
Na podstawie pomiarów wykonać na osobnych wykresach
charakterystyki Uk(I), P(I) oraz cosφK(I).
"""


# 1. Parser AI
ai_specification = parse_report_instruction(
    instruction
)


# 2. Excel
df, units = read_meansurements(
    "test.xlsx"
)


# 3. ChartSpecification
charts = create_chart_specifications(
    ai_specification,
    df
)


# 4. Generowanie PNG
generated_files = generate_chart(
    df=df,
    units=units,
    charts=charts,
    output_dir=Path("storage/test/charts")
)


print("Generated files:")

for file in generated_files:
    print(file)