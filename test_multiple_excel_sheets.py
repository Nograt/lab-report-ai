from app.services.excel_reader import (
    read_measurement_tables,
    create_measurement_table_infos,
)

from app.services.instruction_parser import (
    parse_report_instruction,
)


# ============================================================
# 1. Odczyt prawdziwego Excela
# ============================================================

tables = read_measurement_tables(
    "test_multiple.xlsx"
)


# ============================================================
# 2. Metadata dla AI
# ============================================================

infos = create_measurement_table_infos(
    tables
)


print("\n=== TABELE WYKRYTE W EXCELU ===\n")

for info in infos:
    print(
        info.model_dump_json(
            indent=2
        )
    )


# ============================================================
# 3. Instrukcja laboratoryjna
# ============================================================

instruction = """
Temat ćwiczenia: Badanie silnika indukcyjnego.

1. Próba biegu jałowego.

Na podstawie wyników pomiarów biegu jałowego należy przedstawić
tabelę zawierającą U₀, I₀, P₀, n₀, s₀ oraz cosφ₀.

Należy wykonać wykresy:

I₀(U₀)
P₀(U₀)
cosφ₀(U₀)

Dodatkowo obliczyć wielkość testową:

X0 = U₀ * I₀


2. Charakterystyka momentu.

Należy przedstawić wyniki pomiarów zawierające:
Uₖ, Iₖ, Pₖ, cosφₖ, Fₗ oraz Tₗ.

Należy wykonać wykresy:

Tₗ(Iₖ)
cosφₖ(Iₖ)

Dodatkowo obliczyć wielkość testową:

Xk = Uₖ * Iₖ

3. Próba obciążenia.

Należy przedstawić tabelę wyników zawierającą:
I, Pin, cosφ, Ia, Ui, Pi, POH, P, n, s, η oraz Ts.

Należy wykonać wykresy:

n(Ts)
I(Ts)
η(Ts)
cosφ(Ts)

Każdą część należy krótko opisać oraz przeanalizować otrzymane
wyniki i charakterystyki.

Sprawozdanie powinno zawierać cel ćwiczenia,
opis badanego układu oraz końcowe wnioski.
"""


# ============================================================
# 4. AI analizuje instrukcję + rzeczywiste arkusze
# ============================================================

specification = parse_report_instruction(
    instruction=instruction,
    measurement_tables=infos,
)


# ============================================================
# 5. Wynik
# ============================================================

print("\n=== REPORT SPECIFICATION ===\n")

print(
    specification.model_dump_json(
        indent=2
    )
)