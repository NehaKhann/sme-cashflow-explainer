<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Ledger-Underwriting-3b82f6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0zIDN2MThoMTgiLz48cGF0aCBkPSJNNyAxNmw0LTggNCA0IDQtNiIvPjwvc3ZnPg==">
    <img alt="Ledger" src="https://img.shields.io/badge/Ledger-Underwriting-3b82f6?style=for-the-badge">
  </picture>
</p>

# Ledger — SME Cash-Flow Underwriting

**Turn a raw bank CSV into an auditable risk memo in seconds.** Every metric is computed deterministically — the LLM explains numbers, it never invents them.

[![CI](https://github.com/NehaKhann/sme-cashflow-explainer/actions/workflows/ci.yml/badge.svg)](https://github.com/NehaKhann/sme-cashflow-explainer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=fff)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=fff)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=fff)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=fff)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=fff)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?logo=docker&logoColor=fff)](https://docker.com)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000?logo=ruff)](https://docs.astral.sh/ruff)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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
- **Compare periods** — auto-compare each new analysis vs the previous report; green/red deltas for net flow, risk score, volatility, and concentration
- **Transaction table** — sortable view of all parsed transactions
- **Demo mode** — explore the full workflow without creating an account
- **Dark mode** — toggle from the sidebar, persisted across sessions
- **Chatbot** — fine-tuned LLM (QLoRA + Ollama) for platform Q&A and underwriting concepts; falls back to Groq API when deployed

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
Upload CSV → pandas extracts 20+ metrics → risk rules score & flag → auto-compare vs previous report → narrative generated (Groq or template) → optional chatbot Q&A (fine-tuned model via Ollama, or Groq API when deployed)
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite 6 |
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg |
| Auth | JWT (python-jose), bcrypt (passlib), per-user data isolation, DB-backed refresh rotation |
| LLM | Groq API (Llama 3.3 70B) or deterministic template |
| Chatbot | Fine-tuned Llama 3.2 3B via QLoRA, served via Ollama locally; Groq API when deployed |
| ML Pipeline | PyTorch, Hugging Face Transformers 4.x, PEFT, bitsandbytes, TRL 0.12, datasets 5.x, Ollama |
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
| `/api/auth/refresh` | POST | Rotate refresh token (returns new access + refresh pair) |

All analysis and report endpoints are scoped to the authenticated user — users can only see their own data. The trend comparison reads the user's immediately preceding report for deltas.

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
| `CHAT_PROVIDER` | `ollama` | No — set to `groq` for deployed environments without local Ollama |
| `CHAT_MODEL` | `ledger-chatbot` (ollama) / `llama-3.3-70b-versatile` (groq) | No |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | No — only used when `CHAT_PROVIDER=ollama` |
| `CORS_ORIGINS` | `http://localhost:5173` | No — comma-separated list of allowed origins |

### Rate limiting

| Endpoint | Limit |
|---|---|
| `POST /api/auth/signup` | 5 / minute |
| `POST /api/auth/login` | 10 / minute |
| `POST /api/auth/refresh` | 10 / minute |
| `POST /api/chat` | 20 / minute |
| All others | 60 / minute |

---

## Deployment

**Backend:** Push to GitHub → [Render](https://render.com) "New → Web Service" → select repo (auto-detects `render.yaml`).  
**Frontend:** Import to [Vercel](https://vercel.com) or [Netlify](https://netlify.com) — root `frontend/`, build `npm run build`, output `dist`. Set `VITE_API_BASE` to your Render API URL (e.g. `https://cashflow-explainer-api-ojxv.onrender.com`).  
**Database:** PostgreSQL 16 — Docker Compose for local, [Neon](https://neon.tech) or Render Postgres for production.  
**CORS:** Set `CORS_ORIGINS` on the Render backend to your Vercel URL (comma-separated if you have several), e.g. `https://cashflow-pi-liard.vercel.app`. Redeploy the backend after changing it.  
**Chatbot:** Set `CHAT_PROVIDER=groq` on the backend service — the chatbot uses the Groq API instead of a local Ollama instance (no Ollama on Render).

---

## Chatbot — ML Fine-Tuning Pipeline

The chatbot is a small language model fine-tuned on cash-flow underwriting knowledge using **QLoRA** and served locally via **Ollama**.

When deployed (e.g. on Render where Ollama isn't available), set `CHAT_PROVIDER=groq` in the backend environment — the chatbot uses the **Groq API** (`llama-3.3-70b-versatile`) instead, requiring no local model or GPU.

### Training

Requires a GPU with ≥6 GB VRAM (RTX 4050 / 4060 etc. work with the settings below).

**1. Setup**

```bash
cd ml
pip install -r requirements.txt
```

If you get huggingface-hub / datasets version conflicts:

```bash
pip install "datasets>=4,<6" "huggingface-hub>=1.0"
```

Verify GPU is detected:

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '- Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

If it shows `CUDA: False`, reinstall PyTorch with CUDA:

```bash
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**2. Build the training dataset**

```bash
python prepare_dataset.py --with-hf
```

**3. Fine-tune with QLoRA**

Recommended for 6 GB GPUs:

```bash
python train.py --config training_config.json --disable-wandb --batch-size 2 --max-seq-len 512
```

Other useful variants:

```bash
python train.py --disable-wandb
python train.py --config training_config.json --disable-wandb --lr 1e-4
```

At the end of training a folder is created, e.g.:

```text
output/ledger-chatbot-YYYYMMDD_HHMM/
```

**4. Merge LoRA adapters**

Because 6 GB GPUs often run out of memory, merge on CPU:

```powershell
# Find the latest training folder automatically
$latest = Get-ChildItem output -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Using folder: $($latest.Name)"

python -c "
import os, torch, gc
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

torch.cuda.empty_cache()
gc.collect()

adapter = r'$($latest.FullName)'
merged = os.path.join(adapter, 'merged')
os.makedirs(merged, exist_ok=True)

print('Loading base model on CPU (this is normal for 6 GB GPUs)...')
base = AutoModelForCausalLM.from_pretrained(
    'unsloth/Llama-3.2-3B-Instruct',
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    device_map='cpu',
    trust_remote_code=True,
)

print('Loading + merging LoRA adapters...')
model = PeftModel.from_pretrained(base, adapter)
model = model.merge_and_unload()

print('Saving merged model (may take a few minutes)...')
model.save_pretrained(merged, safe_serialization=True)

print('Saving tokenizer...')
tok = AutoTokenizer.from_pretrained(
    'unsloth/Llama-3.2-3B-Instruct',
    trust_remote_code=True
)
tok.save_pretrained(merged)

print('Done! Merged model saved to:')
print(merged)
"
```

**5. Convert to GGUF (for Ollama)**

Use the official converter that comes with the project (`llama.cpp-temp`):

```powershell
# Create output folder
New-Item -ItemType Directory -Path "$($latest.FullName)\gguf" -Force | Out-Null

# Convert
python llama.cpp-temp\convert_hf_to_gguf.py `
    "$($latest.FullName)\merged" `
    --outfile "$($latest.FullName)\gguf\ledger-chatbot-fp16.gguf" `
    --outtype f16
```

**6. Create a correct Modelfile**

```powershell
@"
# Modelfile for Ledger Chatbot
FROM ./gguf/ledger-chatbot-fp16.gguf

SYSTEM """You are Ledger Assistant, an expert in cash-flow underwriting and financial analysis. You help users understand the Ledger platform, interpret financial metrics, and analyze cash-flow data. Answer concisely, accurately, and always ground your responses in the computed data."""

TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{{ .Response }}<|eot_id|>"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 512
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
"@ | Set-Content "$($latest.FullName)\Modelfile" -Encoding utf8
```

**7. Register the model with Ollama**

```powershell
ollama create ledger-chatbot -f "$($latest.FullName)\Modelfile"
```

**8. Test the model**

```powershell
ollama run ledger-chatbot
```

**9. Start Ollama server (so the backend can talk to it)**

```bash
ollama serve
```

### GPU vs CPU

| Mode | Setup | Speed |
|------|-------|-------|
| GPU (CUDA) | NVIDIA GPU + CUDA 12.x | ~15–40 min training |
| GPU (Metal) | Apple Silicon (M1+) | ~30–60 min training |
| CPU | No GPU | Several hours (not recommended) |

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
| `ml/data/custom_qa.jsonl` | Hand-written Q&A about Ledger and underwriting | 37 examples |
| Hugging Face (optional) | [`AdaptLLM/finance-tasks`](https://huggingface.co/datasets/AdaptLLM/finance-tasks) — FPB, FiQA_SA, ConvFinQA, Headline, NER | 300 examples (60/config) |

See `ml/README.md` for full documentation including config reference, data integrity checks, hyperparameter tuning, GGUF quantization options, and evaluation.

---

## Sample data

```bash
cd sample_data && python generate.py
```

Generates 10 curated CSV files, each targeting a specific scenario:

| File | What it tests |
|---|---|
| `01_healthy_business.csv` | Stable, diversified → low risk score |
| `02_customer_concentration.csv` | 60%+ from one customer → concentration flag |
| `03_seasonal_dip.csv` | Summer revenue drops 60% → seasonality flag |
| `04_negative_streak.csv` | 12 months net-negative → streak flag |
| `05_revenue_volatility.csv` | Revenue swings 3–15K → volatility flag |
| `06_high_growth.csv` | +$600/mo growth → no flags |
| `07_missing_columns.csv` | Missing `counterparty` → upload error |
| `08_empty.csv` | Header only → no data error |
| `09_single_month.csv` | Only 1 month → insufficient data |
| `10_bad_amounts.csv` | Non-numeric amounts → parse error |

---

<p align="center">Built for underwriters who need answers they can trust — not black boxes.</p>
