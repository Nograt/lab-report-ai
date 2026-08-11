from app.services.excel_reader import (
    read_meansurements,
)

from app.services.instruction_parser import (
    parse_report_instruction,
)

from app.services.example_calculations import (
    create_example_calculations,
)


instruction = """
Obliczyć współczynnik mocy:

cosφK = PK / (Uk * I)

oraz moc:

PK = P - Pap

Następnie wykonać wykresy:
PK(I)
cosφK(I)
"""


specification = parse_report_instruction(
    instruction
)


df, units = read_meansurements(
    "storage/reports/e6cca490-e6b5-4264-baed-5121e8a041bd/completed_measurements.xlsx"
)


examples = create_example_calculations(
    df=df,
    calculations=specification.calculations,
    units=units,
    row_index=0,
)


for example in examples:
    print()
    print(example["formula_latex"])
    print(example["substitution_latex"])
    print(example["result_latex"])
    
    
