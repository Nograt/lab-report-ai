from fastapi import (
    APIRouter,
    HTTPException,
)

from app.schemas.profile import (
    UserProfile,
    UpdateUserProfile,
)

from app.services.profile_storage import (
    load_user_profile,
    save_user_profile,
    update_user_profile,
)


router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)


@router.get(
    "",
    response_model=UserProfile,
)
def get_profile():

    profile = load_user_profile()

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="User profile not found.",
        )

    return profile


@router.put(
    "",
    response_model=UserProfile,
)
def create_or_replace_profile(
    profile: UserProfile,
):
    return save_user_profile(
        profile
    )


@router.patch(
    "",
    response_model=UserProfile,
)
def patch_profile(
    update: UpdateUserProfile,
):

    try:
        return update_user_profile(
            update
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )