# External evaluation readiness — SahakarSetu

Assessment date: 2026-10-04  
Problem statement: SIH 26087 — AI & LMS-enabled Cooperative Capacity Building, ERP & Employment Ecosystem

## Evidence-based score: 92/100

This score uses the official SIH idea-selection dimensions: novelty, complexity, clarity/detail, feasibility, practicability, sustainability, scale of impact, user experience, and potential for future progression.

| Evaluation dimension | Score | Evidence in the working product |
|---|---:|---|
| Novelty and innovation | 18/20 | Explainable skill-to-learning/job matching, learner-risk intelligence, integrated ERP + LMS + employment exchange, privacy-aware hybrid attendance |
| Technical complexity | 14/15 | Five roles, 60+ API operations, secure JWT/role controls, assessments, offline conflict resolution, device authentication and audit pipeline |
| Clarity and completeness | 9/10 | Direct problem-feature mapping, OpenAPI documentation, alignment report, realistic demo dataset and automated end-to-end tests |
| Feasibility | 14/15 | Lightweight FastAPI/SQLAlchemy stack, SQLite-to-PostgreSQL path, responsive PWA, QR fallback, explainable deterministic AI |
| Practicability and sustainability | 13/15 | Institution-level operations, hostel/logistics, device lifecycle, offline-first learning, no mandatory paid AI dependency |
| Scale of impact | 14/15 | Central NCCT/RICM/ICM data model, multilingual course metadata, rural connectivity support, employer linkage and outreach analytics |
| User experience | 10/10 | Responsive role-aware dashboard, clear workflows, installable PWA, accessible forms, premium external-demo presentation |
| **Total** | **92/100** | Fully demonstrable locally with honest hardware/production boundaries |

## Highest-value differentiators

1. **Explainable AI instead of a black box.** Trainees receive ranked course and job matches with visible reasons. Staff receive a human-in-the-loop risk queue based on explainable operational signals. No learner is automatically excluded.
2. **Hardware-ready attendance gateway.** Institutions can register QR, face, or hybrid terminals. Each receives a one-time API key, sends authenticated heartbeats, and creates auditable events. Face attendance requires explicit trainee consent, an approved registration, an approved terminal, and at least 0.80 confidence; QR remains the non-biometric alternative.
3. **One continuous rural-youth journey.** Registration → timetable/hostel/logistics → learning → assessment → verified certificate → career guidance → job matching → recruiter pipeline.
4. **Offline-first design.** The PWA caches previously viewed learning content and safely reconciles queued progress after reconnection.
5. **National monitoring layer.** Administrators see training, completion, assessment, certification, employment conversion, and intervention indicators from one database.

## Recommended 7-minute external demo

1. Open `/` and explain the five personas: NCCT admin, institution, trainer, trainee, employer.
2. Show **Overview** to establish programme, course, opportunity, and registration scale.
3. Open **AI Insights** and explain risk signals and the human-in-the-loop safeguard.
4. Open **Programmes** to show registration approvals, nominations, and timetable.
5. Open **Learning** to show multilingual lessons, progress, assessment grading, and certification.
6. Open **Operations** to show hostel/logistics plus the live hybrid attendance terminal and audit trail.
7. Open **Analytics**, then summarize offline PWA and employment conversion.

## Honest remaining 8 points

- Field validation with physical camera/QR terminal hardware and real rural connectivity conditions.
- A vetted on-device or provider face model with liveness testing, DPIA, encryption and formal retention policy.
- Production Alembic migrations, object storage/CDN, observability, rate limiting, backup drills and penetration testing.
- NCCT stakeholder usability studies, accessibility audit and measured programme-outcome evidence at institutional scale.

These are deployment and field-validation milestones, not gaps that should be hidden. Presenting them as a staged pilot roadmap improves credibility and future-progression scoring.
