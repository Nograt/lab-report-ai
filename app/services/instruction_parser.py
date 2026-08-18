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
- Do not create sections for purpose, theory, setup or conclusions.
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


==================================================
CALCULATION TABLE ASSIGNMENT
==================================================

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
TABLE STRUCTURE
==================================================

The matched Excel measurement table is the authoritative source
of the table structure shown in the final report.

For every ReportSection that contains a table:

- table.columns MUST contain ALL columns from the matched Excel
  measurement table.
- Preserve the original Excel column order.
- Preserve the exact Excel column names.
- Never remove an Excel column because it is not mentioned
  in the laboratory instruction.
- Never remove auxiliary measurement columns.
- Never remove columns because they are not used in calculations,
  charts, or report analysis.
- Never reduce the table to only the variables required by
  the laboratory instruction.
- Existing calculated columns from Excel must also be preserved.
- If the instruction requires a calculated quantity and its output
  column already exists in Excel, use that exact column name.
- A named intermediate calculation does NOT need to be added to
  ReportSection.table.columns when no such Excel column exists.
  It may exist only as a CalculationSpecification used by later calculations.
- Do not add helper/intermediate columns to the visible report table
  unless they already exist in Excel or the instruction explicitly requires
  that quantity to be shown as a table column.

IMPORTANT:

The instruction determines WHAT should be calculated, plotted,
and discussed.

The Excel table determines WHICH COLUMNS are displayed in the
report table.

These are separate responsibilities.

Example:

If the matched Excel table contains:

Lp., U₀, I₀, P₀, Iu, Pu, Iz, Pz, Uz, Uc, n₀, s₀, cosφ₀

then table.columns MUST contain exactly those Excel columns in
that order, even if the instruction discusses only:

U₀, I₀, P₀, n₀, s₀, cosφ₀.

Do not use the instruction to filter the Excel table columns.


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

If Excel metadata indicates that an existing result column is already
populated, do not create a new calculation that overwrites it unless the
normalized instruction explicitly requires recalculating that quantity.

If Excel metadata indicates that a result column is empty and the
instruction explicitly provides a formula for it, create the corresponding
CalculationSpecification.


==================================================
INTERMEDIATE CALCULATIONS
==================================================

Named intermediate quantities are important for readable example
calculations in the final report.

If the instruction explicitly defines a named intermediate quantity
with its own formula, ALWAYS preserve it as a separate
CalculationSpecification when it is later used by another calculation.

Do NOT inline the intermediate expression into later formulas.

Example:

If the instruction contains:

n₁ = 60 * f₁ / p
s₀ = (n₁ - n₀) / n₁

create two calculations assigned to the same table:

1. output = "n₁"
   expression = 60 * f₁ / p

2. output = "s₀"
   expression = (n₁ - n₀) / n₁

The second calculation MUST reference variable "n₁".

Do NOT produce:

s₀ = ((60 * f₁ / p) - n₀) / (60 * f₁ / p)

The same rule applies when a named intermediate is reused by several
later calculations.

If the same intermediate quantity is required independently in two
measurement tables, create one CalculationSpecification for each table,
using the appropriate table_id.

Example:

If table 1 uses n₁ to calculate s₀ and table 3 uses n₁ to calculate s,
then it is valid and preferred to return:

- table_id=1, output="n₁"
- table_id=1, output="s₀" referencing "n₁"
- table_id=3, output="n₁"
- table_id=3, output="s" referencing "n₁"

Do not make calculations from one table depend on n₁ calculated for
another table.

A named intermediate calculation may remain invisible in
ReportSection.table.columns if no corresponding Excel column exists.
It should still appear in the section's calculation_outputs when it is
part of the logical calculation sequence shown in the report.


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


==================================================
IMPORTANT ABOUT PHYSICAL VARIABLE NAMES
==================================================

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


==================================================
CALCULATIONS IN SECTIONS
==================================================

Sections do not duplicate CalculationSpecification objects.

Instead:

- calculation_outputs contains the output names of calculations
  belonging to the section.
- Every value in calculation_outputs must exactly match an `output`
  from the global calculations list for the SAME table_id as the section.
- Preserve the logical presentation order when possible.
- Preserve named intermediate calculations before calculations that
  depend on them.

Example logical order:

n₁
s₀

not only:

s₀

when the instruction explicitly defines n₁ as a separate intermediate.


==================================================
CHARTS
==================================================

Every ChartSpecification MUST contain table_id.

table_id identifies the measurement table from which this
particular data series obtains its x and y values.

Several ChartSpecification objects sharing the same figure_id
may use different table_id values.

Example:

A common physical figure may contain:

- n = f(U) from table_id = 5
- n0 = f(U) from table_id = 2

Both series may share the same figure_id, but each series must
retain its own table_id.

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
- When x or y corresponds to an AVAILABLE EXCEL COLUMN,
  use the exact Excel column name whenever possible.
