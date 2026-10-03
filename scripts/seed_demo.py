"""Idempotently add realistic SIH demonstration data without creating known passwords."""

import json
import hashlib
import secrets
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import (Assessment, Attendance, AttendanceDevice, Course, DeviceEvent, Institution,
                        Job, Lesson, Program, Registration, TimetableSession, TraineeProfile, User)
from app.security import hash_password


Base.metadata.create_all(bind=engine)
db = SessionLocal()


def one(model, **where):
    query = select(model)
    for key, value in where.items():
        query = query.where(getattr(model, key) == value)
    return db.scalar(query)


def demo_user(name, email, role="trainee"):
    item = one(User, email=email)
    if not item:
        item = User(full_name=name, email=email, role=role,
                    password_hash=hash_password(secrets.token_urlsafe(28)), is_active=True)
        db.add(item); db.flush()
    return item


try:
    admin = db.scalar(select(User).where(User.role == "admin", User.is_active.is_(True)))
    if not admin:
        raise SystemExit("Create an administrator before seeding demo data.")

    if not one(Institution, name="RICM Lucknow"):
        db.add(Institution(name="RICM Lucknow", institution_type="RICM", state="Uttar Pradesh",
                           district="Lucknow", address="Cooperative Training Campus"))
    if not one(Institution, name="ICM Dehradun"):
        db.add(Institution(name="ICM Dehradun", institution_type="ICM", state="Uttarakhand",
                           district="Dehradun", address="Regional Cooperative Campus"))

    programme_specs = [
        ("PACS Digital Transformation Bootcamp", "RICM Lucknow", "Lucknow", -2, 8, 80,
         "Hands-on digital operations, cyber safety, UPI and member-service transformation."),
        ("Dairy Cooperative Leadership Programme", "ICM Dehradun", "Dehradun", 12, 20, 60,
         "Governance, value-chain planning and quality systems for dairy cooperatives."),
        ("SHG Entrepreneurship Accelerator", "RICM Lucknow", "Hybrid", 28, 40, 120,
         "Market readiness, financial literacy and digital commerce for women-led SHGs."),
    ]
    programmes = []
    for title, institution, location, start, end, capacity, description in programme_specs:
        item = one(Program, title=title)
        if not item:
            item = Program(title=title, institution=institution, location=location,
                start_date=date.today()+timedelta(days=start), end_date=date.today()+timedelta(days=end),
                capacity=capacity, description=description, is_published=True, created_by=admin.id)
            db.add(item); db.flush()
        programmes.append(item)

    course_specs = [
        ("Digital Banking & Cyber Safety", "Hindi", "UPI, fraud prevention and secure digital member services",
         [("Safe UPI Operations", "Interactive scenarios for safe transactions."), ("Fraud Red Flags", "Recognize social engineering and escalation paths.")]),
        ("Cooperative Governance Essentials", "English", "Boards, compliance, democratic governance and member value",
         [("Governance Foundations", "Roles, responsibilities and member accountability."), ("Transparent Reporting", "Practical reporting and audit readiness.")]),
        ("Rural Enterprise & Market Linkage", "Hindi", "Business models, pricing, digital commerce and buyer discovery",
         [("Build a Viable Offer", "Turn local capability into a market-ready offer."), ("Digital Market Access", "Use trusted channels to reach buyers.")]),
    ]
    courses = []
    for title, language, description, lessons in course_specs:
        course = one(Course, title=title)
        if not course:
            course = Course(title=title, language=language, description=description, is_published=True, created_by=admin.id)
            db.add(course); db.flush()
        for order, (lesson_title, content) in enumerate(lessons, 1):
            if not one(Lesson, course_id=course.id, title=lesson_title):
                db.add(Lesson(course_id=course.id, title=lesson_title, content=content, sort_order=order))
        courses.append(course)

    if not one(Assessment, course_id=courses[0].id, title="Digital Safety Readiness Check"):
        questions = [{"prompt":"Should an OTP ever be shared?","options":["Yes","No"],"correct_option":1},
                     {"prompt":"What should follow a suspicious transaction?","options":["Ignore it","Use the escalation process"],"correct_option":1}]
        db.add(Assessment(course_id=courses[0].id, title="Digital Safety Readiness Check",
                          questions_json=json.dumps(questions), passing_percentage=60, max_attempts=3, is_published=True))

    employer = demo_user("Sahakar Rural Careers", "demo-employer@sahakarsetu.invalid", "employer")
    for title, org, location, description in [
        ("PACS Digital Operations Associate", "Sahakar Rural Careers", "Uttar Pradesh", "Support digital member services, records and secure payments."),
        ("Dairy Cooperative Field Coordinator", "Milk Union Network", "Uttarakhand", "Coordinate producer outreach, quality practices and field reporting."),
    ]:
        if not one(Job, title=title):
            db.add(Job(employer_id=employer.id, title=title, organization=org, location=location,
                       description=description, is_active=True))

    trainees = [
        demo_user("Meera Devi", "demo-meera@sahakarsetu.invalid"),
        demo_user("Ravi Kumar", "demo-ravi@sahakarsetu.invalid"),
        demo_user("Sana Parveen", "demo-sana@sahakarsetu.invalid"),
    ]
    profiles = [
        (trainees[0], "Uttar Pradesh", "digital literacy|banking", "Hindi|English", "PACS operations|digital banking"),
        (trainees[1], "Uttarakhand", "dairy farming|field operations", "Hindi", "dairy cooperative|field coordination"),
        (trainees[2], "Uttar Pradesh", "entrepreneurship|ecommerce", "Hindi|English", "SHG enterprise|digital market"),
    ]
    for trainee, state, skills, languages, interests in profiles:
        if not db.get(TraineeProfile, trainee.id):
            db.add(TraineeProfile(trainee_id=trainee.id, state=state, education="Graduate",
                skills=skills, languages=languages, career_interests=interests, bio="Rural cooperative learner"))
        if not one(Registration, program_id=programmes[0].id, trainee_id=trainee.id):
            db.add(Registration(program_id=programmes[0].id, trainee_id=trainee.id,
                                status="approved" if trainee != trainees[2] else "pending"))

    for day, topic in [(date.today()-timedelta(days=1), "Digital Cooperative Foundations"),
                       (date.today(), "Safe Digital Payments")]:
        if not one(TimetableSession, program_id=programmes[0].id, session_date=day, topic=topic):
            db.add(TimetableSession(program_id=programmes[0].id, session_date=day, start_time=time(10),
                end_time=time(12), topic=topic, trainer_name="NCCT Digital Faculty", venue="Smart Lab"))
    if not one(Attendance, program_id=programmes[0].id, trainee_id=trainees[0].id, session_date=date.today()-timedelta(days=1)):
        db.add(Attendance(program_id=programmes[0].id, trainee_id=trainees[0].id,
                          session_date=date.today()-timedelta(days=1), method="qr"))

    device = one(AttendanceDevice, serial_number="RICM-HYBRID-DEMO")
    if not device:
        device = AttendanceDevice(name="RICM Gate Hybrid Terminal", serial_number="RICM-HYBRID-DEMO",
            institution="RICM Lucknow", device_type="hybrid_terminal",
            api_key_hash=hashlib.sha256(secrets.token_urlsafe(32).encode()).hexdigest(),
            last_seen_at=datetime.utcnow())
        db.add(device); db.flush()
        db.add(DeviceEvent(device_id=device.id, event_type="heartbeat", payload_json="{}", status="accepted"))

    db.commit()
    print("SIH demo data is ready. Synthetic demo accounts have random unknown passwords.")
finally:
    db.close()
