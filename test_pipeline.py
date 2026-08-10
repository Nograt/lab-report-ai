from app.services.instruction_parser import parse_report_instruction
from app.services.excel_reader import read_meansurements
from app.services.chart_generator import (
    create_chart_specifications,
    generate_chart,
)


instruction = """
Na podstawie pomiarów z punktu 3
wykonać na wspolnym wykresie charakterystyki
Uk(I), P(I) oraz cosφK(I).
"""

ai_specification = parse_report_instruction(instruction)

print("\n=== AI SPECIFICATION ===")
print(ai_specification.model_dump())

charts = create_chart_specifications(ai_specification)

print("\n=== CHART SPECIFICATIONS ===")

for chart in charts:
    print(chart)
    
df, units = read_meansurements("test.xlsx")

print("\n=== DATAFRAME ===")
print(df)

print("\n=== UNITS ===")
print(units)    


generate_chart(
    df=df,
    units=units,
    charts=charts,
)