- A chart may use a variable produced by a calculation.
- Do not invent additional charts.

Correct:

x = "I"
y = "Uk"

Incorrect:

y = "Uk(I)"

FILTERED CHART SERIES

A ChartSpecification may describe only a subset of rows
from its source table.

Use:

- filter_column
- filter_value

when the instruction requires several series with the same
x and y variables but for different fixed values of another
quantity.

Example:

For one common figure containing:

n = f(U) for Ts = 0.25 TN
n = f(U) for Ts = 0.5 TN
n = f(U) for Ts = TN

create three ChartSpecification objects with:

x = U
y = n
filter_column = Ts
filter_value = the corresponding Ts value or category
label = a human-readable series name.

If a series does not require filtering, return null for
filter_column and filter_value.


==================================================
CHART GROUPING
==================================================

A ChartSpecification represents ONE data series.

figure_id identifies the PHYSICAL FIGURE shown in the final report.

Several ChartSpecification objects may share the same figure_id.

If the instruction explicitly says that multiple characteristics
must be shown on the same chart, all corresponding ChartSpecification
objects MUST have exactly the same figure_id.

Example:

"Na jednym wspólnym wykresie przedstawić:
I = f(P),
cosφ = f(P),
s = f(P),
η = f(P)"

must become:

I(P)       figure_id = 1
cosφ(P)    figure_id = 1
s(P)       figure_id = 1
η(P)       figure_id = 1

Do NOT assign separate figure_id values in this case.

Assign a new figure_id only when the instruction requires
a separate physical figure.

figure_id values should be sequential across PHYSICAL FIGURES,
not across individual ChartSpecification objects.

figure_id identifies the physical figure.

table_id identifies the data source of one individual series.

Do not assume that all series sharing one figure_id come from
the same measurement table.


==================================================
CHARTS IN SECTIONS
==================================================

Sections do not duplicate chart definitions.

Instead:

- chart_figure_ids contains PHYSICAL figure_id values belonging
  to the section.
- Every figure_id in chart_figure_ids must correspond to at least one
  ChartSpecification from the global charts list.
- If several ChartSpecification objects share one figure_id,
  include that figure_id only ONCE in chart_figure_ids.
- A physical figure must belong to exactly one ReportSection.
- Never assign the same figure_id to multiple ReportSections.
- Determine section ownership from the represented variables and
  measurement stage, not from the numerical value of figure_id.


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
MEASUREMENT TABLES
==================================================

The backend provides a list of available measurement tables.

Each table may contain:

- table_id,
- title,
- sheet_name,
- columns,
- units,
- column_has_values.

`column_has_values`, when provided, indicates whether a given Excel
column currently contains any values.

Every ReportSection must reference exactly one measurement table
using table_id.

Rules:

- table_id must match one of the provided measurement tables.
- Select the table whose columns and meaning best match the section.
- Do not invent table_id values.
- Do not assign the same table to multiple unrelated measurement stages
  unless the instruction clearly indicates that they use the same data.
- ReportSection.table.columns must preserve all columns from the
  measurement table referenced by table_id.
- Calculations for a section must use variables available in its
  measurement table or outputs calculated from those variables.
- Charts belonging to a section must use data available in the
  measurement table referenced by that section or calculated outputs
  assigned to the same table.


==================================================
CONSISTENCY RULES
==================================================

Before returning the result, ensure that:

- every calculation_outputs value exists in calculations.output for
  the same table_id as the section,

- every chart_figure_ids value exists in charts.figure_id,

- each physical figure_id belongs to exactly one ReportSection,

- repeated figure_id values in charts are allowed when they represent
  multiple series on one physical figure,

- table.columns preserves all columns from the matched Excel table
  in their original order,

- named intermediate quantities explicitly defined in the instruction
  are preserved as separate CalculationSpecification objects,

- later calculations reference those named intermediate quantities
  by variable name instead of duplicating their full expression,

- if the same named intermediate is needed in different tables,
  it is defined separately for each table_id,

- populated Excel columns are not overwritten by new calculations
  unless explicitly required by the instruction,

- empty result columns with explicit formulas are represented by
  calculations when needed,

- existing measurement variables use exact AVAILABLE EXCEL COLUMN
  names whenever possible,

- chart axes and chart grouping follow the instruction exactly,

- figure_id values are sequential across physical figures,

- section_id values start at 1 and are sequential,

- no formula, chart, section, table column or unit has been invented
  without support from the instruction or Excel metadata.
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
- A physical figure_id may be shared by multiple ChartSpecification
  objects when they represent multiple series on the same physical figure.
- Each physical figure_id must belong to exactly one ReportSection.
- Do not assign the same physical figure_id to multiple ReportSections.
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

        return specification

    except ValueError as error:
        first_error = str(error)

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


        raise ValueError(
            "Report specification remained invalid "
            "after automatic repair. "
            f"First error: {first_error}. "
            f"Repair error: {second_error}"
        )


    return repaired_specification