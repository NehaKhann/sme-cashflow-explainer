# Ledger — SME Cash-Flow Underwriting

## Brief Intro

Ledger transforms raw bank transaction CSVs into audit-ready, underwriter-facing risk memos in seconds. Every metric is computed deterministically from the data — the LLM explains those numbers, never invents them.

The platform bridges a critical gap in small-business lending: traditional underwriting is too slow for modern fintech, but black-box AI scoring is too opaque for regulated lending decisions. Ledger gives underwriters **traceable metrics**, **explainable risk scores**, and an **AI-assisted narrative** — all from a single CSV upload.

---

## Target Users

- **Small-business lenders** at community banks and credit unions
- **Underwriters** at fintech lending platforms
- **Portfolio managers** assessing SME credit risk across a book of business
- **Business owners** performing self-service cash-flow health checks
- **Product demos** for B2B fintech sales teams

---

## Market Gap

| Problem | Traditional approach | Black-box AI | Ledger |
|---|---|---|---|
| Speed | 3–5 days manual review | Instant | **< 5 seconds** |
| Explainability | Narrative is hand-written | "Our model said so" | **Every number traced to code** |
| Data requirements | Financial statements, tax returns | Large training dataset | **Just a bank CSV** |
| Audit readiness | Full paper trail | Impossible | **Deterministic + reproducible** |
| Access | Expensive analysts | Expensive ML team | **Single Python script** |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite 6 | Modern SPA with type safety and fast HMR |
| **Backend** | Python 3.11, FastAPI, Pydantic v2 | Async-first, auto-documented API |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async) | Reliable, transaction-safe, JSONB for flexible memo storage |
| **Auth** | JWT (python-jose), bcrypt, refresh tokens | Session-less, per-user data isolation |
| **PDF** | jsPDF, html2canvas | Client-side A4 memo export with no server overhead |
| **Containerization** | Docker Compose | One-command local setup |
| **Deployment** | Render (backend), Vercel (frontend) | Free-tier cloud hosting with zero config |

### Machine Learning

| Technique | Purpose | Implementation |
|---|---|---|
| **QLoRA** (Quantized Low-Rank Adaptation) | Fine-tune a 3B parameter LLM on a single consumer GPU (8 GB VRAM) | 4-bit NF4 quantization + LoRA adapters; only ~0.1% of parameters trained |
| **PEFT** (Parameter-Efficient Fine-Tuning) | Train without modifying the base model | Hugging Face PEFT + LoRA config (rank=16, alpha=32) |
| **GGUF Quantization** | Convert the merged model to a CPU-friendly format for local inference | llama.cpp convert + quantize (Q4_K_M, Q5_K_M, Q8_0) |
| **Chat Template Fine-Tuning** | Teach the model platform-specific Q&A via structured conversations | Multi-turn messages formatted with `apply_chat_template()` |
| **Reproducibility Pipeline** | Ensure identical training runs produce identical weights | Fixed seed (torch + numpy + python) + deterministic cuDNN + SHA-256 dataset checksums |
| **Cross-Stage Validation** | Prevent silent training on stale or corrupted data | `prepare_dataset.py` writes SHA-256 hashes; `train.py` validates before training |
| **Config-Driven Training** | All hyperparameters in a shared JSON; CLI overrides take priority | `training_config.json` + `merge_config_cli()` across all 4 pipeline scripts |
| **Evaluation** | Quantitative + qualitative model assessment | Perplexity, BERTScore, ROUGE, and manual sample review |

---

## Learning Outcomes

### Full-Stack Web Development
- Building a **React 19** SPA with TypeScript: component architecture, hooks, context, custom hooks (`useDarkMode`)
- Managing complex async state: concurrent API calls, optimistic updates, error boundaries, SSE streams
- **Responsive design** with CSS breakpoints for mobile/tablet/desktop
- **Dark mode** implementation with localStorage persistence

### Backend Engineering
- **FastAPI** async routes with Pydantic v2 request/response models
- **SQLAlchemy 2.0** async ORM with PostgreSQL including JSONB, UUID PKs, and relationship cascading
- **JWT authentication** with access + refresh token rotation
- **CORS** security: credentialed requests with explicit origin allowlists
- **File upload** handling with size limits, format validation, and streaming
- **SSE streaming** for real-time chatbot responses

