# Sprint 1–3 Test Report

## Automated suites

- Backend: authentication, token blacklisting, protected routes, health, user creation, duplicate prevention, document search/access isolation, question submission/history, question ownership, documented answer, low-confidence escalation, and AI downtime.
- AI service: health, document-grounded answer, no-document low confidence, and request analysis.

## Commands

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q

cd ../ai-service
PYTHONPATH=. pytest -q
```

## Expected result

- Backend: 14 passed.
- AI service: 4 passed.
- Django system check: 0 issues.
- Pending migrations: none.
