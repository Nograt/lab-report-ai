
import json
from app.schemas.report import ReportSpecification
from app.core.openai_client import client
from app.schemas.measurement import MeasurementTableInfo
from app.services.specification_validator import validate_report_specification

SYSTEM_PROMPT = """
You analyze laboratory report instructions.

Your task is to extract the complete structure and processing requirements
needed to prepare a laboratory report.

Return data strictly according to ReportSpecification.

Do not invent measurements, formulas, tables, charts, sections,
units, or laboratory requirements that are not supported by the instruction
or by the provided Excel metadata.


==================================================
GENERAL REPORT STRUCTURE
==================================================

The report may contain:

- report title,
- purpose,
- theory,
- measurement setup,
- measurement/result sections,
- conclusions.

Measurement/result sections are stored in `sections`.

Purpose, theory, setup and conclusions are NOT ReportSection objects.
They are controlled by:

- include_purpose
- include_theory
- include_setup
- include_conclusions

Rules:

- report_title should contain only the overall laboratory exercise title.
- If the instruction contains "Temat ćwiczenia: X",
  report_title must contain only X.
- Do not include labels such as "Temat ćwiczenia:" in report_title.
- Remove trailing punctuation from report_title.
- If the instruction explicitly provides a title such as
  "Temat ćwiczenia: ...", preserve that title as closely as possible.

- Do not append measurement section titles, subsection names,
  chart names or processing stages to report_title.

- If the overall exercise title cannot be identified from the instruction,
  return null.


- include_purpose should always be true.

- The final report always contains a purpose section.


- include_setup should always be true.

- The final report always contains a description of the tested circuit,
  measurement setup or laboratory station.

- The content of the setup section must be based only on information
  available in the laboratory instruction or other provided materials.

- Do not invent equipment, circuit elements, connections, apparatus
  or measurement procedures that are not supported by the provided materials.

- Even if the instruction does not explicitly request a setup description,
  include_setup remains true.


- include_conclusions should always be true.

- The final report always contains conclusions.


- include_theory should be true only when the instruction requires
  theoretical description, theoretical background, description of
  the physical phenomenon, principle of operation or similar theory content.

- Otherwise include_theory should be false.


- A request to "describe the measurements", "describe the test",
  "describe the results" or similar wording should normally be represented
  by ReportSection.include_description = true.

- Such wording does not create a separate report section by itself.


- Preserve the order of measurement/result sections from the instruction.

==================================================
REPORT SECTIONS
==================================================

A ReportSection represents one measurement or result-processing stage,
for example:

- no-load test,
- short-circuit test,
- load test,
- resistance measurement,
- diode forward-bias measurement.

For every distinct measurement/result stage return one ReportSection.

Rules:

- section_id is an internal sequential identifier starting from 1.

- section_id is NOT visible numbering such as 3.1, 3.2 or 4.1.

- title should describe the measurement/result stage.

- Preserve section titles from the instruction whenever possible.

- Do not create sections for:
  purpose,
  theory,
  setup,
  conclusions.

- If the instruction contains calculations, a results table or charts
  but does not explicitly name the measurement stage, create one reasonable
  result section describing that group of work.

- Do not merge clearly separate measurement stages into one section.
- section_id identifies the report section.
- table_id identifies the measurement table used by that section.
- section_id and table_id are different concepts and do not need
  to have the same value.
  - calculation_outputs contains calculation output names belonging
  to the same table_id as the section.
  
  CALCULATION TABLE ASSIGNMENT

Every CalculationSpecification must contain table_id.

Rules:

- table_id must match one of the provided measurement tables.
- Assign the calculation to the table containing the variables
  used by its expression.
- The calculation must belong to the same measurement table
  as the ReportSection that references its output.
- Do not invent table_id values.
- Variables used by the calculation must exist in the referenced
  measurement table or be outputs of other calculations assigned
  to the same table.
- Calculations from different measurement tables must never depend
  on each other.
- The same output name may exist in different tables.
  In that case, table_id distinguishes the calculations.

==================================================
TABLES
==================================================

A section may contain one result table.

Rules:

- table may be null if the section does not require a table.

- table.title should describe the results represented by the table.

- table.columns contains the variables that belong to that section.

- When a variable already exists in AVAILABLE EXCEL COLUMNS,
  use the exact Excel column name whenever possible.

- A table may include calculated quantities produced by calculations.

- Calculated output columns may be included even if their cells are
  currently empty in the uploaded Excel file.

- Do not invent unrelated columns.

- Do not automatically include every Excel column in every section.

- Preserve variable notation as closely as possible.


==================================================
CALCULATIONS
==================================================

Extract mathematical calculations explicitly required by the instruction.

Calculations are stored globally in `calculations`.

For every calculation:

- output is the name of the calculated quantity.

- expression represents the mathematical formula as an expression tree.

- unit should be determined in this order:

  1. If output exists in COLUMN UNITS and its unit is known,
     use that unit.

  2. Otherwise, if the instruction explicitly specifies the unit,
     use that unit.

  3. Otherwise return null.

Do not infer a unit only from general scientific knowledge.

Calculations do NOT need to be returned in execution order.
The backend determines dependencies and execution order.

A calculation may depend on the output of another calculation.

Do not invent formulas that are not present in the instruction.

When an input variable corresponds to an existing Excel column,
use its exact name from AVAILABLE EXCEL COLUMNS whenever possible.


==================================================
EXPRESSION TREE
==================================================

Expression types:

VARIABLE

{
  "type": "variable",
  "name": "P"
}

CONSTANT

{
  "type": "constant",
  "value": 3
}

OPERATION

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


Operation argument rules:

- add: at least 2 arguments
- multiply: at least 2 arguments
- subtract: exactly 2 arguments
- divide: exactly 2 arguments
- power: exactly 2 arguments
- sqrt: exactly 1 argument
- sin: exactly 1 argument
- cos: exactly 1 argument
- tan: exactly 1 argument
- log: exactly 1 argument
- ln: exactly 1 argument
- abs: exactly 1 argument


IMPORTANT ABOUT PHYSICAL VARIABLE NAMES

Names such as:

cosφ
cosφK
sinφ
η
ΔP

may be names of physical quantities or Excel columns.

If such a name appears as an AVAILABLE EXCEL COLUMN or is clearly
used as a named measured/calculated quantity, represent it as a variable.

Example:

cosφK = PK / (Uk * I)

Here `cosφK` is the output variable.

Do NOT interpret `cosφK` as a cosine operation.

Use the `cos` operation only when the instruction explicitly describes
the cosine of an argument, for example:

cos(φ)


Example calculation:

PK = P - Pap

becomes:

{
  "output": "PK",
  "unit": null,
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


==================================================
CALCULATIONS IN SECTIONS
==================================================

Sections do not duplicate CalculationSpecification objects.

Instead:

- calculation_outputs contains the output names of calculations
  belonging to the section.

- Every value in calculation_outputs must exactly match an `output`
  from the global calculations list.

- Preserve the logical presentation order when possible.

- A calculation may depend on another calculation even if the backend
  later executes them in a different order.


==================================================
CHARTS
==================================================

Extract only charts required by the instruction.

A characteristic written as:

U(I)

means:

x = "I"
y = "U"

A characteristic written as:

P(I)

means:

x = "I"
y = "P"

Rules:

- x and y contain only variable names.

Correct:

x = "I"
y = "Uk"

Incorrect:

y = "Uk(I)"

- When x or y corresponds to an AVAILABLE EXCEL COLUMN,
  use the exact Excel column name whenever possible.

- A chart may use a variable produced by a calculation.

- Do not invent additional charts.


==================================================
CHART GROUPING
==================================================

If multiple characteristics are explicitly required on the SAME chart,
give them the same figure_id.

Example:

"Na jednym wykresie przedstawić Uk(I), P(I) oraz cosφK(I)"

becomes:

Uk(I)     figure_id = 1
P(I)      figure_id = 1
cosφK(I)  figure_id = 1


If characteristics are required on separate charts,
use different figure_id values.

figure_id values should start from 1 and be assigned sequentially.

Do not reuse the same figure_id for charts that the instruction says
must be separate.


==================================================
CHARTS IN SECTIONS
==================================================

Sections do not duplicate chart definitions.

Instead:

- chart_figure_ids contains figure_id values of charts belonging
  to the section.

- Every figure_id in chart_figure_ids must correspond to a chart
  from the global charts list.

- A chart should normally belong to the measurement/result section
  whose data it represents.


==================================================
DESCRIPTION AND ANALYSIS
==================================================

For measurement/result sections:

- include_description should normally be true.

- include_analysis should normally be true when the section contains
  measured results, calculated results or charts that require interpretation.

These fields only indicate that text should later be generated.

Do NOT write the actual report description or analysis in
ReportSpecification.


==================================================
SOURCE SECTION
==================================================

source_section is a legacy/global reference to a source measurement section.

If the instruction explicitly references one source section,
for example "punkt 3", return that reference.

If there is no single explicit source section, return null.

Do not use source_section instead of ReportSection objects.


==================================================
CONSISTENCY RULES
==================================================

Before returning the result, ensure that:

- every calculation_outputs value exists in calculations.output,

- every chart_figure_ids value exists in charts.figure_id,

- calculated table columns correspond to calculation outputs,

- existing measurement variables use AVAILABLE EXCEL COLUMNS
  whenever possible,

- figure_id values are consistent,

- section_id values start at 1 and are sequential,

- no formula, chart or section has been invented without support
  from the instruction or Excel metadata.
  
MEASUREMENT TABLES

The backend provides a list of available measurement tables.

Each table has:
- table_id,
- title,
- sheet_name,
- columns,
- units.

Every ReportSection must reference exactly one measurement table
using table_id.

Rules:

- table_id must match one of the provided measurement tables.
- Select the table whose columns and meaning best match the section.
- Do not invent table_id values.
- Do not assign the same table to multiple unrelated measurement stages
  unless the instruction clearly indicates that they use the same data.
- The columns selected in ReportSection.table.columns must exist
  in the measurement table referenced by table_id.
- Calculations for a section must use variables available in its
  measurement table or outputs calculated from those variables.
- Charts belonging to a section must use data available in the
  measurement table referenced by that section.
"""

