# Cooperative Training API

Backend for SIH problem statement 26087: cooperative training ERP, LMS, analytics, attendance, certification, logistics, career support, and employment exchange.

The evidence-based feature audit is in [ALIGNMENT_REPORT.md](ALIGNMENT_REPORT.md). The backend is currently assessed at **90/100 alignment**; the report separates working API capability from hardware/mobile/infrastructure work that still requires integration.

The post-hardening external-round assessment, scoring evidence and seven-minute judge flow are in [EXTERNAL_EVALUATION.md](EXTERNAL_EVALUATION.md). Presentation-ready opening, problem–solution narrative, differentiators and judge answers are in [PITCH_GUIDE.md](PITCH_GUIDE.md). Run `python scripts/seed_demo.py` after creating an administrator to load realistic, idempotent demonstration data; demo identities receive random unknown passwords.


The default database is SQLite and the database file is created automatically. To use PostgreSQL, set `DATABASE_URL` in `.env`, for example `postgresql+psycopg://user:password@localhost:5432/cooperative_training`. The web client uses the live API at `http://127.0.0.1:8000` by default.

## Roles

The supported account roles are `admin`, `institution`, `trainer`, `trainee`, and `employer`. Public signup only permits trainee accounts. Create the initial admin with the script above; that admin can provision trusted staff and employers with `POST /auth/users`. Do not let public signup forms choose a privileged role.

## API outline

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET/POST /programs`, `POST /programs/{id}/register`, `GET /programs/{id}/registrations`
- `GET/POST /courses`, `POST /courses/{id}/lessons`, `GET /courses/{id}/lessons`
- `POST /attendance`, `GET /attendance`
- `POST /certificates`, `GET /certificates/verify/{code}`
- `GET/POST /jobs`, `POST /jobs/{id}/apply`, `GET /jobs/{id}/applications`
- `GET /my/applications`
- `GET/POST /institutions`, `GET/PUT /profile/trainee`
- `GET/POST /programs/{id}/nominations`, `PATCH /registrations/{id}`
- `POST /courses/{id}/enroll`, `PUT /lessons/{id}/progress`, `GET /courses/{id}/my-progress`
- `GET/POST /courses/{id}/assessments`, `POST /assessments/{id}/attempts`
- `GET/POST /programs/{id}/timetable`
- `GET/POST /hostel/rooms`, `GET/POST /hostel/allocations`, `GET/POST /logistics`
- `GET /attendance/qr-token`, `POST /attendance/scan`
- `GET /analytics/overview`, `GET /analytics/programs/{id}`
- `POST /career/chat`, `POST /offline/sync`
- `PATCH /job-applications/{id}`
- `GET /ai/recommendations`, `GET /ai/risk-insights`
- `GET/POST /devices`, `POST /devices/heartbeat`, `POST /devices/attendance`, `GET /devices/events`
- `GET /health`

## Frontend coverage

`frontend/index.html` is a role-aware responsive web client rather than a static mock-up. It exposes programme registration and nominations, timetable management, learning enrolment/progress/assessments, secure QR attendance, profiles, certificates, hostel and logistics operations, recruiter pipelines, analytics, and career guidance. Its service worker caches the application shell, previously viewed programme/course content is retained for read-only offline access, and lesson progress is queued and synchronized through `/offline/sync` after reconnection.

Serve the frontend over HTTP so its service worker and camera APIs are available:

```powershell
python -m http.server 5173 --directory frontend
```

Every protected endpoint uses a bearer access token returned by login. The interactive API page shows each field and response format. Dates use ISO format, for example `2026-10-03`.

## Design notes

## Run and verify

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API. Copy `.env.example` to `.env` and replace every placeholder before deployment.

## Production boundaries

Use HTTPS, a strong secret, database migrations, backups, rate limits, centralized logs, and role audits in deployment. QR attendance uses a signed token that expires in two minutes. The system deliberately does not store face images or claim face recognition: add a privacy notice, explicit/withdrawable consent, retention limits, liveness detection, a vetted biometric provider, and a non-biometric alternative before field deployment. The PWA caches previously viewed learning content and synchronizes queued progress; bulk downloadable course packs and native mobile packaging remain future integrations.
