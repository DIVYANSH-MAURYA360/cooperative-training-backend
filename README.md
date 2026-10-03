# Cooperative Training API

Backend starter for cooperative training programme management, learning content, attendance, certificates, and employment.

## Run locally

### Open the web preview

The `frontend/index.html` file is a clickable dashboard preview. Start its lightweight local web server from this project folder with `python -m http.server 4173 --directory frontend`, then open `http://127.0.0.1:4173`. This only needs Python and uses no Python packages. Its dashboard is sample data; it shows “Preview mode” until the API is running.

### Run the backend API

1. Install Python 3.11 or newer.
2. In this folder, create a virtual environment: `python -m venv .venv`
3. Activate it on Windows: `.venv\\Scripts\\Activate.ps1`
4. Install packages: `pip install -e .`
5. Copy `.env.example` to `.env` and replace `SECRET_KEY` with a long random value.
6. Start the API: `uvicorn app.main:app --reload`
7. In a second terminal, create the first administrator: `python scripts/create_admin.py` (run this from the backend folder).
8. Open `http://127.0.0.1:8000/docs` to try the API interactively.

The default database is SQLite and the database file is created automatically. To use PostgreSQL, set `DATABASE_URL` in `.env`, for example `postgresql+psycopg://user:password@localhost:5432/cooperative_training`. The dashboard preview currently uses sample data; the frontend guide shows how to connect real API calls.

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
- `GET /health`

Every protected endpoint uses a bearer access token returned by login. The interactive API page shows each field and response format. Dates use ISO format, for example `2026-10-03`.

## Design notes

This is a working foundation, not yet a production deployment. Run database migrations before evolving schemas in a live environment; Alembic is the recommended next addition. Use HTTPS, a strong secret, backups, rate limits, centralized logs, and role audits in deployment. Attendance accepts `qr` as a recording method, but this starter does not generate QR tokens. It does not store face images or perform face recognition. Add privacy notice, consent, retention limits, and a non-biometric alternative before implementing biometrics. File uploads, offline sync, messaging, hostel allocation, timetable, assessment grading, and analytics dashboards are future modules.
