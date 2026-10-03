"""ERP/LMS modules that map directly to the NCCT problem statement."""

import hashlib
import hmac
import json
import re
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.dependencies import current_user, require_roles

router = APIRouter()
staff_user = Depends(require_roles("admin", "institution", "trainer"))


def commit(db: Session, item, duplicate_message: str = "This record already exists"):
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, duplicate_message)
    db.refresh(item)
    return item


def csv_list(value: str) -> list[str]:
    return [part for part in value.split("|") if part]


def profile_out(item: models.TraineeProfile) -> dict:
    return {
        "trainee_id": item.trainee_id,
        "state": item.state,
        "district": item.district,
        "education": item.education,
        "skills": csv_list(item.skills),
        "languages": csv_list(item.languages),
        "bio": item.bio,
        "career_interests": csv_list(item.career_interests),
        "biometric_consent": item.biometric_consent,
        "updated_at": item.updated_at,
    }


@router.post("/institutions", response_model=schemas.InstitutionOut, status_code=201)
def create_institution(data: schemas.InstitutionCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin"))):
    return commit(db, models.Institution(**data.model_dump()), "An institution with this name already exists")


@router.get("/institutions", response_model=list[schemas.InstitutionOut])
def list_institutions(db: Session = Depends(get_db), _=Depends(current_user)):
    return db.scalars(select(models.Institution).where(models.Institution.is_active.is_(True)).order_by(models.Institution.name)).all()


@router.put("/profile/trainee", response_model=schemas.TraineeProfileOut)
def update_trainee_profile(data: schemas.TraineeProfileInput, db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    item = db.get(models.TraineeProfile, user.id) or models.TraineeProfile(trainee_id=user.id)
    values = data.model_dump(exclude={"skills", "languages", "career_interests"})
    for key, value in values.items():
        setattr(item, key, value)
    item.skills = "|".join(data.skills)
    item.languages = "|".join(data.languages)
    item.career_interests = "|".join(data.career_interests)
    item.updated_at = datetime.utcnow()
    db.add(item); db.commit(); db.refresh(item)
    return profile_out(item)


@router.get("/profile/trainee", response_model=schemas.TraineeProfileOut)
def get_trainee_profile(db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    item = db.get(models.TraineeProfile, user.id)
    if not item:
        raise HTTPException(404, "Trainee profile has not been completed")
    return profile_out(item)


@router.post("/programs/{program_id}/nominations", response_model=schemas.NominationOut, status_code=201)
def nominate(program_id: int, data: schemas.NominationCreate, db: Session = Depends(get_db), user=staff_user):
    if not db.get(models.Program, program_id):
        raise HTTPException(404, "Programme not found")
    item = models.Nomination(program_id=program_id, trainee_email=data.trainee_email.lower(),
                             trainee_name=data.trainee_name, nominated_by=user.id)
    return commit(db, item, "This person is already nominated for the programme")


@router.get("/programs/{program_id}/nominations", response_model=list[schemas.NominationOut])
def list_nominations(program_id: int, db: Session = Depends(get_db), _=staff_user):
    return db.scalars(select(models.Nomination).where(models.Nomination.program_id == program_id)
                      .order_by(models.Nomination.created_at.desc())).all()


@router.patch("/nominations/{nomination_id}", response_model=schemas.NominationOut)
def update_nomination(nomination_id: int, data: schemas.StatusUpdate, db: Session = Depends(get_db), _=staff_user):
    item = db.get(models.Nomination, nomination_id)
    if not item:
        raise HTTPException(404, "Nomination not found")
    item.status = data.status
    db.commit(); db.refresh(item)
    return item


@router.patch("/registrations/{registration_id}", response_model=schemas.RegistrationOut)
def update_registration(registration_id: int, data: schemas.StatusUpdate, db: Session = Depends(get_db), _=staff_user):
    if data.status not in {"pending", "approved", "rejected", "cancelled"}:
        raise HTTPException(422, "Unsupported registration status")
    item = db.get(models.Registration, registration_id)
    if not item:
        raise HTTPException(404, "Registration not found")
    item.status = data.status
    db.commit(); db.refresh(item)
    return item


@router.post("/courses/{course_id}/enroll", response_model=schemas.EnrollmentOut, status_code=201)
def enroll(course_id: int, db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    course = db.get(models.Course, course_id)
    if not course or not course.is_published:
        raise HTTPException(404, "Published course not found")
    return commit(db, models.CourseEnrollment(course_id=course_id, trainee_id=user.id), "Already enrolled in this course")


@router.get("/my/course-enrollments", response_model=list[schemas.EnrollmentOut])
def my_course_enrollments(db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    return db.scalars(select(models.CourseEnrollment).where(models.CourseEnrollment.trainee_id == user.id)
                      .order_by(models.CourseEnrollment.enrolled_at.desc())).all()


@router.put("/lessons/{lesson_id}/progress", response_model=schemas.ProgressOut)
def save_progress(lesson_id: int, data: schemas.ProgressInput, db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    enrolled = db.scalar(select(models.CourseEnrollment).where(models.CourseEnrollment.course_id == lesson.course_id,
                                                                 models.CourseEnrollment.trainee_id == user.id))
    if not enrolled:
        raise HTTPException(403, "Enroll in the course before recording progress")
    item = db.scalar(select(models.LessonProgress).where(models.LessonProgress.lesson_id == lesson_id,
                                                         models.LessonProgress.trainee_id == user.id))
    if not item:
        item = models.LessonProgress(lesson_id=lesson_id, trainee_id=user.id)
    item.completed = data.completed
    item.last_position_seconds = data.last_position_seconds
    item.updated_at = datetime.utcnow()
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.get("/courses/{course_id}/my-progress")
def course_progress(course_id: int, db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    lessons = db.scalars(select(models.Lesson).where(models.Lesson.course_id == course_id)).all()
    lesson_ids = [item.id for item in lessons]
    progress = [] if not lesson_ids else db.scalars(select(models.LessonProgress).where(
        models.LessonProgress.trainee_id == user.id, models.LessonProgress.lesson_id.in_(lesson_ids))).all()
    completed = sum(1 for item in progress if item.completed)
    return {"course_id": course_id, "total_lessons": len(lessons), "completed_lessons": completed,
            "completion_percentage": round(completed * 100 / len(lessons), 2) if lessons else 0,
            "items": [schemas.ProgressOut.model_validate(item) for item in progress]}


def assessment_out(item: models.Assessment) -> dict:
    return {"id": item.id, "course_id": item.course_id, "title": item.title,
            "question_count": len(json.loads(item.questions_json)), "passing_percentage": item.passing_percentage,
            "max_attempts": item.max_attempts, "is_published": item.is_published}


@router.post("/courses/{course_id}/assessments", response_model=schemas.AssessmentOut, status_code=201)
def create_assessment(course_id: int, data: schemas.AssessmentCreate, db: Session = Depends(get_db), _=staff_user):
    if not db.get(models.Course, course_id):
        raise HTTPException(404, "Course not found")
    item = models.Assessment(course_id=course_id, title=data.title,
        questions_json=json.dumps([q.model_dump() for q in data.questions]),
        passing_percentage=data.passing_percentage, max_attempts=data.max_attempts, is_published=data.is_published)
    db.add(item); db.commit(); db.refresh(item)
    return assessment_out(item)


@router.get("/courses/{course_id}/assessments", response_model=list[schemas.AssessmentOut])
def list_assessments(course_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    query = select(models.Assessment).where(models.Assessment.course_id == course_id)
    if user.role == "trainee":
        query = query.where(models.Assessment.is_published.is_(True))
    return [assessment_out(item) for item in db.scalars(query).all()]


@router.get("/assessments/{assessment_id}/questions")
def assessment_questions(assessment_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.get(models.Assessment, assessment_id)
    if not item or (user.role == "trainee" and not item.is_published):
        raise HTTPException(404, "Assessment not found")
    questions = json.loads(item.questions_json)
    return {"assessment_id": item.id, "title": item.title,
            "questions": [{"prompt": q["prompt"], "options": q["options"]} for q in questions]}


@router.post("/assessments/{assessment_id}/attempts", response_model=schemas.AttemptOut, status_code=201)
def submit_attempt(assessment_id: int, data: schemas.AttemptCreate, db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    item = db.get(models.Assessment, assessment_id)
    if not item or not item.is_published:
        raise HTTPException(404, "Published assessment not found")
    enrollment = db.scalar(select(models.CourseEnrollment).where(models.CourseEnrollment.course_id == item.course_id,
                                                                   models.CourseEnrollment.trainee_id == user.id))
    if not enrollment:
        raise HTTPException(403, "Enroll in the course before attempting its assessment")
    questions = json.loads(item.questions_json)
    if len(data.answers) != len(questions):
        raise HTTPException(422, "Submit exactly one answer for every question")
    attempts = db.scalar(select(func.count()).select_from(models.AssessmentAttempt).where(
        models.AssessmentAttempt.assessment_id == assessment_id, models.AssessmentAttempt.trainee_id == user.id))
    if attempts >= item.max_attempts:
        raise HTTPException(409, "Maximum attempts reached")
    correct = sum(answer == question["correct_option"] for answer, question in zip(data.answers, questions))
    score = round(correct * 100 / len(questions), 2)
    attempt = models.AssessmentAttempt(assessment_id=assessment_id, trainee_id=user.id,
        answers_json=json.dumps(data.answers), score=score, passed=score >= item.passing_percentage)
    db.add(attempt); db.commit(); db.refresh(attempt)
    return attempt


@router.get("/assessments/{assessment_id}/attempts", response_model=list[schemas.AttemptOut])
def assessment_attempts(assessment_id: int, db: Session = Depends(get_db), _=staff_user):
    if not db.get(models.Assessment, assessment_id):
        raise HTTPException(404, "Assessment not found")
    return db.scalars(select(models.AssessmentAttempt).where(models.AssessmentAttempt.assessment_id == assessment_id)
                      .order_by(models.AssessmentAttempt.submitted_at.desc())).all()


@router.get("/my/assessment-attempts", response_model=list[schemas.AttemptOut])
def my_assessment_attempts(db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    return db.scalars(select(models.AssessmentAttempt).where(models.AssessmentAttempt.trainee_id == user.id)
                      .order_by(models.AssessmentAttempt.submitted_at.desc())).all()


@router.post("/programs/{program_id}/timetable", response_model=schemas.TimetableOut, status_code=201)
def create_timetable(program_id: int, data: schemas.TimetableCreate, db: Session = Depends(get_db), _=staff_user):
    program = db.get(models.Program, program_id)
    if not program:
        raise HTTPException(404, "Programme not found")
    if not program.start_date <= data.session_date <= program.end_date:
        raise HTTPException(422, "Session date must fall within programme dates")
    return commit(db, models.TimetableSession(program_id=program_id, **data.model_dump()))


@router.get("/programs/{program_id}/timetable", response_model=list[schemas.TimetableOut])
def list_timetable(program_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    return db.scalars(select(models.TimetableSession).where(models.TimetableSession.program_id == program_id)
                      .order_by(models.TimetableSession.session_date, models.TimetableSession.start_time)).all()


@router.post("/hostel/rooms", response_model=schemas.HostelRoomOut, status_code=201)
def create_room(data: schemas.HostelRoomCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin", "institution"))):
    return commit(db, models.HostelRoom(**data.model_dump()), "This room already exists")


@router.get("/hostel/rooms", response_model=list[schemas.HostelRoomOut])
def list_rooms(institution: str | None = None, db: Session = Depends(get_db), _=staff_user):
    query = select(models.HostelRoom).where(models.HostelRoom.is_active.is_(True))
    if institution:
        query = query.where(models.HostelRoom.institution == institution)
    return db.scalars(query.order_by(models.HostelRoom.room_number)).all()


@router.post("/hostel/allocations", response_model=schemas.HostelAllocationOut, status_code=201)
def allocate_room(data: schemas.HostelAllocationCreate, db: Session = Depends(get_db), _=staff_user):
    room = db.get(models.HostelRoom, data.room_id)
    if not room or not room.is_active:
        raise HTTPException(404, "Active hostel room not found")
    trainee = db.get(models.User, data.trainee_id)
    if not db.get(models.Program, data.program_id) or not trainee or trainee.role != "trainee":
        raise HTTPException(404, "Programme or trainee not found")
    occupancy = db.scalar(select(func.count()).select_from(models.HostelAllocation).where(
        models.HostelAllocation.room_id == room.id, models.HostelAllocation.status == "allocated",
        models.HostelAllocation.check_in <= data.check_out, models.HostelAllocation.check_out >= data.check_in))
    if occupancy >= room.capacity:
        raise HTTPException(409, "Room is full for the selected dates")
    return commit(db, models.HostelAllocation(**data.model_dump()), "Trainee already has accommodation for this programme")


@router.get("/hostel/allocations", response_model=list[schemas.HostelAllocationOut])
def list_allocations(program_id: int | None = None, db: Session = Depends(get_db), _=staff_user):
    query = select(models.HostelAllocation)
    if program_id:
        query = query.where(models.HostelAllocation.program_id == program_id)
    return db.scalars(query.order_by(models.HostelAllocation.check_in)).all()


@router.post("/logistics", response_model=schemas.LogisticsOut, status_code=201)
def create_logistics(data: schemas.LogisticsCreate, db: Session = Depends(get_db), user=Depends(current_user)):
    if not db.get(models.Program, data.program_id):
        raise HTTPException(404, "Programme not found")
    if user.role == "trainee" and not db.scalar(select(models.Registration).where(
            models.Registration.program_id == data.program_id, models.Registration.trainee_id == user.id)):
        raise HTTPException(403, "Only a registered participant can request programme logistics")
    return commit(db, models.LogisticsRequest(**data.model_dump(), requested_by=user.id))


@router.get("/logistics", response_model=list[schemas.LogisticsOut])
def list_logistics(program_id: int | None = None, db: Session = Depends(get_db), user=Depends(current_user)):
    query = select(models.LogisticsRequest)
    if user.role == "trainee":
        query = query.where(models.LogisticsRequest.requested_by == user.id)
    if program_id:
        query = query.where(models.LogisticsRequest.program_id == program_id)
    return db.scalars(query.order_by(models.LogisticsRequest.created_at.desc())).all()


@router.patch("/logistics/{request_id}", response_model=schemas.LogisticsOut)
def update_logistics(request_id: int, data: schemas.LogisticsStatusUpdate, db: Session = Depends(get_db), _=staff_user):
    item = db.get(models.LogisticsRequest, request_id)
    if not item:
        raise HTTPException(404, "Logistics request not found")
    item.status = data.status
    db.commit(); db.refresh(item)
    return item


@router.get("/attendance/qr-token", response_model=schemas.QRTokenOut)
def attendance_qr_token(user=Depends(require_roles("trainee"))):
    expires = datetime.now(timezone.utc) + timedelta(minutes=2)
    token = jwt.encode({"sub": str(user.id), "purpose": "attendance", "exp": expires},
                       settings.secret_key, algorithm="HS256")
    return {"token": token, "expires_in_seconds": 120}


@router.post("/attendance/scan", response_model=schemas.AttendanceOut, status_code=201)
def scan_attendance(data: schemas.QRScanInput, db: Session = Depends(get_db), _=staff_user):
    try:
        payload = jwt.decode(data.token, settings.secret_key, algorithms=["HS256"])
        if payload.get("purpose") != "attendance":
            raise ValueError
        trainee_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid or expired attendance QR")
    registration = db.scalar(select(models.Registration).where(models.Registration.program_id == data.program_id,
        models.Registration.trainee_id == trainee_id, models.Registration.status.in_(["pending", "approved"])))
    if not registration:
        raise HTTPException(403, "Trainee is not registered for this programme")
    attendance = models.Attendance(program_id=data.program_id, trainee_id=trainee_id, session_date=date.today(), method="qr")
    return commit(db, attendance, "Attendance already recorded for this trainee and day")


@router.get("/analytics/overview")
def analytics_overview(db: Session = Depends(get_db), _=Depends(require_roles("admin", "institution"))):
    count = lambda model: db.scalar(select(func.count()).select_from(model)) or 0
    registrations = count(models.Registration)
    approved = db.scalar(select(func.count()).select_from(models.Registration).where(models.Registration.status == "approved")) or 0
    applications = count(models.JobApplication)
    selected = db.scalar(select(func.count()).select_from(models.JobApplication).where(models.JobApplication.status == "selected")) or 0
    attempts = count(models.AssessmentAttempt)
    passed = db.scalar(select(func.count()).select_from(models.AssessmentAttempt).where(models.AssessmentAttempt.passed.is_(True))) or 0
    return {"users": count(models.User), "programs": count(models.Program), "registrations": registrations,
            "registration_approval_rate": round(approved * 100 / registrations, 2) if registrations else 0,
            "courses": count(models.Course), "lesson_completions": db.scalar(select(func.count()).select_from(models.LessonProgress)
                .where(models.LessonProgress.completed.is_(True))) or 0,
            "assessment_pass_rate": round(passed * 100 / attempts, 2) if attempts else 0,
            "certificates": count(models.Certificate), "active_jobs": db.scalar(select(func.count()).select_from(models.Job)
                .where(models.Job.is_active.is_(True))) or 0, "job_applications": applications,
            "employment_conversion_rate": round(selected * 100 / applications, 2) if applications else 0}


@router.get("/analytics/programs/{program_id}")
def program_analytics(program_id: int, db: Session = Depends(get_db), _=staff_user):
    if not db.get(models.Program, program_id):
        raise HTTPException(404, "Programme not found")
    registered = db.scalar(select(func.count()).select_from(models.Registration).where(models.Registration.program_id == program_id)) or 0
    attendance_days = db.scalar(select(func.count()).select_from(models.Attendance).where(models.Attendance.program_id == program_id)) or 0
    certified = db.scalar(select(func.count()).select_from(models.Certificate).where(models.Certificate.program_id == program_id)) or 0
    return {"program_id": program_id, "registered": registered, "attendance_records": attendance_days,
            "certified": certified, "certification_rate": round(certified * 100 / registered, 2) if registered else 0}


@router.post("/career/chat", response_model=schemas.CareerChatOut)
def career_chat(data: schemas.CareerChatInput, user=Depends(require_roles("trainee"))):
    text = data.message.lower()
    if any(word in text for word in ("resume", "cv", "रिज्यूमे")):
        topic, actions = "Highlight verified certificates, practical projects, cooperative experience, and measurable outcomes.", ["Complete your trainee profile", "Add verified certificates", "Browse matching jobs"]
    elif any(word in text for word in ("interview", "साक्षात्कार")):
        topic, actions = "Prepare a short introduction, study the cooperative or employer, and answer with specific examples using Situation–Task–Action–Result.", ["Review the job description", "Practice five role-specific questions", "Prepare two questions for the recruiter"]
    elif any(word in text for word in ("course", "skill", "learn", "कोर्स", "कौशल")):
        topic, actions = "Choose learning based on your target role and current skill gap, then finish its assessment so the result is measurable.", ["Set career interests in your profile", "Browse published courses", "Complete an assessment"]
    else:
        topic, actions = "Start by naming your target role, education, location, and strongest skills. I can then suggest a learning and job-search plan.", ["Complete your trainee profile", "Choose a target role", "Browse current jobs"]
    if data.language == "hi":
        topic = "अपने लक्ष्य पद, शिक्षा, स्थान और प्रमुख कौशल बताइए। प्रोफ़ाइल, प्रमाणपत्र, कोर्स और उपलब्ध नौकरियों के आधार पर अगला कदम चुनें।"
        actions = ["प्रशिक्षु प्रोफ़ाइल पूरी करें", "उपयुक्त कोर्स देखें", "नौकरियाँ देखें"]
    return {"reply": topic, "suggested_actions": actions,
            "disclaimer": "Guidance is informational; verify eligibility and terms with the institution or employer."}


@router.post("/offline/sync", response_model=schemas.OfflineSyncOut)
def offline_sync(data: schemas.OfflineSyncInput, db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    accepted, conflicts = 0, []
    for incoming in data.progress:
        lesson = db.get(models.Lesson, incoming.lesson_id)
        if not lesson:
            conflicts.append({"lesson_id": incoming.lesson_id, "reason": "lesson_not_found"})
            continue
        enrolled = db.scalar(select(models.CourseEnrollment).where(models.CourseEnrollment.course_id == lesson.course_id,
            models.CourseEnrollment.trainee_id == user.id))
        if not enrolled:
            conflicts.append({"lesson_id": incoming.lesson_id, "reason": "not_enrolled"})
            continue
        item = db.scalar(select(models.LessonProgress).where(models.LessonProgress.lesson_id == incoming.lesson_id,
            models.LessonProgress.trainee_id == user.id)) or models.LessonProgress(lesson_id=incoming.lesson_id, trainee_id=user.id)
        if incoming.client_updated_at and item.id and item.updated_at.replace(tzinfo=timezone.utc) > incoming.client_updated_at.astimezone(timezone.utc):
            conflicts.append({"lesson_id": incoming.lesson_id, "reason": "server_version_newer"})
            continue
        item.completed = incoming.completed
        item.last_position_seconds = incoming.last_position_seconds
        item.updated_at = datetime.utcnow()
        db.add(item); accepted += 1
    db.commit()
    return {"accepted": accepted, "server_time": datetime.now(timezone.utc), "conflicts": conflicts}


def keywords(*values: str) -> set[str]:
    stop = {"and", "the", "for", "with", "from", "this", "that", "your", "you", "are", "india", "skill", "skills"}
    return {word for word in re.findall(r"[a-zA-Z]{3,}", " ".join(values).lower()) if word not in stop}


@router.get("/ai/recommendations", response_model=schemas.AIRecommendationsOut)
def ai_recommendations(db: Session = Depends(get_db), user=Depends(require_roles("trainee"))):
    profile = db.get(models.TraineeProfile, user.id)
    profile_terms = keywords(profile.skills if profile else "", profile.career_interests if profile else "",
                             profile.education or "" if profile else "")
    languages = {item.lower() for item in csv_list(profile.languages)} if profile else set()
    interests = csv_list(profile.career_interests) if profile else []

    course_items = []
    for course in db.scalars(select(models.Course).where(models.Course.is_published.is_(True))).all():
        overlap = profile_terms & keywords(course.title, course.description)
        score = min(98, 35 + len(overlap) * 15 + (12 if course.language.lower() in languages else 0))
        reasons = ([f"Matches {', '.join(sorted(overlap)[:3])}"] if overlap else ["Builds a complementary cooperative skill"])
        if course.language.lower() in languages:
            reasons.append(f"Available in {course.language}")
        course_items.append({"id": course.id, "title": course.title, "score": score, "reasons": reasons})

    job_items = []
    for job in db.scalars(select(models.Job).where(models.Job.is_active.is_(True))).all():
        overlap = profile_terms & keywords(job.title, job.description, job.organization)
        location_match = bool(profile and profile.state and profile.state.lower() in job.location.lower())
        score = min(98, 28 + len(overlap) * 17 + (15 if location_match else 0))
        reasons = ([f"Uses {', '.join(sorted(overlap)[:3])}"] if overlap else ["Relevant to cooperative-sector experience"])
        if location_match:
            reasons.append("Matches your preferred location")
        job_items.append({"id": job.id, "title": job.title, "score": score, "reasons": reasons})

    fields = [] if not profile else [profile.state, profile.district, profile.education, profile.skills,
                                     profile.languages, profile.bio, profile.career_interests]
    completeness = round(sum(bool(value) for value in fields) * 100 / 7) if fields else 0
    actions = []
    if completeness < 80:
        actions.append("Complete your profile to improve recommendation quality")
    if not interests:
        actions.append("Add at least one career interest")
    if not db.scalar(select(models.Certificate).where(models.Certificate.trainee_id == user.id)):
        actions.append("Complete a programme to earn a verified certificate")
    if not actions:
        actions.append("Apply to your highest-matched active opportunity")
    return {"profile_completeness": completeness,
            "course_recommendations": sorted(course_items, key=lambda x: x["score"], reverse=True)[:5],
            "job_recommendations": sorted(job_items, key=lambda x: x["score"], reverse=True)[:5],
            "next_best_actions": actions}


@router.get("/ai/risk-insights", response_model=schemas.AIRiskOut)
def ai_risk_insights(db: Session = Depends(get_db), _=Depends(require_roles("admin", "institution", "trainer"))):
    results = []
    registrations = db.scalars(select(models.Registration).where(
        models.Registration.status.in_(["pending", "approved"]))).all()
    for registration in registrations:
        trainee = db.get(models.User, registration.trainee_id)
        program = db.get(models.Program, registration.program_id)
        if not trainee or not program:
            continue
        score, signals = 0, []
        if registration.status == "pending":
            score += 25; signals.append("Registration is still pending")
        attendance_count = db.scalar(select(func.count()).select_from(models.Attendance).where(
            models.Attendance.program_id == program.id, models.Attendance.trainee_id == trainee.id)) or 0
        sessions = db.scalar(select(func.count()).select_from(models.TimetableSession).where(
            models.TimetableSession.program_id == program.id,
            models.TimetableSession.session_date <= date.today())) or 0
        if sessions and attendance_count == 0:
            score += 50; signals.append("No attendance recorded for scheduled sessions")
        elif sessions and attendance_count / sessions < .6:
            score += 35; signals.append("Attendance is below 60%")
        certificate = db.scalar(select(models.Certificate).where(models.Certificate.program_id == program.id,
                                                                   models.Certificate.trainee_id == trainee.id))
        if program.end_date < date.today() and not certificate:
            score += 25; signals.append("Programme ended without certification")
        score = min(score, 100)
        level = "high" if score >= 60 else "medium" if score >= 30 else "low"
        results.append({"trainee_id": trainee.id, "trainee_name": trainee.full_name, "program_id": program.id,
                        "program_title": program.title, "risk_score": score, "risk_level": level,
                        "signals": signals or ["No immediate risk signals"]})
    ordered = sorted(results, key=lambda x: x["risk_score"], reverse=True)
    return {"generated_at": datetime.now(timezone.utc), "total_reviewed": len(ordered),
            "high_risk": sum(item["risk_level"] == "high" for item in ordered),
            "medium_risk": sum(item["risk_level"] == "medium" for item in ordered), "learners": ordered}


def device_for_request(serial: str, key: str, db: Session) -> models.AttendanceDevice:
    device = db.scalar(select(models.AttendanceDevice).where(models.AttendanceDevice.serial_number == serial))
    supplied = hashlib.sha256(key.encode()).hexdigest()
    if not device or not device.is_active or not hmac.compare_digest(supplied, device.api_key_hash):
        raise HTTPException(401, "Invalid or inactive attendance device")
    return device


@router.post("/devices", response_model=schemas.DeviceCreatedOut, status_code=201)
def register_device(data: schemas.DeviceCreate, db: Session = Depends(get_db), _=Depends(require_roles("admin", "institution"))):
    raw_key = secrets.token_urlsafe(32)
    item = models.AttendanceDevice(**data.model_dump(), api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest())
    commit(db, item, "A device with this serial number already exists")
    return {**schemas.DeviceOut.model_validate(item).model_dump(), "api_key": raw_key}


@router.get("/devices", response_model=list[schemas.DeviceOut])
def list_devices(db: Session = Depends(get_db), _=Depends(require_roles("admin", "institution", "trainer"))):
    return db.scalars(select(models.AttendanceDevice).order_by(models.AttendanceDevice.created_at.desc())).all()


@router.post("/devices/heartbeat", response_model=schemas.DeviceHeartbeatOut)
def device_heartbeat(x_device_serial: str = Header(alias="X-Device-Serial"),
                     x_device_key: str = Header(alias="X-Device-Key"), db: Session = Depends(get_db)):
    device = device_for_request(x_device_serial, x_device_key, db)
    device.last_seen_at = datetime.utcnow()
    db.add(models.DeviceEvent(device_id=device.id, event_type="heartbeat", payload_json="{}"))
    db.commit()
    return {"status": "online", "server_time": datetime.now(timezone.utc)}


@router.post("/devices/attendance", response_model=schemas.AttendanceOut, status_code=201)
def device_attendance(data: schemas.DeviceAttendanceInput, x_device_serial: str = Header(alias="X-Device-Serial"),
                      x_device_key: str = Header(alias="X-Device-Key"), db: Session = Depends(get_db)):
    device = device_for_request(x_device_serial, x_device_key, db)
    if data.method == "face" and device.device_type not in {"face_terminal", "hybrid_terminal"}:
        raise HTTPException(403, "This device is not approved for face attendance")
    registration = db.scalar(select(models.Registration).where(models.Registration.program_id == data.program_id,
        models.Registration.trainee_id == data.trainee_id, models.Registration.status == "approved"))
    if not registration:
        raise HTTPException(403, "Trainee does not have an approved programme registration")
    if data.method == "face":
        profile = db.get(models.TraineeProfile, data.trainee_id)
        if not profile or not profile.biometric_consent:
            raise HTTPException(403, "Biometric consent is required; use QR as the alternative")
        if data.confidence is None or data.confidence < .80:
            raise HTTPException(422, "Face-match confidence must be at least 0.80")
    attendance = models.Attendance(program_id=data.program_id, trainee_id=data.trainee_id,
                                   session_date=(data.captured_at.date() if data.captured_at else date.today()), method=data.method)
    event = models.DeviceEvent(device_id=device.id, event_type=f"attendance_{data.method}",
        payload_json=json.dumps({"program_id": data.program_id, "trainee_id": data.trainee_id,
                                 "confidence": data.confidence}), status="accepted")
    device.last_seen_at = datetime.utcnow()
    db.add_all([attendance, event])
    try:
        db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "Attendance already recorded for this trainee and day")
    db.refresh(attendance)
    return attendance


@router.get("/devices/events")
def device_events(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), _=Depends(require_roles("admin", "institution"))):
    events = db.scalars(select(models.DeviceEvent).order_by(models.DeviceEvent.received_at.desc()).limit(limit)).all()
    return [{"id": item.id, "device_id": item.device_id, "event_type": item.event_type,
             "status": item.status, "received_at": item.received_at} for item in events]


@router.patch("/job-applications/{application_id}", response_model=schemas.ApplicationOut)
def update_application(application_id: int, data: schemas.StatusUpdate, db: Session = Depends(get_db), user=Depends(require_roles("employer", "admin"))):
    if data.status not in {"submitted", "shortlisted", "interview", "selected", "rejected"}:
        raise HTTPException(422, "Unsupported application status")
    item = db.get(models.JobApplication, application_id)
    if not item:
        raise HTTPException(404, "Application not found")
    job = db.get(models.Job, item.job_id)
    if user.role != "admin" and job.employer_id != user.id:
        raise HTTPException(403, "You can only update applicants to your own jobs")
    item.status = data.status
    db.commit(); db.refresh(item)
    return item
