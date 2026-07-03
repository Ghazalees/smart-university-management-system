# UniFlow

**UniFlow** is a role-aware university management platform that combines academic operations, governed institutional knowledge, workflow automation, notifications, reporting, and grounded AI-assisted question answering in one responsive web application.

This repository contains the complete frontend, backend, private AI service, reverse-proxy configuration, automated tests, and Docker deployment configuration required to run the system from end to end.

## Table of contents

1. [Core capabilities](#core-capabilities)
2. [Architecture](#architecture)
3. [Technology stack](#technology-stack)
4. [Roles and access model](#roles-and-access-model)
5. [Repository structure](#repository-structure)
6. [Prerequisites](#prerequisites)
7. [Quick start with Docker](#quick-start-with-docker)
8. [Configuration](#configuration)
9. [Demo data](#demo-data)
10. [Local development](#local-development)
11. [Frontend production build](#frontend-production-build)
12. [Testing and quality checks](#testing-and-quality-checks)
13. [End-to-end verification](#end-to-end-verification)
14. [Knowledge upload and grounded AI](#knowledge-upload-and-grounded-ai)
15. [API overview](#api-overview)
16. [Production deployment](#production-deployment)
17. [Data persistence and backup](#data-persistence-and-backup)
18. [Troubleshooting](#troubleshooting)
19. [Security notes](#security-notes)

---

## Core capabilities

### Identity and authorization

- JWT access and refresh tokens
- Refresh-token rotation and token blacklisting
- Role-based access control and object-level authorization
- Account lockout and request throttling
- User activation, deactivation, reactivation, and role assignment
- Role-aware navigation and protected frontend routes

### Academic operations

- Courses and class sections
- Professor-owned class editing
- Enrollment management with duplicate and capacity validation
- Exams and grades
- Student-only grade visibility
- Professor class-performance reports containing:
  - enrolled students
  - each student's grade
  - students without grades
  - class average
  - minimum and maximum grades
  - recorded feedback
- Degree-progress tracking, academic goals, recommendations, and schedule suggestions

### Knowledge management

- Governed institutional documents
- File upload and text extraction
- Supported uploads: `.txt`, `.md`, `.csv`, `.json`, `.pdf`, `.docx`, `.docm`, `.html`, and `.htm`
- Document publishing, archiving, restoration, and reindexing
- Revision history and version restoration
- Access levels and role restrictions
- Governance dates, review ownership, tags, and expiration status
- JSON and CSV import/export

### Grounded AI

- Retrieval only from authorized, published, AI-enabled knowledge
- English and Persian token normalization
- Relevant-passage selection for long documents
- Source citations and confidence scoring
- Local deterministic provider for offline development
- Optional remote-provider adapter
- Human-answer escalation and answer feedback

### University operations

- Configurable workflow request types
- Dynamic forms, assignment, transitions, history, and optimistic concurrency
- Notifications, unread counts, preferences, actions, digest, and broadcasts
- Role-specific dashboards and analytics
- Calendar, global search, activity feed, feedback center, and user preferences
- Light/dark appearance and responsive layouts

---

## Architecture

```mermaid
flowchart LR
    U[Browser] --> G[Nginx gateway :80]
    G --> F[React static frontend :8080]
    G --> B[Django REST API :8000]
    B --> D[(SQLite persistent volume)]
    B --> A[Private FastAPI AI service :9000]
    A --> L[Local grounded provider]
    A -. optional .-> R[Remote LLM endpoint]
```

Only the gateway is published to the host in the default Docker setup. The backend, frontend service, database volume, and AI service communicate on a private Docker network.

### Request flow

1. The browser loads the React application through Nginx.
2. Requests under `/api/` are proxied to Django REST Framework.
3. Django authenticates the user and applies permission and object-level checks.
4. For grounded questions, Django retrieves only documents visible to that user.
5. Authorized passages are sent to the private AI service.
6. The response is returned with confidence information and source references.

---

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Redux Toolkit, RTK Query, React Router, React Hook Form, Zod |
| UI | Custom responsive CSS, Geist Variable font, Lucide icons, light/dark themes |
| Backend | Python 3.12, Django 5.2, Django REST Framework, Simple JWT |
| AI service | FastAPI, Pydantic, HTTPX, local or remote provider abstraction |
| Storage | SQLite in a persistent Docker volume |
| Gateway | Nginx 1.27 Alpine |
| Testing | Pytest, pytest-django, Vitest, React Testing Library |
| Deployment | Docker and Docker Compose v2 |

---

## Roles and access model

| Role | Primary capabilities |
|---|---|
| Student | View own academics and grades, ask questions, read permitted knowledge, submit requests, view notifications |
| Professor | Student capabilities plus manage own classes, view enrollments, record grades, and view class reports |
| Administrative Staff | Manage users, documents, workflows, academic records, questions, broadcasts, reports, and feedback |
| University President | Full platform permissions, analytics, audit visibility, and management access |

The backend is the source of truth for authorization. Hiding a control in the frontend does not replace server-side permission checks.

---

## Repository structure

```text
.
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── README.md
├── backend/
│   ├── apps/                 # Django domain applications
│   ├── config/               # Django settings and URL configuration
│   ├── docker/entrypoint.sh  # Runtime migration and seed entrypoint
│   ├── requirements/         # Development and production dependencies
│   ├── tests/                # Backend API and domain tests
│   ├── Dockerfile
│   └── manage.py
├── ai-service/
│   ├── api/                  # FastAPI application and provider layer
│   ├── tests/                # AI-service tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/                  # React application source
│   ├── public/               # Static public assets
│   ├── dist/                 # Production bundle used by the frontend image
│   ├── docker/nginx.conf     # Static frontend server configuration
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
└── nginx/
    ├── nginx.conf            # Gateway-level Nginx configuration
    └── conf.d/default.conf   # API and frontend proxy routes
```

---

## Prerequisites

### Recommended Docker workflow

- Docker Desktop or Docker Engine
- Docker Compose v2 (`docker compose`)
- At least 4 GB of available memory
- Port 80 available, or another port configured through `HTTP_PORT`

### Local development workflow

- Python 3.12
- Node.js 22 LTS or newer
- npm 10 or newer

Verify the tools:

```bash
docker --version
docker compose version
python --version
node --version
npm --version
```

---

## Quick start with Docker

### 1. Open the project directory

PowerShell:

```powershell
cd C:\path\to\smart-university-management-system-complete
```

macOS/Linux:

```bash
cd /path/to/smart-university-management-system-complete
```

### 2. Create the environment file

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

For local development, the supplied defaults are usable. Before any shared or production deployment, replace the secret values.

### 3. Build and start the system

```bash
docker compose up --build -d
```

The backend container automatically performs the following when enabled in `.env`:

1. database migrations
2. system role and permission seeding
3. optional demo-data seeding
4. static-file collection
5. Gunicorn startup

### 4. Check service status

```bash
docker compose ps
```

All services should be running, and the backend and AI service should become healthy.

### 5. Open UniFlow

```text
http://localhost
```

When `HTTP_PORT` is changed, use that port instead, for example:

```text
http://localhost:8088
```

### 6. Verify health endpoints

PowerShell:

```powershell
curl.exe http://localhost/gateway-health
curl.exe http://localhost/healthz
curl.exe http://localhost/api/v1/health
```

macOS/Linux:

```bash
curl http://localhost/gateway-health
curl http://localhost/healthz
curl http://localhost/api/v1/health
```

Expected gateway result:

```text
ok
```

### 7. View logs

```bash
docker compose logs -f --tail=100
```

Service-specific examples:

```bash
docker compose logs -f backend
docker compose logs -f ai-service
docker compose logs -f frontend
docker compose logs -f nginx
```

### 8. Stop or remove the containers

Stop without removing containers:

```bash
docker compose stop
```

Restart stopped containers:

```bash
docker compose start
```

Remove containers while preserving the database volume:

```bash
docker compose down
```

Reset containers and delete all persisted application data:

```bash
docker compose down -v
docker compose up --build -d
```

> `docker compose down -v` permanently removes the local database volume.

---

## Configuration

The root `.env` file is consumed by Docker Compose.

### Main Docker configuration

| Variable | Development default | Purpose |
|---|---:|---|
| `DJANGO_SECRET_KEY` | required placeholder | Django cryptographic secret; replace before deployment |
| `DJANGO_DEBUG` | `1` | Enables development behavior |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` | Accepted HTTP hostnames |
| `CORS_ALLOWED_ORIGINS` | `http://localhost` | Browser origins allowed by the API |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost` | Trusted CSRF origins |
| `AI_SERVICE_API_KEY` | required placeholder | Shared private key between Django and the AI service |
| `AI_PROVIDER` | `local` | `local` for grounded offline responses or `remote` for an external provider |
| `AI_RETRIEVAL_STRATEGY` | `hybrid` | Backend retrieval strategy |
| `HTTP_PORT` | `80` | Host port exposed by the gateway |
| `AUTO_MIGRATE` | `1` | Runs migrations at backend startup |
| `AUTO_SEED_SYSTEM` | `1` | Ensures system roles and permissions exist |
| `AUTO_SEED_DEMO` | `1` | Creates demonstration users and sample data in debug mode |
| `SESSION_COOKIE_SECURE` | `0` | Set to `1` behind HTTPS |
| `CSRF_COOKIE_SECURE` | `0` | Set to `1` behind HTTPS |
| `SECURE_SSL_REDIRECT` | `0` | Redirects HTTP to HTTPS when enabled |
| `SECURE_HSTS_SECONDS` | `0` | HSTS duration; enable only after HTTPS is correctly configured |

### Additional backend variables

The backend also supports the variables documented in `backend/.env.example`, including:

- `SQLITE_DB_PATH`
- `AI_SERVICE_URL`
- `AI_SERVICE_TIMEOUT_SECONDS`
- `AI_CONFIDENCE_THRESHOLD`
- `LOGIN_MAX_ATTEMPTS`
- `ACCOUNT_LOCK_MINUTES`
- authentication and AI throttle rates
- upload and extracted-text limits
- logging level

### Remote AI provider

Set these variables for a compatible remote endpoint:

```env
AI_PROVIDER=remote
LLM_API_URL=https://provider.example/v1/answer
LLM_API_KEY=replace-me
LLM_MODEL=your-model
```

The remote endpoint must accept the request shape implemented in `ai-service/api/providers.py` and return an `answer` field, with optional `confidence`.

### Using a non-default local port

Example `.env`:

```env
HTTP_PORT=8088
CORS_ALLOWED_ORIGINS=http://localhost:8088
CSRF_TRUSTED_ORIGINS=http://localhost:8088
```

Restart after changing `.env`:

```bash
docker compose down
docker compose up --build -d
```

---

## Demo data

When both conditions are true:

```env
DJANGO_DEBUG=1
AUTO_SEED_DEMO=1
```

the backend creates development-only sample users and academic data.

| Role | Username | Password |
|---|---|---|
| Student | `student` | `Student123!` |
| Professor | `professor` | `Professor123!` |
| Administrative Staff | `staff` | `Staff123!` |
| University President | `president` | `President123!` |

These credentials are intentionally not displayed on the login page. Disable demo seeding for any non-local environment:

```env
AUTO_SEED_DEMO=0
```

System-only seed command:

```bash
python manage.py seed_initial_data --system-only
```

Full development seed command:

```bash
python manage.py seed_initial_data
```

The full seed command is blocked outside debug mode unless explicitly allowed.

---

## Local development

Run the three application services in separate terminals.

### 1. AI service

PowerShell:

```powershell
cd ai-service
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:AI_SERVICE_API_KEY = "local-ai-internal-key"
$env:AI_PROVIDER = "local"
uvicorn api.main:app --reload --host 0.0.0.0 --port 9000
```

macOS/Linux:

```bash
cd ai-service
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
export AI_SERVICE_API_KEY=local-ai-internal-key
export AI_PROVIDER=local
uvicorn api.main:app --reload --host 0.0.0.0 --port 9000
```

Endpoints:

```text
http://localhost:9000/health
http://localhost:9000/docs
```

### 2. Django backend

PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements\development.txt

$env:DJANGO_SECRET_KEY = "local-development-key-change-me"
$env:DJANGO_DEBUG = "1"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
$env:CORS_ALLOWED_ORIGINS = "http://localhost:3000"
$env:AI_SERVICE_URL = "http://localhost:9000"
$env:AI_SERVICE_API_KEY = "local-ai-internal-key"

python manage.py migrate
python manage.py seed_initial_data
python manage.py runserver 0.0.0.0:8000
```

macOS/Linux:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements/development.txt

export DJANGO_SECRET_KEY=local-development-key-change-me
export DJANGO_DEBUG=1
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
export CORS_ALLOWED_ORIGINS=http://localhost:3000
export AI_SERVICE_URL=http://localhost:9000
export AI_SERVICE_API_KEY=local-ai-internal-key

python manage.py migrate
python manage.py seed_initial_data
python manage.py runserver 0.0.0.0:8000
```

Backend health:

```text
http://localhost:8000/api/v1/health
```

Django administration:

```text
http://localhost:8000/admin/
```

### 3. React frontend

```bash
cd frontend
npm ci
npm run dev
```

Open:

```text
http://localhost:3000
```

Vite proxies `/api` to `http://localhost:8000` during development.

---

## Frontend production build

The frontend Docker image serves the existing `frontend/dist` directory. After changing anything in `frontend/src`, rebuild the bundle before rebuilding the image:

```bash
cd frontend
npm ci
npm run build
cd ..
docker compose build --no-cache frontend
docker compose up -d frontend nginx
```

Then hard-refresh the browser:

- Windows/Linux: `Ctrl + F5`
- macOS: `Cmd + Shift + R`

The login page uses its original responsive, scrollable behavior so content remains accessible at small viewport heights and browser zoom levels.

---

## Testing and quality checks

The repository includes automated backend, AI-service, and frontend tests.

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment, then run:

```bash
pip install -r requirements/development.txt
python manage.py check
python manage.py makemigrations --check --dry-run
ruff format --check .
ruff check .
pytest -q
pytest -q --cov=apps --cov-report=term-missing --cov-fail-under=70
```

Coverage includes authentication, roles, user creation, student registration, documents, Word extraction, revisions, grounded Q&A, workflows, notifications, academics, grading, reports, and security behavior.

### AI service

```bash
cd ai-service
python -m venv .venv
```

Activate the environment, then run:

```bash
pip install -r requirements.txt
pytest -q
```

The AI tests cover health, internal API-key enforcement, grounded responses, confidence behavior, request limits, request analysis, and relevant-passage selection.

### Frontend

```bash
cd frontend
npm ci
npm run typecheck
npm run lint
npm test
npm run build
```

The frontend tests cover authentication state, protected routes, modal focus behavior, Escape handling, close buttons, and backdrop closing.

### Watch mode

```bash
cd frontend
npm run test:watch
```

---

## End-to-end verification

Use this checklist after a fresh Docker startup.

### Authentication and roles

1. Sign in with each development role.
2. Confirm each role sees only its authorized navigation and actions.
3. Sign out and verify protected pages redirect to `/login`.

### Modal behavior

1. Open forms in Requests, Knowledge, Classes, Grades, and Feedback.
2. Confirm text fields retain focus while typing.
3. Confirm each modal closes using:
   - the close button
   - `Escape`
   - `Cancel`
   - the backdrop, where enabled
4. Confirm the page is not left with a blocking overlay or locked scroll.

### Knowledge and AI

1. Sign in as Administrative Staff.
2. Upload a text-based `.docx` file in Knowledge.
3. Set it to Published and enable grounded AI usage.
4. Select an access level that includes the user who will ask the question.
5. Ask a question whose answer appears near the end of the document.
6. Confirm the answer includes relevant content and a citation to the uploaded document.
7. Edit the document using Create Revision.
8. Confirm a new version appears and the revision summary is retained.

### Student registration and enrollment

1. Create a new user with the Student role and a unique student number.
2. Confirm duplicate student numbers are rejected.
3. Enroll the student in a class.
4. Confirm duplicate enrollment and full-capacity enrollment are rejected.

### Professor grading and class report

1. Sign in as the professor who owns the class.
2. Edit the class and save the change.
3. Open Record Grade and confirm students are loaded from class enrollments.
4. Record a grade and feedback.
5. Open the class report and verify the student list, grades, ungraded count, average, minimum, maximum, and feedback.
6. Sign in as a student and confirm other students' results are not visible.

### API health smoke test

```bash
curl http://localhost/gateway-health
curl http://localhost/healthz
curl http://localhost/api/v1/health
```

---

## Knowledge upload and grounded AI

### Supported files

| Format | Notes |
|---|---|
| TXT / Markdown | Direct text extraction |
| CSV | Rows are converted to readable text |
| JSON | Parsed and normalized as formatted JSON |
| HTML / HTM | Visible text is extracted |
| PDF | Text-based PDFs only; OCR is not included |
| DOCX / DOCM | Paragraphs, tables, headers, footers, footnotes, endnotes, and comments are extracted when present |

Legacy `.doc` files are not supported. Open them in Microsoft Word or another compatible editor and save them as `.docx` before uploading.

### Requirements for an AI-eligible document

A document must be:

- published
- enabled for knowledge retrieval
- not expired
- visible to the requesting user under its access level and role restrictions
- successfully indexed

### Upload limits

The default maximum upload size is 5 MB. Backend settings also limit the maximum extracted character count. Both can be changed through environment variables.

### Reindexing

Use Reindex after a document or its governance metadata changes. A document uploaded before extraction-related code changes should be uploaded again or reindexed so stored text reflects the current extractor.

### Important retrieval behavior

The local provider does not invent an answer from general knowledge. When no sufficiently relevant authorized passage exists, it returns a low-confidence escalation response rather than an unsupported answer.

---

## API overview

Base path:

```text
/api/v1/
```

### Main route groups

| Area | Routes |
|---|---|
| Health | `GET /health` |
| Authentication | `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`, `/auth/change-password` |
| Users and RBAC | `/users`, `/roles`, `/permissions`, `/departments` |
| Knowledge | `/documents`, `/documents/upload`, `/documents/search`, versions, restore, publish, reindex, import, export |
| Questions | `/questions`, answer, human answer, history, and feedback routes |
| Workflows | `/workflow-types`, `/workflow-requests`, assignment and transition routes |
| Notifications | `/notifications`, preferences, read actions, digest, and broadcast |
| Academics | `/courses`, `/classes`, `/enrollments`, `/exams`, `/grades`, degree progress, goals, recommendations, schedule suggestions |
| Reports | `/reports/dashboard`, `/reports/ai-analytics`, `/audit-logs` |
| Experience | `/search`, `/calendar`, `/activity-feed`, `/feedback`, `/experience/preferences` |

### Login example

PowerShell:

```powershell
$body = @{
  identifier = "student"
  password   = "Student123!"
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body $body

$access = $response.data.tokens.access
```

curl:

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"student","password":"Student123!"}'
```

Authenticated request:

```bash
curl http://localhost/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Production deployment

The supplied `docker-compose.prod.yml` expects immutable image names instead of building source code on the production host.

### 1. Build application images

Build the frontend bundle first:

```bash
cd frontend
npm ci
npm run build
cd ..
```

Build and tag images:

```bash
docker build -t your-registry/uniflow-backend:2.0 ./backend
docker build -t your-registry/uniflow-frontend:2.0 ./frontend
docker build -t your-registry/uniflow-ai:2.0 ./ai-service
```

Push them to your registry when required.

### 2. Create a production environment file

Example `.env.production`:

```env
BACKEND_IMAGE=your-registry/uniflow-backend:2.0
FRONTEND_IMAGE=your-registry/uniflow-frontend:2.0
AI_IMAGE=your-registry/uniflow-ai:2.0

DJANGO_SECRET_KEY=replace-with-a-long-random-production-secret
DJANGO_ALLOWED_HOSTS=uniflow.example.edu
CORS_ALLOWED_ORIGINS=https://uniflow.example.edu
CSRF_TRUSTED_ORIGINS=https://uniflow.example.edu
AI_SERVICE_API_KEY=replace-with-a-long-random-private-service-key
AI_PROVIDER=local
AI_RETRIEVAL_STRATEGY=hybrid
HTTP_PORT=80

SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
SECURE_SSL_REDIRECT=0
SECURE_HSTS_SECONDS=31536000
```

### 3. Start the production stack

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

### Production requirements

- Terminate TLS at a trusted reverse proxy or load balancer.
- Keep `AUTO_SEED_DEMO=0`.
- Use unique production secrets.
- Restrict registry and host access.
- Back up the persistent database volume.
- Use PostgreSQL instead of SQLite for multi-instance or high-concurrency production workloads.
- Enable HSTS only after HTTPS is working correctly on all relevant subdomains.

---

## Data persistence and backup

The default stack stores SQLite data in the Docker volume named from the Compose project and `backend-data` volume declaration.

### Copy the database out of the running container

PowerShell:

```powershell
docker compose stop backend
$backendContainer = docker compose ps -q backend
docker cp "${backendContainer}:/app/data/db.sqlite3" .\db.sqlite3.backup
docker compose start backend
```

macOS/Linux:

```bash
docker compose stop backend
backend_container=$(docker compose ps -q backend)
docker cp "$backend_container:/app/data/db.sqlite3" ./db.sqlite3.backup
docker compose start backend
```

### Restore a database backup

Stop the backend before replacement:

PowerShell:

```powershell
docker compose stop backend
$backendContainer = docker compose ps -q backend
docker cp .\db.sqlite3.backup "${backendContainer}:/app/data/db.sqlite3"
docker compose start backend
```

macOS/Linux:

```bash
docker compose stop backend
backend_container=$(docker compose ps -q backend)
docker cp ./db.sqlite3.backup "$backend_container:/app/data/db.sqlite3"
docker compose start backend
```

Create backups before migrations, upgrades, or destructive resets.

---

## Troubleshooting

### Docker Hub returns `403 Forbidden`

Test the base image directly:

```bash
docker logout
docker login
docker pull nginx:1.27-alpine
docker pull python:3.12-slim
```

If token requests still return `403`, check VPN, proxy, corporate network policy, DNS, regional access restrictions, or test with another network such as a mobile hotspot. This error occurs before the project is built and is not caused by the application source.

### Port 80 is already in use

Change `.env`:

```env
HTTP_PORT=8088
CORS_ALLOWED_ORIGINS=http://localhost:8088
CSRF_TRUSTED_ORIGINS=http://localhost:8088
```

Then restart:

```bash
docker compose down
docker compose up --build -d
```

### Frontend changes do not appear

The frontend container serves `frontend/dist`. Rebuild it:

```bash
cd frontend
npm ci
npm run build
cd ..
docker compose build --no-cache frontend
docker compose up -d frontend nginx
```

Then hard-refresh the browser.

### A Word document does not answer questions

Confirm all of the following:

- the file is `.docx` or `.docm`, not legacy `.doc`
- the document is Published
- knowledge retrieval is enabled
- the requesting role has access
- the document is not expired
- reindexing completed
- the question uses terms that exist in the document

If the document was uploaded before extractor changes, upload it again so the stored extracted text is recreated.

### A scanned PDF produces no useful text

The project extracts embedded PDF text and does not include OCR. Convert the scan to a searchable PDF or upload the text in another supported format.

### The database should be reset

```bash
docker compose down -v
docker compose up --build -d
```

This removes all local users, documents, grades, requests, and other stored records.

### Inspect backend errors

```bash
docker compose logs --tail=200 backend
```

### Inspect AI-service errors

```bash
docker compose logs --tail=200 ai-service
```

### Restart Docker Desktop and WSL on Windows

```powershell
wsl --shutdown
```

Then reopen Docker Desktop and retry.

---

## Security notes

- Never commit `.env` files or real credentials.
- Replace default secrets before shared deployment.
- Disable demo data outside local development.
- Keep the AI service private; the gateway intentionally does not expose it.
- Treat role checks in the frontend as usability only; backend authorization remains mandatory.
- Use HTTPS and secure cookies in production.
- Review allowed hosts, CORS origins, and CSRF trusted origins carefully.
- Apply least-privilege roles to documents and management actions.
- Monitor audit records and request IDs when investigating incidents.
- Back up data before deployment changes.
- SQLite is appropriate for this self-contained deployment; use a managed relational database for larger production installations.

---

## Project status

The repository is self-contained for local Docker deployment and source-level development. It includes application code, runtime configuration, database migrations, production frontend assets, and automated component/service tests. No external SaaS dependency is required when `AI_PROVIDER=local`.
