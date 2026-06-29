# Matchmatic Backend

US job matching platform: **JSearch ingest → Postgres → Gemini analysis → personalized feed**.

## Architecture

```
┌─────────────┐     Google OAuth      ┌──────────────┐
│  React UI   │ ◄──────────────────► │   Supabase   │
│  (Vite)     │                       │   Auth       │
└──────┬──────┘                       └──────────────┘
       │ REST + JWT
       ▼
┌─────────────┐     enqueue tasks     ┌──────────────┐
│  FastAPI    │ ────────────────────► │    Redis     │
│  :8000      │                       │   (broker)   │
└──────┬──────┘                       └──────┬───────┘
       │                                     │
       │ SQL                                 │ consume
       ▼                                     ▼
┌─────────────┐                       ┌──────────────┐
│ PostgreSQL  │ ◄── save jobs ─────── │ Celery worker│
│  (Docker)   │                       │              │
└─────────────┘                       └──────┬───────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
             JSearch API              Gemini API              Redis cache
             (RapidAPI)            (match scoring)         (analysis TTL)
```

### Pipeline

1. **Ingest** — `run_scrapers` Celery task calls JSearch (`/search-v2`) with user keywords.
2. **Persist** — `JobIngestionService` dedupes by URL, validates descriptions, writes `jobs`.
3. **Analyze** — `analyze_job` task runs ATS scorer + optional visa check + report writer (Gemini).
4. **Feed** — `GET /jobs/feed` returns jobs where `ats_score >= user.min_match_score` and not dismissed.

### Key modules

| Path | Role |
|------|------|
| `app/scraper/jsearch.py` | JSearch API client + normalization |
| `app/scraper/job_ingestion.py` | Validation, dedupe, DB save, run logging |
| `app/tasks/scraper_task.py` | Celery app + `run_scrapers` task |
| `app/tasks/analysis_task.py` | Per-job Gemini pipeline + Redis cache |
| `app/agents/` | ATS scorer, visa analyzer, report writer |
| `app/utils/auth.py` | Supabase JWT (ES256 JWKS) → Matchmatic user |

## Prerequisites

- Python 3.11+
- Node 18+ (frontend)
- Docker Desktop (Postgres + Redis)
- [Google AI Studio](https://aistudio.google.com/apikey) API key
- [JSearch on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) API key
- Supabase project (auth + resume storage)

## First-time setup

```powershell
# Repo root
cd Matchmatic
copy .env.example .env          # fill in all values

docker compose up -d

cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
```

### `.env` (repo root — not `backend/`)

Required:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
JSEARCH_API_KEY=
DATABASE_URL=postgresql://postgres:localpassword123@localhost:5432/matchmatic
REDIS_URL=redis://localhost:6379
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SECRET_KEY=
FRONTEND_URL=http://localhost:5173
TEST_USER_EMAIL=you@example.com
```

Optional JSearch tuning:

```env
JSEARCH_NUM_PAGES=2
JSEARCH_DATE_POSTED=week
JSEARCH_JOB_REQUIREMENTS=under_3_years_experience
```

### Frontend `.env.local`

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

## Run (4 terminals)

```powershell
# 1 — Infrastructure (once)
docker compose up -d

# 2 — API
cd backend && .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# 3 — Celery worker (required for ingest + analysis)
celery -A app.tasks.scraper_task:celery_app worker --loglevel=info --pool=solo --concurrency=1

# 4 — Frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 → log in → upload resume in Settings.

## Dev commands

```powershell
cd backend

# Test JSearch API only (no Celery)
python test_jsearch.py

# Test Gemini on a pasted JD
python test_analysis.py

# Full pipeline: JSearch ingest + queue analysis
python test_scraper.py

# Wipe all jobs/analyses for a fresh run
python clear_jobs.py --yes

# Unit tests
pytest tests/test_gemini_client.py -v
```

## Scheduled ingest

The API scheduler triggers `run_scrapers` every 6 hours (ingest only — no analysis unless you extend it with `user_id`).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Celery can't connect to Redis | `docker compose up -d` |
| `JSEARCH_API_KEY is required` | Add key to root `.env`, restart Celery |
| JSearch 404 | Endpoint is `/search-v2` (already configured) |
| Empty Jobs feed | Lower min match score; wait for analysis; check resume uploaded |
| Gemini quota | Switch `GEMINI_MODEL` in `.env` |
| `User not found` in analysis | Log in locally once; set `TEST_USER_EMAIL` |

## API smoke checks

```powershell
curl http://localhost:8000/health
# Bearer token from browser devtools after login:
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/jobs/feed
```