MODEL = "gpt-5.6"

def repair_report_specification(
    specification: ReportSpecification,
    validation_error: str,
    instruction: str,
    measurement_tables: list[MeasurementTableInfo],
) -> ReportSpecification:

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

    repair_input = f"""
The previously generated ReportSpecification failed backend validation.

VALIDATION ERROR:

{validation_error}

ORIGINAL LABORATORY INSTRUCTION:

{instruction}

AVAILABLE MEASUREMENT TABLES:

{tables_context}

PREVIOUS REPORT SPECIFICATION:

{specification.model_dump_json(indent=2)}

Correct the ReportSpecification.

Rules:

- Fix the validation error.
- Preserve the meaning and requirements of the laboratory instruction.
- Do not remove required charts merely to avoid the validation error.
- Do not invent new measurements, tables, calculations or variables.
- Keep table assignments consistent with available measurement tables.
- Figure IDs must be globally unique.
- Every figure must belong to exactly one report section.
- Return the complete corrected ReportSpecification.
"""

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": repair_input,
            },
        ],
        text_format=ReportSpecification,
    )

    result = response.output_parsed

    if result is None:
        raise ValueError(
            "Unable to repair report specification."
        )

    return result

def parse_report_instruction(
    instruction: str,
    measurement_tables: list[MeasurementTableInfo]
) -> ReportSpecification:

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


    user_input = f"""
      REPORT INSTRUCTION:

      {instruction}

      AVAILABLE MEASUREMENT TABLES:

      {tables_context}
      """

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_input,
            },
        ],
        text_format=ReportSpecification,
    )

    result = response.output_parsed

    if result is None:
        raise ValueError(
            "Unable to parse report instruction."
        )

    return result
  
