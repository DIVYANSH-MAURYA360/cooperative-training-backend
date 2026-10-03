from datetime import date, datetime, time
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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


class InstitutionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    institution_type: str = Field(default="ICM", pattern="^(NCCT|VAMNICOM|RICM|ICM|PARTNER)$")
    state: str
    district: str | None = None
    address: str = ""
    contact_email: EmailStr | None = None


class InstitutionOut(InstitutionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class TraineeProfileInput(BaseModel):
    state: str | None = None
    district: str | None = None
    education: str | None = None
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    bio: str = Field(default="", max_length=2000)
    career_interests: list[str] = Field(default_factory=list)
    biometric_consent: bool = False


class TraineeProfileOut(TraineeProfileInput):
    trainee_id: int
    updated_at: datetime


class NominationCreate(BaseModel):
    trainee_email: EmailStr
    trainee_name: str = Field(min_length=2, max_length=160)


class NominationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    program_id: int
    trainee_email: str
    trainee_name: str
    nominated_by: int
    status: str
    created_at: datetime


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(nominated|pending|approved|rejected|cancelled|submitted|shortlisted|interview|selected)$")


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    trainee_id: int
    enrolled_at: datetime
    completed_at: datetime | None


class ProgressInput(BaseModel):
    completed: bool = False
    last_position_seconds: int = Field(default=0, ge=0)


class ProgressOut(ProgressInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    trainee_id: int
    updated_at: datetime


class QuestionInput(BaseModel):
    prompt: str
    options: list[str] = Field(min_length=2)
    correct_option: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_answer(self):
        if self.correct_option >= len(self.options):
            raise ValueError("correct_option must reference an option")
        return self


class AssessmentCreate(BaseModel):
    title: str
    questions: list[QuestionInput] = Field(min_length=1)
    passing_percentage: float = Field(default=60, ge=0, le=100)
    max_attempts: int = Field(default=3, ge=1, le=20)
    is_published: bool = False


class AssessmentOut(BaseModel):
    id: int
    course_id: int
    title: str
    question_count: int
    passing_percentage: float
    max_attempts: int
    is_published: bool


class AttemptCreate(BaseModel):
    answers: list[int]


class AttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assessment_id: int
    trainee_id: int
    score: float
    passed: bool
    submitted_at: datetime


class TimetableCreate(BaseModel):
    session_date: date
    start_time: time
    end_time: time
    topic: str
    trainer_name: str = ""
    venue: str = ""

    @model_validator(mode="after")
    def valid_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class TimetableOut(TimetableCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    program_id: int


class HostelRoomCreate(BaseModel):
    institution: str
    room_number: str
    capacity: int = Field(default=2, ge=1, le=50)
    gender: str = Field(default="any", pattern="^(any|female|male)$")


class HostelRoomOut(HostelRoomCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class HostelAllocationCreate(BaseModel):
    room_id: int
    program_id: int
    trainee_id: int
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def valid_dates(self):
        if self.check_out < self.check_in:
            raise ValueError("check_out must be on or after check_in")
        return self


class HostelAllocationOut(HostelAllocationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str


class LogisticsCreate(BaseModel):
    program_id: int
    request_type: str = Field(pattern="^(transport|equipment|catering|accessibility|other)$")
    details: str = Field(min_length=2, max_length=2000)


class LogisticsOut(LogisticsCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    requested_by: int
    status: str
    created_at: datetime


class LogisticsStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|resolved|cancelled)$")


class QRTokenOut(BaseModel):
    token: str
    expires_in_seconds: int


class QRScanInput(BaseModel):
    token: str
    program_id: int


class CareerChatInput(BaseModel):
    message: str = Field(min_length=2, max_length=1000)
    language: str = Field(default="en", pattern="^(en|hi)$")


class CareerChatOut(BaseModel):
    reply: str
    suggested_actions: list[str]
    disclaimer: str


class OfflineProgressItem(BaseModel):
    lesson_id: int
    completed: bool = False
    last_position_seconds: int = Field(default=0, ge=0)
    client_updated_at: datetime | None = None


class OfflineSyncInput(BaseModel):
    progress: list[OfflineProgressItem] = Field(default_factory=list)


class OfflineSyncOut(BaseModel):
    accepted: int
    server_time: datetime
    conflicts: list[dict[str, Any]]


class DeviceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    serial_number: str = Field(min_length=4, max_length=100, pattern="^[A-Za-z0-9_-]+$")
    institution: str
    device_type: str = Field(default="qr_kiosk", pattern="^(qr_kiosk|face_terminal|hybrid_terminal)$")


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    serial_number: str
    institution: str
    device_type: str
    is_active: bool
    last_seen_at: datetime | None
    created_at: datetime


class DeviceCreatedOut(DeviceOut):
    api_key: str


class DeviceHeartbeatOut(BaseModel):
    status: str
    server_time: datetime


class DeviceAttendanceInput(BaseModel):
    program_id: int
    trainee_id: int
    method: str = Field(pattern="^(qr|face)$")
    confidence: float | None = Field(default=None, ge=0, le=1)
    captured_at: datetime | None = None


class RecommendationItem(BaseModel):
    id: int
    title: str
    score: int
    reasons: list[str]


class AIRecommendationsOut(BaseModel):
    profile_completeness: int
    course_recommendations: list[RecommendationItem]
    job_recommendations: list[RecommendationItem]
    next_best_actions: list[str]


class RiskItem(BaseModel):
    trainee_id: int
    trainee_name: str
    program_id: int
    program_title: str
    risk_score: int
    risk_level: str
    signals: list[str]


class AIRiskOut(BaseModel):
    generated_at: datetime
    total_reviewed: int
    high_risk: int
    medium_risk: int
    learners: list[RiskItem]
