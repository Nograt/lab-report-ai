from pydantic import BaseModel


class Subject(BaseModel):
    id: str

    name: str
    instructor_name: str

    department: str | None = None
    laboratory: str | None = None


class CreateSubject(BaseModel):
    name: str
    instructor_name: str

    department: str | None = None
    laboratory: str | None = None


class UpdateSubject(BaseModel):
    name: str | None = None
    instructor_name: str | None = None

    department: str | None = None
    laboratory: str | None = None