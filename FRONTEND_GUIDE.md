# Frontend handoff guide

## How the frontend talks to this backend

The frontend sends HTTP requests to `http://127.0.0.1:8000`. Most data is JSON. Sign in first, keep the returned `access_token` in your app's authentication state, and send it on protected requests using `Authorization: Bearer <token>`. Do not put passwords or tokens in source code. For production, use HTTPS and choose an appropriate secure token storage strategy.

Example with browser JavaScript:

```js
const response = await fetch("http://127.0.0.1:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password })
});
const result = await response.json();
if (!response.ok) throw new Error(result.detail ?? "Login failed");
const token = result.access_token;

const programsResponse = await fetch("http://127.0.0.1:8000/programs", {
  headers: { Authorization: `Bearer ${token}` }
});
const programs = await programsResponse.json();
```

## Suggested screens mapped to API

1. Sign up and sign in: `/auth/register`, `/auth/login`, `/auth/me`.
2. Programme catalogue and registration: `GET /programs`, `POST /programs/{id}/register`.
3. Staff programme administration: `POST /programs`, `GET /programs/{id}/registrations`.
4. Course catalogue and lesson viewer: `GET /courses`, `GET /courses/{id}/lessons`.
5. Trainer attendance entry and reports: `POST /attendance`, `GET /attendance`.
6. Certificate check: `GET /certificates/verify/{code}`.
7. Job board and applications: `GET /jobs`, `POST /jobs/{id}/apply`, `GET /my/applications`.
8. Employer job management: `POST /jobs`, `GET /jobs/{id}/applications`.
9. Trainee profile and career guidance: `GET/PUT /profile/trainee`, `POST /career/chat`.
10. Course enrolment, progress and assessment: `/courses/{id}/enroll`, `/lessons/{id}/progress`, `/assessments` routes.
11. Secure QR attendance: trainees display `GET /attendance/qr-token`; staff scanners submit it to `POST /attendance/scan`.
12. Timetable and operations: `/programs/{id}/timetable`, `/hostel`, and `/logistics` routes.
13. Monitoring: `/analytics/overview` and `/analytics/programs/{id}`.
14. Offline progress reconciliation: `POST /offline/sync`.

## Important behavior

- A `401` means the user needs to sign in again or their token expired.
- A `403` means they are signed in but their role cannot perform that action.
- A `404` means the requested record does not exist or is not visible to that role.
- A `409` means a duplicate action or capacity conflict, such as registering twice.
- Validation failures use `422`; the response explains the field that needs correction.
- Roles are returned by `/auth/me`. Use them to show the right screens, but remember that the backend enforces permissions too.
- Local CORS permits common React/Vite origins on ports 3000 and 5173. Add the deployed frontend's exact origin to the CORS allow-list before deployment.
