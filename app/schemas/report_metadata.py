from pydantic import BaseModel


class ProfileSnapshot(BaseModel):
    first_name: str
    last_name: str

    university: str
    faculty: str
    field_of_study: str

    semester: str
    group: str
    academic_year: str


class SubjectSnapshot(BaseModel):
    id: str

    name: str
    instructor_name: str

    department: str | None = None
    laboratory: str | None = None


class ReportMetadata(BaseModel):
    profile: ProfileSnapshot
    subject: SubjectSnapshot

    members: list[str]

    team: str
    execution_date: str