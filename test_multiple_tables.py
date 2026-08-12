from app.schemas.measurement import MeasurementTableInfo
from app.services.instruction_parser import parse_report_instruction


tables = [
    MeasurementTableInfo(
        table_id=1,
        title="Bieg jałowy",
        sheet_name="Pomiary",
        columns=["Lp", "U0", "I0", "P0", "n0"],
        units={
            "Lp": None,
            "U0": "V",
            "I0": "A",
            "P0": "W",
            "n0": "rpm",
        },
    ),

    MeasurementTableInfo(
        table_id=2,
        title="Stan zwarcia",
        sheet_name="Pomiary",
        columns=[
            "Lp",
            "Uk",
            "I",
            "P",
            "Pap",
            "PK",
            "cosφK",
            "Tl",
        ],
        units={
            "Lp": None,
            "Uk": "V",
            "I": "A",
            "P": "W",
            "Pap": "W",
            "PK": "W",
            "cosφK": None,
            "Tl": "mNm",
        },
    ),

    MeasurementTableInfo(
        table_id=3,
        title="Próba obciążenia",
        sheet_name="Pomiary",
        columns=[
            "Lp",
            "U",
            "I",
            "P",
            "n",
            "M",
            "P2",
            "eta",
        ],
        units={
            "Lp": None,
            "U": "V",
            "I": "A",
            "P": "W",
            "n": "rpm",
            "M": "Nm",
            "P2": "W",
            "eta": None,
        },
    ),

    MeasurementTableInfo(
        table_id=4,
        title="Regulacja prędkości",
        sheet_name="Pomiary",
        columns=[
            "Lp",
            "U",
            "I",
            "n",
        ],
        units={
            "Lp": None,
            "U": "V",
            "I": "A",
            "n": "rpm",
        },
    ),
]


instruction = """
Temat ćwiczenia: Badanie silnika uniwersalnego.

1. Bieg jałowy.
Przedstawić tabelę U0, I0, P0, n0.
Wykonać wykresy I0(U0) oraz n0(U0).

2. Stan zwarcia.
Przedstawić tabelę Uk, I, P, Pap, PK, cosφK, Tl.
Obliczyć PK = P - Pap.
Obliczyć cosφK = PK / (Uk * I).
Wykonać wykresy PK(I) oraz cosφK(I).

3. Próba obciążenia.
Przedstawić tabelę U, I, P, n, M, P2, eta.
Wykonać wykresy n(M), I(M), eta(M).

4. Regulacja prędkości.
Przedstawić tabelę U, I, n.
Wykonać wykresy n(U) oraz I(U).

Każdą część należy opisać i przeanalizować.
Na końcu przedstawić wnioski.
"""


result = parse_report_instruction(
    instruction=instruction,
    measurement_tables=tables,
)


print(
    result.model_dump_json(
        indent=2,
    )
)