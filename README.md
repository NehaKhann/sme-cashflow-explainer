# Ledger — SME Cash-Flow Underwriting Platform

[![Tests](https://img.shields.io/badge/tests-15%20passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![React](https://img.shields.io/badge/react-19-61DAFB)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)]()

**Turn a raw bank transaction export into an auditable cash-flow risk memo in seconds.**

Ledger is an end-to-end underwriting tool for thin-file small-business borrowers. It separates **deterministic computation** (pandas + rule-based risk scoring) from **narrative generation** (optional LLM via Groq), so every figure in the final memo traces back to a specific calculation — the LLM is never allowed to invent a number.

## Why this exists

Small-business loan underwriting for thin-file borrowers (no long credit history) still leans on humans reading raw bank statements to judge seasonality, customer concentration risk, and cash-flow volatility. Existing scoring tools output a number; almost none explain *why* in a way an underwriter can audit.

Ledger solves this by making every number auditable. The pipeline is:

```
Upload CSV → Extract metrics (pandas) → Score risk (deterministic rules) → Generate narrative (LLM or template)
```

The narrative layer can only explain pre-computed figures. No hallucinations, no invented numbers.

## Architecture

```
├── docker-compose.yml     Orchestrates PostgreSQL + backend + frontend
│
├── frontend/              React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── components/    UI components (Sidebar, Intake, Results, Chart…)
│   │   ├── api/           API client (health check, analyze, reports CRUD)
│   │   ├── types/         TypeScript interfaces matching the backend schema
│   │   └── data/          Built-in sample dataset
│   └── Dockerfile.dev     Vite dev server container
│
├── backend/               FastAPI (Python 3.11+)
│   ├── Dockerfile         Production image
│   ├── docker-entrypoint.sh  Waits for DB, runs migrations, starts uvicorn
│   ├── app/
│   │   ├── database.py    Async SQLAlchemy engine + session
│   │   ├── db_models.py   Report & Transaction ORM models (PostgreSQL)
│   │   ├── routers/
│   │   │   ├── analysis.py   POST /api/analyze — saves to DB
│   │   │   └── reports.py    CRUD for persisted analysis reports
│   │   ├── services/
│   │   │   ├── feature_extraction.py   Pandas computations — every metric
│   │   │   ├── risk_scoring.py         Deterministic rules, fully unit-tested
│   │   │   └── narrative_generator.py  LLM (Groq) or template fallback
│   │   ├── models.py      Shared domain models
│   │   └── schemas.py     Pydantic API response models
│   └── tests/             15+ tests covering extraction, scoring, API, and reports
│
├── sample_data/           Synthetic data generator
└── render.yaml            Render.com deploy config
```

## Quick start — Docker (recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A free [Groq API key](https://console.groq.com) _(optional — works without one)_

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
# Optional — skip for deterministic template narratives
GROQ_API_KEY=gsk_your_key_here

# Required — generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=<your-generated-secret>
```

Docker Compose auto-loads `.env` from the project root — no extra flags needed.

### 2. Start all services

```bash
docker compose up -d
```

> **After pulling new code:** run `docker compose build frontend` to rebuild the frontend image, then `docker compose up -d` to restart with the latest changes.

This starts three containers:

| Service | URL | Description |
|---|---|---|
| **PostgreSQL** | `localhost:5432` | Persistent storage for transactions and reports |
| **Backend** | `localhost:8000` | FastAPI — auto-creates tables on startup |
| **Frontend** | `localhost:5173` | Vite dev server with live reload |

### 3. Run it

1. Open `http://localhost:5173` — you'll see the **landing page** describing the platform
2. Click **"Get started"** or **"Sign in"** to reach the login form
3. **First time?** Click "Create one" to sign up — you'll be signed in automatically
4. Returning users just **sign in** to see their history
4. Click **"Use sample data instead"** (or drop a CSV)
5. Click **"Analyze cash flow"**
6. Review the metrics, risk flags, chart, and narrative
7. Switch to the **Reports** page to see all saved analyses — data is scoped to your account

### 4. Run tests

```bash
cd backend
python -m pytest tests/ -v
```

15+ tests covering feature extraction edge cases, risk scoring rules, the API, and report CRUD.

### 5. Stop

```bash
docker compose down        # stops containers
docker compose down -v     # stops + deletes the database volume
```

## Quick start — native (no Docker)

### Prerequisites

- **Python 3.11+** and **Node.js 18+**
- A running **PostgreSQL 16** instance (or use [Neon](https://neon.tech) free tier)
- A free [Groq API key](https://console.groq.com) _(optional)_

### 1. Backend

```bash
cd backend
cp .env.example .env   # edit .env with your keys (DB, JWT, Groq)

python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API reads `.env` via `python-dotenv` and auto-creates tables (users, reports, transactions) on startup.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173` — sign up on first visit, then log in normally.

### 3. Run tests

```bash
cd backend
python -m pytest tests/ -v
```

## CSV format

| Column | Required | Notes |
|---|---|---|
| `date` | Yes | Any pandas-parseable date format |
| `amount` | Yes | Signed: positive = inflow, negative = outflow |
| `counterparty` | Yes | Payer/payee name — used for concentration risk |
| `category` | No | e.g. `revenue`, `payroll`, `rent` — defaults to `uncategorized` |

## LLM narrative (Groq)

Ledger uses the [Groq](https://console.groq.com) free tier to generate natural-language narratives from the computed metrics. Without an API key, it falls back to a deterministic template — both paths produce the same data, only the prose differs.

### Set your API key

**Docker (recommended):**
```bash
# Create .env at the project root — Docker Compose loads it automatically
cp .env.example .env

# Edit .env and paste your key
GROQ_API_KEY=gsk_your_key_here

# Then start normally — no extra flags
docker compose up -d
```

**Native:**
```bash
cp backend/.env.example backend/.env

# Edit backend/.env and paste your key
GROQ_API_KEY=gsk_your_key_here
```

Both `.env` files are gitignored and loaded automatically (`python-dotenv` for native, Docker Compose's built-in `.env` support for Docker).

## Authentication

Ledger requires a user account to access the dashboard, upload, and reports pages.

### Sign up / Sign in

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/signup` | POST | Create an account with `email`, `password` (min 8 chars), optional `display_name` |
| `/api/auth/login` | POST | Returns JWT access + refresh tokens |
| `/api/auth/me` | GET | Returns the current user (requires Bearer token) |

All analysis and report endpoints are protected — users can only see their own data.

### JWT configuration

Set these in your `.env` (both Docker and native):

| Variable | Default | Notes |
|---|---|---|
| `JWT_SECRET` | — | **Required.** Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Short-lived access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Long-lived refresh token |

### Frontend flow

- Unauthenticated users see a full-page sign-in / sign-up form
- Tokens are stored in `localStorage` and attached to every API request via `Authorization: Bearer <token>`
- The sidebar shows the user's email and a **Sign out** button
- On page reload, the stored token is validated against `GET /api/auth/me`

## Deploying

### Backend → Render (free tier)

1. Push this repo to GitHub
2. On Render: **New → Web Service → connect repo**
3. Render auto-detects `render.yaml` (Docker, points at `backend/Dockerfile`)
4. Add your `GROQ_API_KEY` as an environment variable in the Render dashboard
5. Render's free tier spins down after inactivity — first request takes ~30–60s to wake up

### Frontend → Vercel / Netlify (free)

1. Import the repo, set root directory to `frontend/`
2. Build command: `npm run build`
3. Output directory: `dist`
4. Once deployed, set the API endpoint (top-bar API Config) to your Render URL

### Database

**Default:** PostgreSQL 16 via Docker Compose (persistent volume, auto-created tables).

**Alternative:** Any PostgreSQL 16 instance — set `DATABASE_URL` env var. The backend auto-creates tables on startup using SQLAlchemy's `create_all`.

_For local dev without Docker, [Neon's free Postgres](https://neon.tech) or a local `pg` install both work. Set `DATABASE_URL` to `postgresql+asyncpg://user:pass@host:5432/dbname`._

## Sample data

```bash
cd sample_data
python generate_sample.py
```

Generates a synthetic 12-month transaction CSV with an engineered customer-concentration issue and a seasonal mid-year dip — the demo always has something interesting to show. Entirely fabricated, safe to commit and share.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite 6 |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg |
| Data | Pandas, NumPy |
| Auth | JWT (python-jose), bcrypt (passlib), HTTPBearer, per-user data isolation |
| Narrative | Groq API (Llama 3.3 70B) or deterministic template |
| Testing | pytest, pytest-asyncio, httpx (30%+ coverage on core logic) |
| Deploy | Docker Compose, Dockerfiles, Render, Vercel / Netlify |

## Roadmap

- [x] Analysis history with PostgreSQL persistence
- [x] User authentication (signup / login / JWT)
- [x] Per-user data isolation
- [ ] PDF export of the memo
- [ ] Multi-file comparison (quarter-over-quarter)
- [ ] Additional bank export format support

---

<p align="center">Built for underwriters who need answers they can trust — not black boxes.</p>
