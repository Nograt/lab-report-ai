import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from app.core.openai_client import client


def upload_instruction_pdf(
    upload: UploadFile,
) -> str:

    filename = (
        upload.filename
        or "instruction.pdf"
    )

    if not filename.lower().endswith(".pdf"):
        raise ValueError(
            "Instruction file must be a PDF."
        )

    upload.file.seek(0)

    temp_path: Path | None = None

    try:
        with NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:

            shutil.copyfileobj(
                upload.file,
                temp_file,
            )

            temp_path = Path(
                temp_file.name
            )

        with temp_path.open("rb") as pdf_file:
            uploaded_file = client.files.create(
                file=pdf_file,
                purpose="user_data",
                expires_after={
                    "anchor": "created_at",
                    "seconds": 3600,
                },
            )

        return uploaded_file.id

    finally:
        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )


def delete_openai_file(
    file_id: str,
) -> None:

    try:
        client.files.delete(
            file_id
        )

    except Exception:
        pass