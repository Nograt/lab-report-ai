from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    first_name: str
    last_name: str

    university: str
    faculty: str
    field_of_study: str

    semester: str
    group: str
    academic_year: str


class UpdateUserProfile(BaseModel):
    first_name: str | None = None
    last_name: str | None = None

    university: str | None = None
    faculty: str | None = None
    field_of_study: str | None = None

    semester: str | None = None
    group: str | None = None
    academic_year: str | None = None