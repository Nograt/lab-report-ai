from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas.subject import (
    Subject,
    CreateSubject,
    UpdateSubject,
)

from app.services.subject_storage import (
    load_subjects,
    get_subject,
    create_subject,
    update_subject,
    delete_subject,
)


router = APIRouter(
    prefix="/subjects",
    tags=["subjects"],
)


@router.get(
    "",
    response_model=list[Subject],
)
def get_subjects():
    return load_subjects()


@router.get(
    "/{subject_id}",
    response_model=Subject,
)
def get_single_subject(
    subject_id: str,
):

    subject = get_subject(
        subject_id
    )

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail="Subject not found.",
        )

    return subject


@router.post(
    "",
    response_model=Subject,
    status_code=201,
)
def post_subject(
    data: CreateSubject,
):
    return create_subject(
        data
    )


@router.patch(
    "/{subject_id}",
    response_model=Subject,
)
def patch_subject(
    subject_id: str,
    update: UpdateSubject,
):

    try:
        return update_subject(
            subject_id=subject_id,
            update=update,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.delete(
    "/{subject_id}",
    status_code=204,
)
def remove_subject(
    subject_id: str,
):

    try:
        delete_subject(
            subject_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )