from app.services.instruction_parser import (
    parse_report_instruction,
)


instruction = """
Na podstawie pomiarów z punktu 3
wykonać na jednym wykresie charakterystyki
Uk(I), P(I) oraz cosφK(I).
"""


result = parse_report_instruction(
    instruction
)

print(result)
print(result.model_dump())