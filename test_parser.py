from app.services.instruction_parser import parse_report_instruction


instruction = """
Obliczyć moc PK według zależności:

PK = P - Pap

Następnie wykonać wykres PK(I).
"""


result = parse_report_instruction(
    instruction
)


print(
    result.model_dump_json(
        indent=2
    )
)