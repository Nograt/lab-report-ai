import json

from app.schemas.analysis import SectionAnalysis
from app.schemas.section import ReportSection
from app.schemas.report_text import SectionTextContent
from app.core.openai_client import client


MODEL = "gpt-5.6"


SYSTEM_PROMPT = """
You write parts of laboratory reports in Polish.

Generate text only from the information provided to you.

Do not invent:
- measurement values,
- equipment,
- formulas,
- experimental procedures,
- physical explanations unsupported by the provided context.

The writing style should be appropriate for a university engineering
laboratory report.

DESCRIPTION

The description explains what was measured or calculated in the section.

It should:
- be concise,
- describe the purpose and scope of the measurement stage,
- use past tense when describing performed measurements,
- not analyze results yet.

ANALYSIS

The analysis interprets the provided numerical results and chart analysis.

It should:
- refer to actual values when useful,
- describe overall trends,
- distinguish between overall direction and strict monotonicity,
- mention relevant irregularities,
- not claim perfect monotonic behavior when monotonic is false,
- not calculate new values,
- not invent causes for anomalies unless they are supported by context.

Return data strictly according to SectionTextContent.
"""

def generate_section_text(
    section: ReportSection,
    analysis: SectionAnalysis,
    instruction: str,
) -> SectionTextContent:

    context = {
        "section": section.model_dump(),
        "analysis": analysis.model_dump(),
        "laboratory_instruction": instruction,
    }

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": SYSTEM_PROMPT,
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
        text_format=SectionTextContent,
    )

    result = response.output_parsed

    if result is None:
        raise ValueError(
            "Unable to generate section text."
        )

    return result