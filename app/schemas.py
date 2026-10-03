from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    institution: str | None = None
    phone: str | None = None


class StaffCreate(UserCreate):
    role: str = Field(pattern="^(admin|institution|trainer|employer)$")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str
    role: str
    institution: str | None
    phone: str | None
    is_active: bool
    created_at: datetime


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProgramCreate(BaseModel):
    title: str
    description: str = ""
    institution: str
    location: str = "Online"
    start_date: date
    end_date: date
    capacity: int = Field(default=100, ge=1)
    is_published: bool = False


class ProgramOut(ProgramCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int


class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    program_id: int
    trainee_id: int
    status: str
    registered_at: datetime


class CourseCreate(BaseModel):
    title: str
    description: str = ""
    language: str = "English"
    is_published: bool = False


class CourseOut(CourseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int


class LessonCreate(BaseModel):
    title: str
    content: str = ""
    sort_order: int = 1


class LessonOut(LessonCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int


class AttendanceCreate(BaseModel):
    program_id: int
    trainee_id: int
    session_date: date = Field(default_factory=date.today)
    method: str = "manual"


class AttendanceOut(AttendanceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    marked_at: datetime


class JobCreate(BaseModel):
    title: str
    organization: str
    description: str
    location: str = "India"


class JobOut(JobCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employer_id: int
    is_active: bool
    created_at: datetime


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    applicant_id: int
    status: str
    applied_at: datetime


class CertificateCreate(BaseModel):
    trainee_id: int
    program_id: int


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trainee_id: int
    program_id: int
    certificate_code: str
    issued_at: datetime
