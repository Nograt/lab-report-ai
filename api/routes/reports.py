from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from app.services.instruction_parser import parse_report_instruction


router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/analyze")
async def analyze_report(instruction: Annotated[str, Form()], measurements: Annotated[UploadFile, File()]):
   
    specification = parse_report_instruction(instruction)
   
   
    return {
        "filename": measurements.filename,
        "content_type": measurements.content_type,
        "specification": specification.model_dump(),
    }