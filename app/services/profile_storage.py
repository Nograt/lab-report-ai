import json
from pathlib import Path

from app.schemas.profile import (
    UserProfile,
    UpdateUserProfile,
)


STORAGE_DIR = Path("storage")
PROFILE_PATH = STORAGE_DIR / "user_profile.json"


def save_user_profile(
    profile: UserProfile,
) -> UserProfile:

    STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

    PROFILE_PATH.write_text(
        json.dumps(
            profile.model_dump(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return profile


def load_user_profile() -> UserProfile | None:

    if not PROFILE_PATH.exists():
        return None

    data = json.loads(
        PROFILE_PATH.read_text(
            encoding="utf-8",
        )
    )

    return UserProfile.model_validate(
        data
    )


def update_user_profile(
    update: UpdateUserProfile,
) -> UserProfile:

    profile = load_user_profile()

    if profile is None:
        raise ValueError(
            "User profile has not been created."
        )

    updated_data = profile.model_dump()

    updated_data.update(
        update.model_dump(
            exclude_none=True
        )
    )

    updated_profile = (
        UserProfile.model_validate(
            updated_data
        )
    )

    return save_user_profile(
        updated_profile
    )