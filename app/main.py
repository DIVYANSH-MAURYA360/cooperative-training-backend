from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.aligned import router as aligned_router
from app.config import settings
from app.database import Base, engine, get_db
from app.dependencies import current_user, require_roles
from app.security import create_access_token, hash_password, verify_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Creates tables for a fresh local install. Use migrations for production updates.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Cooperative Training API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(aligned_router)
staff = Depends(require_roles("admin", "institution", "trainer"))


@app.get("/health")
def health():
    return {"status": "ok", "service": "cooperative-training-api"}


@app.post("/auth/register", response_model=schemas.UserOut, status_code=201)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(models.User).where(models.User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = models.User(full_name=data.full_name, email=email, password_hash=hash_password(data.password),
                       role="trainee", institution=data.institution, phone=data.phone)
    db.add(user); db.commit(); db.refresh(user)
    return user


@app.post("/auth/users", response_model=schemas.UserOut, status_code=201)
def create_staff(data: schemas.StaffCreate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("admin"))):
    email = data.email.lower()
    if db.scalar(select(models.User).where(models.User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    item = models.User(full_name=data.full_name, email=email, password_hash=hash_password(data.password),
                       role=data.role, institution=data.institution, phone=data.phone)
    db.add(item); db.commit(); db.refresh(item)
    return item


@app.post("/auth/login", response_model=schemas.Token)
def login(data: schemas.LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash) or not user.is_active:
        raise HTTPException(401, "Email or password is incorrect")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer"}


@app.get("/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(current_user)):
    return user


@app.get("/programs", response_model=list[schemas.ProgramOut])
def list_programs(skip: int = 0, limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db),
                  user: models.User = Depends(current_user)):
    query = select(models.Program).order_by(models.Program.start_date.desc()).offset(skip).limit(limit)
    if user.role == "trainee": query = query.where(models.Program.is_published.is_(True))
    return db.scalars(query).all()


@app.post("/programs", response_model=schemas.ProgramOut, status_code=201)
def create_program(data: schemas.ProgramCreate, db: Session = Depends(get_db), user: models.User = staff):
    if data.end_date < data.start_date: raise HTTPException(422, "End date must be on or after start date")
    item = models.Program(**data.model_dump(), created_by=user.id)
    db.add(item); db.commit(); db.refresh(item); return item


@app.post("/programs/{program_id}/register", response_model=schemas.RegistrationOut, status_code=201)
def register_program(program_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("trainee"))):
    program = db.get(models.Program, program_id)
    if not program or not program.is_published: raise HTTPException(404, "Published programme not found")
    if db.scalar(select(models.Registration).where(models.Registration.program_id == program_id,
                                                    models.Registration.trainee_id == user.id)):
        raise HTTPException(409, "You already registered for this programme")
    from sqlalchemy import func
    count = db.scalar(select(func.count()).select_from(models.Registration).where(models.Registration.program_id == program_id))
    if count >= program.capacity: raise HTTPException(409, "Programme capacity has been reached")
    item = models.Registration(program_id=program_id, trainee_id=user.id)
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/programs/{program_id}/registrations", response_model=list[schemas.RegistrationOut])
def registrations(program_id: int, db: Session = Depends(get_db), user: models.User = staff):
    return db.scalars(select(models.Registration).where(models.Registration.program_id == program_id).order_by(models.Registration.registered_at.desc())).all()


@app.post("/courses", response_model=schemas.CourseOut, status_code=201)
def create_course(data: schemas.CourseCreate, db: Session = Depends(get_db), user: models.User = staff):
    item = models.Course(**data.model_dump(), created_by=user.id)
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/courses", response_model=list[schemas.CourseOut])
def list_courses(db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    query = select(models.Course).order_by(models.Course.title)
    if user.role == "trainee": query = query.where(models.Course.is_published.is_(True))
    return db.scalars(query).all()


@app.post("/courses/{course_id}/lessons", response_model=schemas.LessonOut, status_code=201)
def create_lesson(course_id: int, data: schemas.LessonCreate, db: Session = Depends(get_db), user: models.User = staff):
    if not db.get(models.Course, course_id): raise HTTPException(404, "Course not found")
    item = models.Lesson(course_id=course_id, **data.model_dump())
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/courses/{course_id}/lessons", response_model=list[schemas.LessonOut])
def list_lessons(course_id: int, db: Session = Depends(get_db), user: models.User = Depends(current_user)):
    course = db.get(models.Course, course_id)
    if not course or (user.role == "trainee" and not course.is_published): raise HTTPException(404, "Course not found")
    return db.scalars(select(models.Lesson).where(models.Lesson.course_id == course_id).order_by(models.Lesson.sort_order)).all()


@app.post("/attendance", response_model=schemas.AttendanceOut, status_code=201)
def mark_attendance(data: schemas.AttendanceCreate, db: Session = Depends(get_db), user: models.User = staff):
    if data.method != "manual": raise HTTPException(422, "Use /attendance/scan for QR attendance")
    if not db.get(models.Program, data.program_id): raise HTTPException(404, "Programme not found")
    trainee = db.get(models.User, data.trainee_id)
    if not trainee or trainee.role != "trainee": raise HTTPException(404, "Trainee not found")
    item = models.Attendance(**data.model_dump())
    db.add(item)
    try: db.commit()
    except Exception:
        db.rollback(); raise HTTPException(409, "Attendance already recorded for this trainee and day")
    db.refresh(item); return item


@app.get("/attendance", response_model=list[schemas.AttendanceOut])
def list_attendance(program_id: int | None = None, trainee_id: int | None = None, db: Session = Depends(get_db), user: models.User = staff):
    query = select(models.Attendance).order_by(models.Attendance.session_date.desc())
    if program_id is not None: query = query.where(models.Attendance.program_id == program_id)
    if trainee_id is not None: query = query.where(models.Attendance.trainee_id == trainee_id)
    return db.scalars(query.limit(500)).all()


@app.post("/certificates", response_model=schemas.CertificateOut, status_code=201)
def issue_certificate(data: schemas.CertificateCreate, db: Session = Depends(get_db), user: models.User = staff):
    trainee = db.get(models.User, data.trainee_id)
    if not trainee or trainee.role != "trainee" or not db.get(models.Program, data.program_id): raise HTTPException(404, "Trainee or programme not found")
    registration = db.scalar(select(models.Registration).where(models.Registration.trainee_id == data.trainee_id,
                                                                 models.Registration.program_id == data.program_id,
                                                                 models.Registration.status == "approved"))
    if not registration: raise HTTPException(409, "Only an approved programme participant can be certified")
    if db.scalar(select(models.Certificate).where(models.Certificate.trainee_id == data.trainee_id,
                                                   models.Certificate.program_id == data.program_id)):
        raise HTTPException(409, "A certificate has already been issued for this trainee and programme")
    item = models.Certificate(trainee_id=data.trainee_id, program_id=data.program_id, certificate_code=uuid4().hex.upper())
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/certificates/verify/{code}", response_model=schemas.CertificateOut)
def verify_certificate(code: str, db: Session = Depends(get_db)):
    item = db.scalar(select(models.Certificate).where(models.Certificate.certificate_code == code.upper()))
    if not item: raise HTTPException(404, "Certificate code is not valid")
    return item


@app.post("/jobs", response_model=schemas.JobOut, status_code=201)
def create_job(data: schemas.JobCreate, db: Session = Depends(get_db), user: models.User = Depends(require_roles("employer", "admin"))):
    item = models.Job(**data.model_dump(), employer_id=user.id)
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/jobs", response_model=list[schemas.JobOut])
def list_jobs(skip: int = 0, limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    return db.scalars(select(models.Job).where(models.Job.is_active.is_(True)).order_by(models.Job.created_at.desc()).offset(skip).limit(limit)).all()


@app.post("/jobs/{job_id}/apply", response_model=schemas.ApplicationOut, status_code=201)
def apply_for_job(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("trainee"))):
    job = db.get(models.Job, job_id)
    if not job or not job.is_active: raise HTTPException(404, "Active job not found")
    if db.scalar(select(models.JobApplication).where(models.JobApplication.job_id == job_id, models.JobApplication.applicant_id == user.id)):
        raise HTTPException(409, "You already applied for this job")
    item = models.JobApplication(job_id=job_id, applicant_id=user.id)
    db.add(item); db.commit(); db.refresh(item); return item


@app.get("/my/applications", response_model=list[schemas.ApplicationOut])
def my_applications(db: Session = Depends(get_db), user: models.User = Depends(require_roles("trainee"))):
    return db.scalars(select(models.JobApplication).where(models.JobApplication.applicant_id == user.id).order_by(models.JobApplication.applied_at.desc())).all()


@app.get("/jobs/{job_id}/applications", response_model=list[schemas.ApplicationOut])
def job_applications(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_roles("employer", "admin"))):
    job = db.get(models.Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    if user.role != "admin" and job.employer_id != user.id: raise HTTPException(403, "You can only see applicants to your own jobs")
    return db.scalars(select(models.JobApplication).where(models.JobApplication.job_id == job_id).order_by(models.JobApplication.applied_at.desc())).all()


# Keep this mount last so API routes and /docs take precedence over the SPA shell.
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
