# Ledger — SME Cash-Flow Underwriting Platform

[![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![React](https://img.shields.io/badge/react-19-61DAFB)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)]()

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
├── frontend/              React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── components/    UI components (Sidebar, Intake, Results, Chart…)
│   │   ├── api/           API client (health check, analyze)
│   │   ├── types/         TypeScript interfaces matching the backend schema
│   │   └── data/          Built-in sample dataset
│   └── dist/              Static build output (for deployment)
│
├── backend/               FastAPI (Python 3.11+)
│   ├── app/
│   │   ├── routers/       POST /api/analyze endpoint
│   │   ├── services/
│   │   │   ├── feature_extraction.py   Pandas computations — every metric
│   │   │   ├── risk_scoring.py         Deterministic rules, fully unit-tested
│   │   │   └── narrative_generator.py  LLM (Groq) or template fallback
│   │   ├── models.py      Shared domain models
│   │   └── schemas.py     Pydantic API response models
│   └── tests/             14 tests covering extraction, scoring, and API
│
├── sample_data/           Synthetic data generator
└── render.yaml            Render.com deploy config
```

## Quick start

### Prerequisites

- **Python 3.11+** and **Node.js 18+**
- A free [Groq API key](https://console.groq.com) _(optional — works without one)_

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`.  
_Without a `GROQ_API_KEY`, it automatically uses a deterministic template narrative — no external dependencies needed._

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. The frontend defaults to `http://localhost:8000` for the API — adjust via the **API Config** button in the top bar if needed.

### 3. Run it

1. Click **"Use sample data instead"** (or drop a CSV)
2. Click **"Analyze cash flow"**
3. Review the metrics, risk flags, chart, and narrative

### 4. Run tests

```bash
cd backend
python -m pytest tests/ -v
```

14 tests covering feature extraction edge cases, risk scoring rules, and the API.

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

```powershell
# Windows (PowerShell)
$env:GROQ_API_KEY="gsk_your_api_key_here"

# macOS / Linux
# export GROQ_API_KEY="gsk_your_api_key_here"
```

Then restart the backend. The key is session-scoped — set it again after closing the terminal, or add it to your shell profile.

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

Not required — the MVP is stateless request/response. For persistence, [Neon's free Postgres](https://neon.tech) is the natural next step.

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
| Data | Pandas, NumPy |
| Narrative | Groq API (Llama 3.3 70B) or deterministic template |
| Testing | pytest, httpx (30%+ coverage on core logic) |
| Deploy | Docker, Render, Vercel / Netlify |

## Roadmap

- [ ] Analysis history per business (Neon Postgres)
- [ ] PDF export of the memo
- [ ] Multi-file comparison (quarter-over-quarter)
- [ ] Additional bank export format support
- [ ] Auth and multi-tenant isolation

---

<p align="center">Built for underwriters who need answers they can trust — not black boxes.</p>
