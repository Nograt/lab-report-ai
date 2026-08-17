from app.core.openai_client import client

from app.schemas.instruction_preparation import (
    InstructionPreparation,
)

from app.schemas.measurement import (
    MeasurementTableInfo,
)


MODEL = "gpt-5.6"

PREPARER_SYSTEM_PROMPT = """
You prepare laboratory instructions for further processing
by another backend parser.

You receive:

- the original laboratory instruction as a PDF,
- metadata describing measurement tables available in Excel.

Your task is NOT to generate the laboratory report.

Your task is to convert the original laboratory instruction
into a clean textual instruction that can later be parsed
by another system.

Return data strictly according to InstructionPreparation.


GENERAL RULES

- Write the normalized instruction in Polish.
- Preserve the meaning of the original laboratory instruction.
- Do not invent formulas.
- Do not invent measurements.
- Do not invent numerical constants.
- Do not invent experiment stages.
- Use information from text, equations, tables and figures
  contained in the PDF.
- Compare the requirements from the PDF with the available
  Excel measurement tables.
- Do not use general scientific knowledge to modify formulas
  from the PDF.
- Do not derive alternative formulas that are not explicitly
  present in the PDF.
- Do not convert formulas merely because Excel uses different
  units or different variable names.


NORMALIZED INSTRUCTION

The `instruction` field should contain a clear textual
laboratory instruction suitable for the next backend parser.

It should contain, when supported by both the PDF and
the available Excel data:

- exercise title,
- exercise purpose,
- measurement/result stages,
- quantities used in each stage,
- formulas required for calculations,
- charts required by the original instruction,
- whether multiple characteristics should be placed
  on the same chart,
- analysis or interpretation requirements,
- final conclusion requirements.

Write it like a normal laboratory instruction.

Do not write explanations addressed to the backend.
Do not write JSON inside the instruction field.
Do not describe what the AI did.


EXCEL IS THE AUTHORITATIVE SOURCE OF AVAILABLE DATA

The Excel workbook defines which measurement quantities
and result columns are actually available to the backend.

For each measurement stage:

- Match the PDF section to the most appropriate Excel table.
- Use exact Excel column names whenever a PDF quantity
  corresponds to an available Excel column.
- Preserve Excel notation when a clear correspondence exists.
- Do not invent Excel columns.
- Do not request generation of additional table columns
  that are not present in Excel.

If the PDF contains an auxiliary or calculated quantity
whose corresponding column does NOT exist in the matched
Excel table:

- do not include that calculation in the normalized
  instruction,
- unless that quantity is necessary as an intermediate value
  for calculating another output column that DOES exist
  in Excel.

Example:

If the PDF contains:

I0W = I0 * cosφ0

but the Excel table does not contain an I0W column and no
required Excel output depends on I0W,

do not include I0W in the normalized instruction.


CALCULATED OUTPUTS

A calculation should normally be included only when:

1. its output corresponds to an existing Excel column,
   especially an empty result column,

or

2. it is an indispensable intermediate calculation required
   to calculate another output that corresponds to an
   existing Excel column.

Do not include theoretical or auxiliary calculations merely
because they appear in the PDF.

If the Excel already contains measured values for a quantity,
do not describe that quantity as something that must be
calculated unless the PDF explicitly requires recalculation
and the Excel structure clearly supports it.


FORMULA FIDELITY

Formulas in the normalized instruction must remain faithful
to the formulas contained in the PDF.

Do not:

- alter formulas using domain knowledge,
- perform unit conversions inside formulas,
- replace variables with supposedly equivalent variables,
- simplify formulas into a different physical form,
- infer constants that are missing from the PDF.

Example:

If the PDF contains:

T_l = 9.81 * F * l

where F is expressed in kg,

and Excel contains a column F_l with unit N,

do NOT automatically replace the formula with:

T_l = F_l * l

Instead, preserve the original PDF formula if it can be
processed safely.

If the PDF formula cannot be directly matched to available
Excel variables because of incompatible notation or units,
do not invent a transformed formula.

The normalized instruction may state that the required
parameter or mapping must be clarified.


CHARTS

Extract charts explicitly required by the PDF.

For every chart:

- preserve the dependent and independent variables,
- preserve whether characteristics should be placed on one
  common chart or on separate charts,
- map variables to exact Excel column names when a clear
  correspondence exists.

Do not change chart axes merely because another relation
would also be scientifically reasonable.

Do not invent additional charts.

If a chart requires a quantity that cannot be produced from
the available Excel data and known parameters, omit that
chart from the normalized instruction.


UNSUPPORTED EXPERIMENT STAGES

If an entire measurement/result stage from the PDF has no
corresponding Excel measurement table:

- do not invent measurements,
- do not invent a table,
- do not include that stage as a processable result section
  in the normalized instruction.

The purpose or general context may still mention the broader
exercise if appropriate, but the normalized processing
instructions should contain only stages supported by the
uploaded Excel data.


MISSING PARAMETERS

A missing parameter is a scalar value required to fully
perform a supported calculation or another explicit
requirement from the PDF, but whose numerical value is not
available in either:

- the laboratory instruction,
- the available Excel metadata,
- or another directly available parameter.

Examples:

- lever arm length l,
- number of pole pairs p,
- supply frequency f1,
- synchronous speed n1,
- rated voltage U_N when the PDF explicitly requires
  evaluation at the rated operating point.

Do NOT report measured row-by-row quantities as missing
parameters.

Do NOT report calculated result columns as missing
parameters.

Do NOT guess missing numerical values.

For every missing parameter return:

- name: human-readable Polish name,
- symbol: symbol used in the instruction,
- unit: unit if explicitly known,
- description: short explanation of why the value is needed.


MISSING PARAMETER DEPENDENCIES

Do not report both a derived parameter and all of its source
parameters as missing when that would unnecessarily ask the
user for redundant information.

Prefer the most fundamental parameters explicitly used by
the PDF.

Example:

If:

n1 = 60 * f1 / p

and both f1 and p are missing,

return f1 and p as missing parameters.

Do not additionally return n1 as missing because n1 can be
calculated after f1 and p are provided.


IMPORTANT EXAMPLE

If the PDF contains:

s0 = (n1 - n0) / n1

and Excel contains columns n0 and s0,

preserve this calculation.

If n1 depends on:

n1 = 60 * f1 / p

and f1 or p are missing,

preserve both formulas and return the missing scalar
parameters.

Do not replace n1 with a guessed constant such as 1500.


FINAL CHECK

Before returning the result ensure that:

- formulas come from the PDF,
- formulas have not been transformed using outside knowledge,
- charts come from the PDF,
- chart axes match the PDF requirements,
- Excel column names are preserved whenever a clear mapping
  exists,
- no unnecessary auxiliary Excel columns are introduced,
- calculations mainly produce existing Excel result columns,
- missing scalar values were not guessed,
- missing_parameters contains only genuinely required
  parameters,
- unsupported experiment stages were not invented,
- the normalized instruction can be safely passed to another
  parser without requiring it to reinterpret the PDF.
"""



def prepare_instruction(
    instruction_file_id: str,
    measurement_tables: list[MeasurementTableInfo],
) -> InstructionPreparation:

    tables_context = "\n\n".join(
        [
            f"""
TABLE ID: {table.table_id}
TITLE: {table.title}
SHEET: {table.sheet_name}
COLUMNS: {table.columns}
UNITS: {table.units}
""".strip()
            for table in measurement_tables
        ]
    )

    user_prompt = f"""
Prepare a normalized laboratory instruction
from the attached PDF.

AVAILABLE EXCEL MEASUREMENT TABLES:

{tables_context}

Compare the PDF requirements with the available Excel tables.

Return:

1. a clean textual laboratory instruction suitable for
   further parsing,
2. any missing scalar parameters required to perform
   calculations.

Do not generate the report itself.
"""

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": PREPARER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": instruction_file_id,
                    },
                    {
                        "type": "input_text",
                        "text": user_prompt,
                    },
                ],
            },
        ],
        text_format=InstructionPreparation,
    )

    result = response.output_parsed

    if result is None:
        raise ValueError(
            "Unable to prepare laboratory instruction."
        )

    return result