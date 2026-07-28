<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Ledger-Underwriting-3b82f6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0zIDN2MThoMTgiLz48cGF0aCBkPSJNNyAxNmw0LTggNCA0IDQtNiIvPjwvc3ZnPg==">
    <img alt="Ledger" src="https://img.shields.io/badge/Ledger-Underwriting-3b82f6?style=for-the-badge">
  </picture>
</p>

# Ledger — SME Cash-Flow Underwriting

**Turn a raw bank CSV into an auditable risk memo in seconds.** Every metric is computed deterministically — the LLM explains numbers, it never invents them.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=fff)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=fff)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=fff)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=fff)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=fff)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-15_ passing-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

---

## Quick start

```bash
cp .env.example .env          # add GROQ_API_KEY (optional) and JWT_SECRET
docker compose up -d          # start PostgreSQL, backend, frontend
```

Open **http://localhost:5173** — click "Try demo" or sign up.

> After pulling new code: `docker compose build frontend && docker compose up -d`

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| PostgreSQL | localhost:5432 |

---

## Features

- **Deterministic metrics** — revenue volatility, customer concentration, negative-flow streaks, seasonal patterns — every figure links to a pandas computation
- **Risk scoring** — rule-based engine assigns a score and band (low / medium / high) with explainable flags
- **LLM narrative** — optional Groq-powered prose; falls back to a deterministic template that explains the same numbers
- **PDF export** — one-click download of the full memo as an A4 PDF
- **Multi-currency** — 10 currencies supported; all amounts format to the selected currency
- **Report history** — every analysis is saved and scoped to your account; revisit, compare, or delete past memos
- **Compare periods** — diff two reports side-by-side with delta values for every key metric
- **Transaction table** — sortable view of all parsed transactions
- **Demo mode** — explore the full workflow without creating an account
- **Dark mode** — toggle from the sidebar, persisted across sessions

---

## Architecture

```
frontend/         React 19 + TypeScript + Vite
backend/          FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL
sample_data/      Synthetic CSV generator
```

The pipeline:

```
Upload CSV → pandas extracts 20+ metrics → risk rules score & flag → narrative generated (Groq or template)
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite 6 |
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg |
| Auth | JWT (python-jose), bcrypt (passlib), per-user data isolation |
| LLM | Groq API (Llama 3.3 70B) or deterministic template |
| Data | Pandas, NumPy |
| Testing | pytest, pytest-asyncio, httpx |
| Infra | Docker Compose, Render |

---

## CSV format

| Column | Required | Notes |
|---|---|---|
| `date` | Yes | Any pandas-parseable date format |
| `amount` | Yes | Positive = inflow, negative = outflow |
| `counterparty` | Yes | Used for concentration risk analysis |
| `category` | No | e.g. `revenue`, `payroll` — defaults to `uncategorized` |

---

## Authentication

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/signup` | POST | Create account (email, password ≥8 chars, optional display_name) |
| `/api/auth/login` | POST | Returns JWT access + refresh tokens |
| `/api/auth/me` | GET | Current user info (requires Bearer token) |

All analysis and report endpoints are scoped to the authenticated user — users can only see their own data.

---

## Development

### Native (no Docker)

**Backend:**
```bash
cd backend
cp .env.example .env   # set DATABASE_URL, JWT_SECRET, GROQ_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Tests:**
```bash
cd backend
python -m pytest tests/ -v
```

### Environment variables

| Variable | Default | Required |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://cashflow:cashflow_dev@localhost:5432/cashflow` | Yes |
| `JWT_SECRET` | — | Yes (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `GROQ_API_KEY` | — | No (template narrative used without it) |
| `VITE_API_BASE` | `http://localhost:8000` | Frontend only |

---

## Deployment

**Backend:** Push to GitHub → [Render](https://render.com) "New → Web Service" → select repo (auto-detects `render.yaml`).  
**Frontend:** Import to [Vercel](https://vercel.com) or [Netlify](https://netlify.com) — root `frontend/`, build `npm run build`, output `dist`.  
**Database:** PostgreSQL 16 — Docker Compose for local, [Neon](https://neon.tech) or Render Postgres for production.

---

## Sample data

```bash
cd sample_data && python generate_sample.py
```

Generates 12 months of synthetic transactions with an engineered customer-concentration issue and a seasonal dip — the demo always has something interesting to show.

---

<p align="center">Built for underwriters who need answers they can trust — not black boxes.</p>