def parse_report_instruction_with_repair(
    instruction: str,
    measurement_tables: list[MeasurementTableInfo],
) -> ReportSpecification:


    specification = parse_report_instruction(
        instruction=instruction,
        measurement_tables=measurement_tables,
    )

    try:
        validate_report_specification(
            specification=specification,
            measurement_tables=measurement_tables,
        )

        print(
            "[SPEC VALIDATION] Specification valid."
        )

        return specification

    except ValueError as error:
        first_error = str(error)

        print(
            "[SPEC VALIDATION] Validation failed:"
        )
        print(first_error)


    print(
        "[SPEC REPAIR] Starting automatic repair..."
    )

    repaired_specification = repair_report_specification(
        specification=specification,
        validation_error=first_error,
        instruction=instruction,
        measurement_tables=measurement_tables,
    )


    try:
        validate_report_specification(
            specification=repaired_specification,
            measurement_tables=measurement_tables,
        )

    except ValueError as error:
        second_error = str(error)

        print(
            "[SPEC REPAIR] Repair failed:"
        )
        print(second_error)

        raise ValueError(
            "Report specification remained invalid "
            "after automatic repair. "
            f"First error: {first_error}. "
            f"Repair error: {second_error}"
        )

    print(
        "[SPEC REPAIR] Specification repaired successfully."
    )

    return repaired_specification