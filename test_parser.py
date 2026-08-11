from app.services.excel_reader import read_meansurements
from app.services.instruction_parser import parse_report_instruction


df, units = read_meansurements(
    "test.xlsx"
)


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

Sprawozdanie powinno zawierać cel ćwiczenia oraz końcowe wnioski.
"""


result = parse_report_instruction(
    instruction=instruction,
    available_columns=df.columns.tolist(),
    units=units,
)


print(
    result.model_dump_json(
        indent=2
    )
)