import json

from app.schemas.analysis import SectionAnalysis
from app.schemas.section import ReportSection
from app.schemas.report_text import SectionTextContent, ReportTextContent
from app.schemas.report import ReportSpecification
from app.core.openai_client import client


MODEL = "gpt-5.6"


REPORT_SYSTEM_PROMPT = """
You write complete laboratory report text in Polish.

You receive:
- the parsed report specification,
- the original laboratory instruction,
- deterministic numerical analyses prepared by Python.

Return data strictly according to ReportTextContent.

GENERAL RULES

- Write in Polish.
- Use formal but natural engineering laboratory-report language.
- Base numerical statements only on the provided analysis.
- Do not perform new calculations.
- Do not invent measurement values.
- Do not invent equipment, circuit elements or measurement procedures.
- Do not invent explanations for anomalies unless supported by the provided context.
- Do not generate tables, formulas or charts.
  They are generated separately by the backend.
- Do not use Markdown headings inside text fields.

PURPOSE

`purpose` should briefly describe:
- what was investigated,
- what quantities or characteristics were determined,
- the main purpose of the laboratory exercise.

Do not describe numerical results in the purpose.

SETUP DESCRIPTION

`setup_description` describes the tested circuit,
measurement setup or laboratory station.

This section is always present.

Use only information supported by the laboratory instruction.
If little information about the setup is available,
write a short description using only the known facts.
Do not invent missing equipment or connections.

THEORY

If report_specification.include_theory is false:
- theory must be null.

If include_theory is true:
- provide a concise theoretical background relevant to the exercise,
- prefer information contained in the laboratory instruction,
- do not add unrelated theoretical material.

SECTIONS

Return exactly one SectionTextContent for every ReportSection
in report_specification.sections.

section_id must exactly match the corresponding ReportSection.section_id.

DESCRIPTION

The section description should explain:
- what was measured,
- what was changed during the measurement,
- what quantities were determined or calculated.

Use past tense when describing performed measurements.

Do not analyze results in the description.

If include_description is false,
return an empty string for description.

ANALYSIS

Use the deterministic SectionAnalysis corresponding to the section.

The analysis should:
- describe relevant ranges and trends,
- distinguish overall direction from strict monotonicity,
- mention irregularities when monotonic is false,
- use actual values when useful,
- compare variables only when supported by the provided analysis.

Do not calculate new values.

Do not claim a cause of an irregularity unless the cause
is explicitly supported by the instruction.

If include_analysis is false,
return an empty string for analysis.

CONCLUSIONS

`conclusions` should summarize the most important findings
from the entire laboratory exercise.

Conclusions should:
- refer to the measured and calculated results,
- describe the most important observed relationships,
- be consistent with SectionAnalysis,
- avoid repeating every value from the tables,
- not introduce new calculations or unsupported explanations.

CONSISTENCY

Before returning the result ensure that:
- every report section appears exactly once,
- section_id values match the specification,
- theory is null when include_theory is false,
- all numerical claims are supported by SectionAnalysis,
- no equipment, formulas, results or experimental facts were invented.
"""

def generate_report_text(
    specification: ReportSpecification,
    analyses: list[SectionAnalysis],
    instruction: str,
) -> ReportTextContent:

    context = {
        "report_specification": specification.model_dump(),
        "section_analyses": [
            analysis.model_dump()
            for analysis in analyses
        ],
        "laboratory_instruction": instruction,
    }

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": REPORT_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    context,
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
        text_format=ReportTextContent,
    )

    result = response.output_parsed

    if result is None:
        raise ValueError(
            "Unable to generate complete report text."
        )

    return result