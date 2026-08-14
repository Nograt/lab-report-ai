import json
from pathlib import Path
from uuid import uuid4

from app.schemas.subject import (
    Subject,
    CreateSubject,
    UpdateSubject,
)


STORAGE_DIR = Path("storage")
SUBJECTS_PATH = STORAGE_DIR / "subjects.json"


def load_subjects() -> list[Subject]:

    if not SUBJECTS_PATH.exists():
        return []

    data = json.loads(
        SUBJECTS_PATH.read_text(
            encoding="utf-8",
        )
    )

    return [
        Subject.model_validate(item)
        for item in data
    ]


def save_subjects(
    subjects: list[Subject],
) -> None:

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SUBJECTS_PATH.write_text(
        json.dumps(
            [
                subject.model_dump()
                for subject in subjects
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_subject(
    subject_id: str,
) -> Subject | None:

    subjects = load_subjects()

    for subject in subjects:
        if subject.id == subject_id:
            return subject

    return None


def create_subject(
    data: CreateSubject,
) -> Subject:

    subject = Subject(
        id=uuid4().hex,
        **data.model_dump(),
    )

    subjects = load_subjects()

    subjects.append(subject)

    save_subjects(subjects)

    return subject


def update_subject(
    subject_id: str,
    update: UpdateSubject,
) -> Subject:

    subjects = load_subjects()

    for index, subject in enumerate(
        subjects
    ):
        if subject.id != subject_id:
            continue

        updated_data = (
            subject.model_dump()
        )

        updated_data.update(
            update.model_dump(
                exclude_none=True
            )
        )

        updated_subject = (
            Subject.model_validate(
                updated_data
            )
        )

        subjects[index] = updated_subject

        save_subjects(subjects)

        return updated_subject

    raise ValueError(
        "Subject not found."
    )


def delete_subject(
    subject_id: str,
) -> None:

    subjects = load_subjects()

    remaining_subjects = [
        subject
        for subject in subjects
        if subject.id != subject_id
    ]

    if len(remaining_subjects) == len(subjects):
        raise ValueError(
            "Subject not found."
        )

    save_subjects(
        remaining_subjects
    )