### ML & LLM Ops
- **QLoRA** fine-tuning: loading 4-bit quantized models, applying LoRA adapters, merging and saving
- **Dataset preparation**: converting raw Q&A into chat-template format, train/eval splits, checksum integrity
- **Quantization pipeline**: merging adapters → converting to GGUF → quantizing → serving via Ollama
- **Config management**: shared JSON config + CLI override merging across all scripts
- **GPU/CPU detection**: auto-select CUDA, MPS, or CPU with appropriate dtype and quantization settings
- **Reproducibility**: fixed seeds, deterministic algorithms, cross-stage checksum validation

### Infrastructure & DevOps
- **Docker Compose** multi-service orchestration (PostgreSQL, backend, frontend)
- **Docker optimization**: `.dockerignore`, layer caching, slim base images
- **Render deployment**: Blueprint-as-code with managed PostgreSQL + Docker web service
- **Vercel deployment**: Vite SPA with API proxy configuration
- **Environment management**: `.env.example` documentation, `render.yaml` as infrastructure-as-code
- **Git workflow**: staged commits with conventional commit messages, .gitignore hygiene

### Software Design Patterns
- **Provider pattern** for auth context across the component tree
- **Custom hooks** to encapsulate reusable state logic (dark mode, API health)
- **Service layer** separation (feature extraction → risk scoring → narrative generation)
- **Dependency injection** via FastAPI's `Depends()` for database sessions and auth
- **Strategy pattern** for chat providers (Ollama local vs Groq API) via environment variable
- **Fail-open design**: LLM narrative falls back to deterministic template; chatbot falls back from Ollama to Groq

### Security & Reliability
- **JWT secrets**: validated at startup to prevent default-secret attacks
- **Password hashing**: bcrypt via passlib with configurable rounds
- **SQL injection prevention**: SQLAlchemy parameterized queries throughout
- **Input validation**: Pydantic models with custom field validators (email, password length, file format)
- **Error handling**: graceful degradation with fallback templates for every external service

---

## Architecture Diagram

```
User's Browser (React SPA)
        │
        │ HTTPS
        ▼
  ┌─ Vercel (CDN) ─────────────────┐
  │  Frontend (React 19 + Vite)    │
  │  • Upload CSV                  │
  │  • View risk memo              │
  │  • Compare reports             │
  │  • Chat with AI assistant      │
  │  • Export PDF                  │
  └──────────────┬─────────────────┘
                 │
                 │ HTTPS + Auth (JWT Bearer)
                 ▼
  ┌─ Render (Docker) ────────────────────┐
  │  Backend (FastAPI + Python 3.11)     │
  │                                      │
  │  POST /api/analyze ─► Feature Ext.   │
  │       │         ─► Risk Scoring      │
  │       │         ─► Narrative Gen.    │
  │       ▼                              │
  │  PostgreSQL 16 ◄── Report Storage    │
  │                                      │
  │  POST /api/chat ───► Groq API        │
  │       │         ──► (or Ollama)      │
  │       ▼         (SSE stream)         │
  └──────────────────────────────────────┘

  ┌─ ML Pipeline (local / CI) ───────────┐
  │  prepare_dataset.py ─► train.py      │
  │       │         ─► quantize.py       │
  │       ▼         ─► evaluate.py       │
  │  Ollama ◄── GGUF model ─► Chatbot    │
  └──────────────────────────────────────┘
```

---

## Key Metrics

- **Analysis time**: ~3 seconds for 12 months of transactions
- **Training time**: ~20 minutes on NVIDIA RTX 3060 (8 GB VRAM)
- **Model size**: 3B parameters → 2.1 GB GGUF (Q4_K_M)
- **Dataset**: 600+ Q&A pairs (hand-written + Hugging Face financial datasets)
- **Risk flags**: 7 distinct checks (volatility, concentration, seasonality, negative streaks, etc.)
- **PDF export**: < 1 second client-side generation
- **Test coverage**: 15+ backend tests for feature extraction + risk scoring
