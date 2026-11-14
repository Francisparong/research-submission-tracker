# Research Submission Tracker — Project 28 | Weeks 13–15

This educational project uses Flutter Web and a Python backend to manage research submissions and demonstrate system security. Week 13 focused on submission tracking, simulated notifications, and reviewer assignments. Week 14 introduced authentication, role-based access control, protected API requests, session management, and local HTTPS integration.

**Development Status:** Weeks 13–15 completed for educational testing. This system is not production-ready. Only fictional student information should be used.

## 1. Requirements
Python 3.10+; Flutter SDK; Chrome; network access once to install the Flutter `http` dependency.

## 2. Run API (Week 13 Legacy HTTP Setup)
Open Terminal/CMD in `backend`, then:

```bat
python server.py
```

Expected: `Research Submission Tracker API at http://127.0.0.1:8091`
Open http://127.0.0.1:8091/health to verify.

## 3. Run Flutter Web
The provided `flutter_web` has Dart sources and manifest. In a separate terminal:

```bat
cd flutter_web
flutter create . --platforms web
flutter pub get
flutter run -d chrome
```

If Flutter says target files exist, preserve the supplied `lib/main.dart` and `pubspec.yaml`. If port 8091 is taken by another app, stop it first (the API uses 8091). Firefox or phones on another device require a different API host and CORS configuration.

## 4. Run the Week 13 evidence demonstrations
1. Set role student, create a fictional research submission.
2. Switch role staff, select the submission, assign reviewer + deadline in YYYY-MM-DD format.
3. Run normal reminder. Run simulated transient failure; see attempt 1 failed and attempt 2 recovered.
4. Run simulated permanent failure; see three failed attempts and `manual_review` event.
5. Switch to student; submit revised version and check incremented version.
6. Refresh summary and visit `http://127.0.0.1:8091/events` in browser for structured event history.
7. Set past deadline before running automation to demonstrate overdue escalation.
8. Try submitting blank title and using staff-only action while in student role, and record actual error messages.

**This prototype records simulated notifications, not actual emails/SMS.** Retries are simulated inline for repeatable proof; production-ready scheduling, real integrations, and hardened role security remain limitations.

## 5. API contract
- `GET /health` â€” service status
- `GET /submissions` â€” list
- `POST /submissions` â€” `{title, student}` demo student
- `POST /assign` â€” `{id, reviewer, deadline}` demo staff
- `POST /revision` â€” `{id}` demo student
- `POST /automation/run` â€” `{id, simulate}` where simulate is `none`, `transient`, or `permanent`; demo staff
- `GET /events` â€” structured event list
- `GET /summary` â€” counts

## 6. Week 13 scope and alternatives
Trigger: on-demand demonstration of scheduled/event-driven candidate notifications. Event types: review assignment, version-status update, deadline reminder, overdue escalation. Bounded delivery retry max 3. Permanent failure -> manual review. This is a simplified educational vertical slice; a real daily scheduler and notification provider are future implementation tasks.

Alternative considered: external SMS/email (rejected for demo due to credentials/privacy). Chosen: local event log with controlled fault injection to generate repeatable test evidence.

## 7. Safety
Never upload `backend/tracker.db` with real people or any credentials. Use fake names. Review screenshots before sharing. Preserve original evidence; do not fabricate screenshots or logs. Cite permitted assistance in your individual note.

## Week 14 — Secure Authentication and HTTPS Integration

### Implemented Security Features

- Student and staff authentication
- Role-based access control
- Protected API endpoints
- Session expiration and logout
- Invalid password and tampered token rejection
- HTTPS communication using a trusted local certificate
- Server-side submission validation
- Git exclusions for databases and sensitive files

### Security Testing Results

The automated security test script completed 11 checks successfully.

**Result: 11/11 PASS (100%)**

Additional manual tests verified session expiration, invalid submission rejection, and HTTPS integration.

### Week 14 Local Setup

1. Configure separate demo credentials using `TRACKER_STUDENT_PASSWORD` and `TRACKER_STAFF_PASSWORD`.
2. Configure `TRACKER_TLS_CERT` and `TRACKER_TLS_KEY` using local development certificate paths.
3. Start the backend using `python server.py`.
4. Run Flutter Web using `--dart-define=TRACKER_API_BASE=https://localhost:8091`.
5. Run `python test_security.py` from the backend directory.

**Security Notice:** Never upload passwords, session tokens, local databases, or private keys to GitHub. This system is intended for educational local testing only.



## Week 15 — Integration Testing and Security Hardening

Week 15 builds on the Week 13 submission tracking features and Week 14 authentication and HTTPS integration.

### Completed Testing

- Backend regression testing: 20/20 passed
- Flutter login-interface widget test: 1/1 passed
- Authentication and authorization security smoke tests: passed
- Security hardening source checks: 5/5 verified

### Security Improvements

- SQLite connection cleanup
- JSON content-type and request-size validation
- Safe request logging
- Role-based authorization
- Session and authentication regression testing

### Testing Commands

Backend:
- `python -m unittest -v test_week15.py`
- `python test_security.py` (requires configured demo credentials and a running local API)

Flutter Web:
- `flutter pub get`
- `flutter test`

### Limitations

This is an educational prototype, not a production-ready system. Only fictional data should be used. The Flutter widget test covers basic login-interface rendering; additional state and failure-recovery testing is recommended.

### Week 15 Repository

https://github.com/Francisparong/research-submission-tracker/tree/week15-testing-hardening

