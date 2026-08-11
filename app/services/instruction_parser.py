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
   
CALCULATIONS

Extract mathematical calculations explicitly required by the instruction.

For every calculation:
- output is the name of the calculated quantity,
- unit is the output unit if it is explicitly known, otherwise null,
- expression must represent the mathematical formula as an expression tree.

Expression types:

1. variable
{
    "type": "variable",
    "name": "P"
}

2. constant
{
    "type": "constant",
    "value": 3
}

3. operation
{
    "type": "operation",
    "operation": "...",
    "args": [...]
}

Supported operations:
add
subtract
multiply
divide
power
sqrt
sin
cos
tan
log
ln
abs

Examples:

PK = P - Pap

becomes:

{
    "output": "PK",
    "unit": "W",
    "expression": {
        "type": "operation",
        "operation": "subtract",
        "args": [
            {
                "type": "variable",
                "name": "P"
            },
            {
                "type": "variable",
                "name": "Pap"
            }
        ]
    }
}

Do not invent formulas that are not present in the instruction.

Preserve variable names as closely as possible to the notation used in the instruction.

Calculations do not need to be returned in execution order.
The backend determines calculation dependencies and execution order.

A chart may use a variable that is produced by a calculation.
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
