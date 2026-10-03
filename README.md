# Cooperative Training API

Backend starter for cooperative training programme management, learning content, attendance, certificates, and employment.


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
