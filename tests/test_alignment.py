import os

os.environ["DATABASE_URL"] = "sqlite:///./test_cooperative_training.db"

from fastapi.testclient import TestClient

from app import models
from app.database import Base, SessionLocal, engine
from app.main import app
from app.security import hash_password


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_ncct_erp_lms_employment_flow():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add(models.User(full_name="NCCT Admin", email="admin@example.org",
                           password_hash=hash_password("StrongPass123!"), role="admin"))
        db.commit()

    with TestClient(app) as client:
        homepage = client.get("/")
        assert homepage.status_code == 200 and "SahakarSetu" in homepage.text
        assert client.get("/docs").status_code == 200
        admin = login(client, "admin@example.org", "StrongPass123!")
        response = client.post("/auth/register", json={
            "full_name": "Rural Trainee", "email": "trainee@example.org", "password": "StrongPass123!"
        })
        assert response.status_code == 201, response.text
        trainee_id = response.json()["id"]
        trainee = login(client, "trainee@example.org", "StrongPass123!")

        response = client.post("/institutions", headers=auth(admin), json={
            "name": "RICM Test Centre", "institution_type": "RICM", "state": "Uttar Pradesh"
        })
        assert response.status_code == 201, response.text

        response = client.put("/profile/trainee", headers=auth(trainee), json={
            "state": "Uttar Pradesh", "skills": ["digital literacy"], "languages": ["Hindi"],
            "career_interests": ["cooperative banking"], "biometric_consent": False
        })
        assert response.status_code == 200, response.text
        assert response.json()["skills"] == ["digital literacy"]

        response = client.post("/programs", headers=auth(admin), json={
            "title": "PACS Digital Operations", "institution": "RICM Test Centre", "location": "Lucknow",
            "start_date": "2026-10-01", "end_date": "2026-10-10", "capacity": 30, "is_published": True
        })
        assert response.status_code == 201, response.text
        program_id = response.json()["id"]

        response = client.post(f"/programs/{program_id}/register", headers=auth(trainee))
        assert response.status_code == 201, response.text
        registration_id = response.json()["id"]
        response = client.patch(f"/registrations/{registration_id}", headers=auth(admin), json={"status": "approved"})
        assert response.status_code == 200, response.text

        response = client.post(f"/programs/{program_id}/nominations", headers=auth(admin), json={
            "trainee_email": "nominee@example.org", "trainee_name": "Nominated Learner"
        })
        assert response.status_code == 201, response.text

        response = client.post("/courses", headers=auth(admin), json={
            "title": "Digital Cooperative Basics", "language": "Hindi", "is_published": True
        })
        assert response.status_code == 201, response.text
        course_id = response.json()["id"]
        response = client.post(f"/courses/{course_id}/lessons", headers=auth(admin), json={
            "title": "UPI Safety", "content": "Interactive lesson", "sort_order": 1
        })
        assert response.status_code == 201, response.text
        lesson_id = response.json()["id"]
        assert client.post(f"/courses/{course_id}/enroll", headers=auth(trainee)).status_code == 201
        enrollments = client.get("/my/course-enrollments", headers=auth(trainee))
        assert enrollments.status_code == 200 and enrollments.json()[0]["course_id"] == course_id
        response = client.put(f"/lessons/{lesson_id}/progress", headers=auth(trainee), json={
            "completed": True, "last_position_seconds": 90
        })
        assert response.status_code == 200, response.text

        response = client.post(f"/courses/{course_id}/assessments", headers=auth(admin), json={
            "title": "Safety Check", "questions": [{
                "prompt": "Should an OTP be shared?", "options": ["Yes", "No"], "correct_option": 1
            }], "passing_percentage": 60, "is_published": True
        })
        assert response.status_code == 201, response.text
        assessment_id = response.json()["id"]
        recommendations = client.get("/ai/recommendations", headers=auth(trainee))
        assert recommendations.status_code == 200, recommendations.text
        assert recommendations.json()["course_recommendations"][0]["id"] == course_id
        questions = client.get(f"/assessments/{assessment_id}/questions", headers=auth(trainee)).json()
        assert "correct_option" not in questions["questions"][0]
        response = client.post(f"/assessments/{assessment_id}/attempts", headers=auth(trainee), json={"answers": [1]})
        assert response.status_code == 201, response.text
        assert response.json()["passed"] is True
        assert client.get("/my/assessment-attempts", headers=auth(trainee)).json()[0]["score"] == 100
        assert client.get(f"/assessments/{assessment_id}/attempts", headers=auth(admin)).status_code == 200

        response = client.post(f"/programs/{program_id}/timetable", headers=auth(admin), json={
            "session_date": "2026-10-04", "start_time": "10:00", "end_time": "11:00",
            "topic": "Digital Payments", "trainer_name": "Trainer", "venue": "Lab 1"
        })
        assert response.status_code == 201, response.text

        response = client.post("/hostel/rooms", headers=auth(admin), json={
            "institution": "RICM Test Centre", "room_number": "A-101", "capacity": 2, "gender": "any"
        })
        assert response.status_code == 201, response.text
        room_id = response.json()["id"]
        response = client.post("/hostel/allocations", headers=auth(admin), json={
            "room_id": room_id, "program_id": program_id, "trainee_id": trainee_id,
            "check_in": "2026-10-01", "check_out": "2026-10-10"
        })
        assert response.status_code == 201, response.text

        response = client.post("/logistics", headers=auth(trainee), json={
            "program_id": program_id, "request_type": "accessibility", "details": "Ground-floor room required"
        })
        assert response.status_code == 201, response.text
        logistics_id = response.json()["id"]
        response = client.patch(f"/logistics/{logistics_id}", headers=auth(admin), json={"status": "resolved"})
        assert response.status_code == 200 and response.json()["status"] == "resolved"

        qr = client.get("/attendance/qr-token", headers=auth(trainee)).json()["token"]
        insecure = client.post("/attendance", headers=auth(admin), json={
            "program_id": program_id, "trainee_id": trainee_id, "session_date": "2026-10-04", "method": "qr"
        })
        assert insecure.status_code == 422
        response = client.post("/attendance/scan", headers=auth(admin), json={"token": qr, "program_id": program_id})
        assert response.status_code == 201, response.text
        assert response.json()["method"] == "qr"

        response = client.post("/certificates", headers=auth(admin), json={
            "trainee_id": trainee_id, "program_id": program_id
        })
        assert response.status_code == 201, response.text
        certificate_code = response.json()["certificate_code"]
        assert client.get(f"/certificates/verify/{certificate_code}").status_code == 200

        response = client.post("/offline/sync", headers=auth(trainee), json={
            "progress": [{"lesson_id": lesson_id, "completed": True, "last_position_seconds": 120}]
        })
        assert response.status_code == 200, response.text
        assert response.json()["accepted"] == 1

        response = client.post("/career/chat", headers=auth(trainee), json={"message": "Help with my resume", "language": "en"})
        assert response.status_code == 200, response.text
        assert response.json()["suggested_actions"]

        response = client.get("/analytics/overview", headers=auth(admin))
        assert response.status_code == 200, response.text
        assert response.json()["users"] == 2

        risk = client.get("/ai/risk-insights", headers=auth(admin))
        assert risk.status_code == 200 and risk.json()["total_reviewed"] == 1

        response = client.post("/devices", headers=auth(admin), json={
            "name": "Gate QR Kiosk", "serial_number": "RICM-QR-001",
            "institution": "RICM Test Centre", "device_type": "qr_kiosk"
        })
        assert response.status_code == 201, response.text
        device_key = response.json()["api_key"]
        device_headers = {"X-Device-Serial": "RICM-QR-001", "X-Device-Key": device_key}
        assert client.post("/devices/heartbeat", headers=device_headers).status_code == 200
        response = client.post("/devices/attendance", headers=device_headers, json={
            "program_id": program_id, "trainee_id": trainee_id, "method": "qr",
            "captured_at": "2026-10-05T10:00:00Z"
        })
        assert response.status_code == 201, response.text
        events = client.get("/devices/events", headers=auth(admin))
        assert events.status_code == 200 and len(events.json()) == 2
