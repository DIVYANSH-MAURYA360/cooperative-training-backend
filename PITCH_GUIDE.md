# SahakarSetu — external evaluation pitch guide

## One-line proposition

SahakarSetu is an AI-enabled cooperative capacity-building ecosystem that connects programme administration, inclusive learning, verified skills and rural employment in one measurable journey.

## 30-second opening

NCCT and its institutions train cooperative personnel and rural youth at national scale, but programme records, learning progress, certifications and employment outcomes often remain fragmented. SahakarSetu creates one continuous digital journey—from nomination and hostel allocation to multilingual learning, secure attendance, assessment, verified certification, explainable opportunity matching and employer selection. It is offline-ready, hardware-ready and designed around consent, inclusion and measurable public impact.

## Two-minute problem–solution narrative

The problem is not a lack of training activity; it is a lack of continuity. A participant may be nominated in one system, attend through a paper register, learn from disconnected material, receive a certificate that is difficult to verify, and then search for work without any link to the skills they gained.

SahakarSetu connects these stages. Institutions manage programmes, nominations, schedules, accommodation and logistics. Learners access multilingual lessons, complete assessments and build a verified skill profile even under intermittent connectivity. Secure QR and authenticated attendance terminals provide auditable participation, while biometric attendance remains consent-based with a QR alternative. Explainable AI recommends learning and jobs and helps counsellors identify learners who may need supportive outreach. Employers publish opportunities and manage candidates through a controlled pipeline. NCCT receives centralized analytics covering registration, learning, certification and employment conversion.

The result is not merely an LMS or ERP. It is an outcome-focused capacity-building and livelihood ecosystem for India's cooperative movement.

## Five differentiators

1. **Full lifecycle:** registration to employment outcome, not isolated modules.
2. **Explainable responsible AI:** visible match reasons and human-reviewed intervention signals.
3. **Inclusive hardware model:** secure QR plus consent-controlled face-terminal integration.
4. **Rural readiness:** responsive PWA, cached learning and conflict-aware offline progress.
5. **Measurable governance:** centralized programme, certification and employment indicators.

## Suggested closing

SahakarSetu turns every training investment into a traceable pathway: a learner reached, a skill built, a credential trusted and an opportunity unlocked. With NCCT field validation and approved hardware partners, the same architecture can scale across institutions while preserving local language, accessibility and privacy needs.

## Common judge questions

### Is the AI only a chatbot?

No. The system includes explainable course and job ranking, profile-completeness actions and learner-risk signals. The career assistant is one interface; the underlying value is decision support across learning and employment.

### How do you prevent AI bias?

Recommendations show reasons and never make automatic hiring or exclusion decisions. Risk scores only prioritize supportive human outreach. Users can improve recommendations by editing their profile.

### What happens without reliable internet?

The PWA caches previously viewed programme and learning content. Lesson progress is queued locally and reconciled through the offline-sync API after connectivity returns.

### Is face recognition mandatory?

No. Biometric attendance requires explicit consent, an approved device and a confidence threshold. QR is always available as the non-biometric alternative.

### Can this scale nationally?

The API and data model are institution-aware and support PostgreSQL deployment. Production scaling requires migrations, object storage, observability, rate limiting and staged NCCT rollout; these are documented pilot milestones rather than hidden assumptions.
