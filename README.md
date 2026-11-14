# Research Submission Tracker — Project 28, Week 13 SA7

Educational prototype with Python standard-library API + Flutter Web. **Not production-ready.** All names must be fictional. The `X-Demo-Role` header is intentionally an insecure role simulation for Week 13; it is NOT authentication. Week 14 must replace it with real server-side authentication and authorization.

## 1. Requirements
Python 3.10+; Flutter SDK; Chrome; network access once to install the Flutter `http` dependency.

## 2. Run API
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
- `GET /health` — service status
- `GET /submissions` — list
- `POST /submissions` — `{title, student}` demo student
- `POST /assign` — `{id, reviewer, deadline}` demo staff
- `POST /revision` — `{id}` demo student
- `POST /automation/run` — `{id, simulate}` where simulate is `none`, `transient`, or `permanent`; demo staff
- `GET /events` — structured event list
- `GET /summary` — counts

## 6. Week 13 scope and alternatives
Trigger: on-demand demonstration of scheduled/event-driven candidate notifications. Event types: review assignment, version-status update, deadline reminder, overdue escalation. Bounded delivery retry max 3. Permanent failure -> manual review. This is a simplified educational vertical slice; a real daily scheduler and notification provider are future implementation tasks.

Alternative considered: external SMS/email (rejected for demo due to credentials/privacy). Chosen: local event log with controlled fault injection to generate repeatable test evidence.

## 7. Safety
Never upload `backend/tracker.db` with real people or any credentials. Use fake names. Review screenshots before sharing. Preserve original evidence; do not fabricate screenshots or logs. Cite permitted assistance in your individual note.
