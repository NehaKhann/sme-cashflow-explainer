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
[![Tests](https://img.shields.io/badge/tests-15__passing-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)

---

## Quick start

```bash
cp .env.example .env          # add GROQ_API_KEY (optional) and JWT_SECRET
docker compose up -d          # start PostgreSQL, backend, frontend
```

Open **http://localhost:5173** — click "Try demo" or sign up.

> After pulling new code: `docker compose build backend frontend && docker compose up -d`
> To reset (delete database): `docker compose down -v`

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
- **Chatbot** — fine-tuned LLM (QLoRA + Ollama) for platform Q&A and underwriting concepts

---

## Architecture

```
frontend/         React 19 + TypeScript + Vite
backend/          FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL
ml/               Fine-tuning pipeline (QLoRA + GGUF + Ollama)
sample_data/      Synthetic CSV generator
```

The pipeline:

```
Upload CSV → pandas extracts 20+ metrics → risk rules score & flag → narrative generated (Groq or template) → optional chatbot Q&A (fine-tuned model via Ollama)
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
| Chatbot | Fine-tuned Llama 3.2 3B via QLoRA, served via Ollama |
| ML Pipeline | PyTorch, Hugging Face Transformers, PEFT, bitsandbytes, TRL, Ollama |
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

## Chatbot — ML Fine-Tuning Pipeline

The chatbot is a small language model fine-tuned on cash-flow underwriting knowledge using **QLoRA** and served locally via **Ollama**.

### Training

Requires a GPU with ≥8 GB VRAM for reasonable speed. The script auto-detects your GPU (NVIDIA CUDA or Apple Metal).

```bash
cd ml
pip install -r requirements.txt
python prepare_dataset.py --with-hf              # build dataset + writes checksum
python train.py                                  # QLoRA fine-tune (validates checksum)
python train.py --config my_config.json          # use a custom config file
python quantize.py --adapters ./output/...       # merge + GGUF
ollama create ledger-chatbot -f ./output/.../Modelfile
ollama serve                                     # backend proxies here
```

**Config priority:** CLI arg > `training_config.json` > built-in default. All four scripts (`prepare_dataset.py`, `train.py`, `quantize.py`, `evaluate.py`) accept `--config` and share the same config file.

**Data integrity:** `train.py` validates SHA-256 hashes of the dataset against checksums written by `prepare_dataset.py`, preventing silent training on stale or corrupted data.

**GPU vs CPU:**

| Mode | Setup | Speed |
|---|---|---|
| **GPU (CUDA)** | NVIDIA GPU, CUDA 12.x, `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124` | ~15-30 min training |
| **GPU (Metal)** | Apple Silicon Mac (M1+), PyTorch MPS backend | ~30-60 min training |
| **CPU** | No GPU, `pip install torch torchvision torchaudio` | Several hours (not recommended for training) |

Ollama also uses the GPU automatically when available — verify with `ollama run ledger-chatbot` and check GPU usage in Task Manager (Windows) or `nvidia-smi`.

### What it learns

- Platform features (upload, analyze, compare, export)
- Financial metrics (volatility, concentration, seasonality)
- Risk scoring methodology
- CSV format and requirements
- Architecture and deployment

### Approach

| Technique | What it does |
|---|---|
| **QLoRA** | 4-bit NF4 quantization + low-rank adapters — fine-tune a 3B model on a single GPU |
| **PEFT** | Only ~0.1% of parameters are trainable; base model stays frozen |
| **GGUF** | Converts the merged model to a CPU-efficient format for Ollama |
| **Ollama** | Serves the quantized model locally with a REST API, GPU-accelerated |
| **Config** | Shared `training_config.json` + CLI overrides; all scripts accept `--config` |
| **Checksums** | Dataset SHA-256 hashes validated across prepare/train stages |

### Dataset

| Source | Description | Size |
|---|---|---|
| `ml/data/custom_qa.jsonl` | Hand-written Q&A about Ledger and underwriting | 50 examples |
| Hugging Face (optional) | [`financial_phrasebank`](https://huggingface.co/datasets/financial_phrasebank), [`AdaptLLM/finance-tasks`](https://huggingface.co/datasets/AdaptLLM/finance-tasks) | ~600 examples |

See `ml/README.md` for full documentation including config reference, data integrity checks, hyperparameter tuning, GGUF quantization options, and evaluation.

---

## Sample data

```bash
cd sample_data && python generate_sample.py
```

Generates 12 months of synthetic transactions with an engineered customer-concentration issue and a seasonal dip — the demo always has something interesting to show.

---

<p align="center">Built for underwriters who need answers they can trust — not black boxes.</p>
