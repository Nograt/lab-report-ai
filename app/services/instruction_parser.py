import os

from openai import OpenAI
from app.schemas.report import ReportSpecification

client = OpenAI()

SYSTEM_PROMPT = """
You analyze laboratory report instructions.

Your task is to extract chart requirements from the instruction.

Return data strictly according to ReportSpecification.

Rules:

1. A characteristic written as U(I) means:
   x = "I"
   y = "U"

2. A characteristic written as P(I) means:
   x = "I"
   y = "P"

3. x and y must contain only the variable symbol.
   Never include the complete characteristic notation.

Correct:
x = "I"
y = "Uk"

Incorrect:
y = "Uk(I)"

4. If multiple characteristics are explicitly required
   on the same chart, give them the same figure_id.

Example:

"Na jednym wykresie przedstawić Uk(I), P(I) oraz cosφK(I)"

means:

Uk(I)     figure_id = 1
P(I)      figure_id = 1
cosφK(I)  figure_id = 1

5. If characteristics are required on separate charts,
   use different figure_id values.

6. source_section should contain the referenced measurement
   section if the instruction explicitly specifies one,
   for example "punkt 3".

If no source section is specified, return null.

7. Do not invent additional charts.

8. Preserve variable symbols as closely as possible
   to the notation used in the instruction.
"""

MODEL = "gpt-5-mini"

def parse_report_instruction(instruction: str,)-> ReportSpecification:
    response = client.responses.parse(
        model=MODEL, 
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": instruction,
            },
        ],
        text_format=ReportSpecification,
            
                                      )
    
    specification = response.output_parsed
    
    if specification is None:
        raise RuntimeError("Nie udało utworzyć sie specyfikacji sprawozdania")
    
    return specification
