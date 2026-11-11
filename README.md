# Resume & Cover Letter Feedback Assistant

Full-stack demo app: React + Django REST Framework + PostgreSQL. A
candidate records job applications (company, job title, job description,
their own resume text) and generates AI feedback - a structured critique of
how the resume matches the job description, plus a tailored cover letter
draft.

## Stack

- Backend: Django 5 + Django REST Framework + Simple JWT, plain PostgreSQL
  in Docker (no extensions - no pgvector/vector DB in this app) with a
  SQLite dev-override for local `manage.py` work without Docker.
- Frontend: React + Vite + TypeScript, plain styling.
- AI: a single OpenAI chat-completion call per feedback generation - see
  `backend/apps/common/ai.py`. No embeddings, no vector search.

## Data model

- `accounts.User` (custom, email login, no username field): `full_name`,
  `role` (`candidate`/`admin`). Simple role distinction for a personal
  tool, not multi-tenant - a candidate manages only their own applications,
  an admin can additionally list everyone's.
- `applications.JobApplication`: owner, company_name, job_title,
  job_description (text), resume_text (text), created_at.
- `applications.FeedbackResult`: one-to-one with JobApplication - feedback
  (text), cover_letter_draft (text), generated_at. Regenerating replaces
  the existing result rather than creating a duplicate.

## AI feature (dual-path, see `backend/apps/common/ai.py`)

`generate_resume_feedback(resume_text, job_description)` returns
`{"feedback": str, "cover_letter_draft": str}`.

- **Real path** (`OPENAI_API_KEY` set): one chat-completions call using
  `OPENAI_CHAT_MODEL` (default **`gpt-5.4-mini`** - deliberately different
  from the `gpt-5.6-sol` default used by some sibling AI apps in this
  batch), prompted to return structured JSON. Parsed defensively; falls
  back gracefully rather than crashing if the model's reply isn't valid
  JSON.
- **Stub path** (no key - the default for local dev/tests, fully offline,
  zero cost): a deterministic, template-based result built only from the
  literal input text, quoting distinctive snippets back so it's clearly
  tied to that specific resume/job description. The same input always
  produces the same stub output.

## Demo accounts (seeded via data migration)

| Email | Password | Role |
| --- | --- | --- |
| candidate@example.com | demo12345 | candidate |
| admin@example.com | demo12345 | admin |

Seed data (the two demo users plus ~9 JobApplications across different
companies/roles for the demo candidate, most with a generated
FeedbackResult) is created by an idempotent Django data migration
(`backend/apps/applications/migrations/0002_seed_demo_data.py`) - it calls
the real `generate_resume_feedback()` function (running in stub mode at
migrate time, since there's no `OPENAI_API_KEY` then) and runs on every
`migrate` but only inserts once.

## API

- `POST /api/auth/login/`, `/api/auth/refresh/`, `/api/auth/logout/`,
  `/api/auth/register/`
- `GET /api/users/me/`
- `/api/applications/` (list/create/retrieve/update/delete, scoped per
  role - see below)
- `POST /api/applications/{id}/generate-feedback/` - triggers the AI call,
  creates/replaces the FeedbackResult.
- `GET /api/applications/{id}/feedback/` - fetch the generated
  feedback/cover-letter, 404 if not yet generated.

### Queryset scoping

A candidate sees/edits only their own applications. An admin can
additionally **list** all applications across candidates, but detail
actions (retrieve/update/delete/generate-feedback/feedback) stay scoped to
`owner=request.user` even for an admin - a cross-candidate request 404s
before any object-level permission check runs, the same queryset-scoping
pattern used by sibling apps like `leave-attendance` and
`perf-okr-platform`.

## Running locally without Docker (backend)

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # or venv/bin/activate on macOS/Linux
pip install -r requirements.txt

export USE_SQLITE=True
export DJANGO_SETTINGS_MODULE=config.settings.dev

python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Running locally without Docker (frontend)

```bash
cd frontend
npm install
npm run dev     # dev server on :5173
npm run build   # production build
```

Set `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`) if the
backend runs elsewhere.

## Running with Docker Compose (Postgres)

```bash
cp .env.example .env
docker compose up --build
```

Not exercised in this build environment (no Docker available here) - the
compose file targets a plain `postgres:16` with no extensions.

## Running against a real local Postgres (no Docker)

`backend/.env` is already set up for a native Postgres instance at
`localhost:5432` with role/database `resume_feedback_assistant` /
`resume_feedback_assistant`, and `USE_SQLITE=False`:

```bash
cd backend
source venv/Scripts/activate
python manage.py migrate
python manage.py runserver
```
