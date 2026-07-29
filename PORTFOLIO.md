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
| **Hybrid Dataset Strategy** | Combine hand-written Q&A with curated Hugging Face finance datasets for breadth + precision | 37 custom pairs (Ledger-specific) + 300 examples from 5 `AdaptLLM/finance-tasks` configs (FPB, FiQA_SA, ConvFinQA, Headline, NER) |
| **Reproducibility Pipeline** | Ensure identical training runs produce identical weights | Fixed seed (torch + numpy + python) + deterministic cuDNN + SHA-256 dataset checksums |
| **Cross-Stage Validation** | Prevent silent training on stale or corrupted data | `prepare_dataset.py` writes SHA-256 hashes; `train.py` validates before training |
| **Config-Driven Training** | All hyperparameters in a shared JSON; CLI overrides take priority | `training_config.json` + `merge_config_cli()` across all 4 pipeline scripts |
| **Evaluation** | Quantitative + qualitative model assessment | Perplexity, BERTScore, ROUGE, and manual sample review |
---

### AI Architecture: Dual-Model Strategy

Ledger uses **two AI models** — a small locally fine-tuned model for development and experimentation, and a production-grade API for deployed inference.

| Role | Model | Where it runs | When it's used |
|---|---|---|---|
| **Local Chatbot** | Llama 3.2 3B fine-tuned via QLoRA → GGUF → Ollama | Your laptop (CPU/GPU) | Development, demos, pipeline showcase, experimentation |
| **Production Chatbot** | Groq API (`llama-3.3-70b-versatile`) | Groq's cloud infrastructure | Deployed app on Render (no GPU available) |

**Why train a local model at all if the deployed app uses Groq?**

1. **End-to-end ML pipeline** — the project includes a complete, reproducible training pipeline: dataset preparation → QLoRA fine-tuning → GGUF quantization → Ollama serving. This demonstrates real ML engineering skills far beyond calling an API.

2. **Full control** — every hyperparameter, dataset sample, and training seed is under our control. No vendor lock-in, no API pricing changes, no data sent to third parties during training.

3. **Experimentation** — we can rapidly iterate on architecture choices (rank, target modules, learning rate, dataset composition) without incurring per-request costs.

4. **Offline capability** — the local model runs entirely on-device with no internet dependency. Useful for demos in air-gapped environments or for underwriters who need data to stay on-premise.

5. **Portfolio signal** — shipping a production-grade ML pipeline that spans data collection, training, quantization, serving, and fail-over demonstrates the full ML lifecycle, not just inference.

**Why the hybrid dataset (custom + Hugging Face)?**

- **Custom Q&A** (37 pairs) ensures the model knows Ledger-specific details: how to upload a CSV, what each risk flag means, where to find the compare feature, etc. Public datasets don't contain this information.

- **Hugging Face finance datasets** (300 examples from 5 AdaptLLM configs) provide broad financial literacy — sentiment classification, financial QA, named entity recognition — without manual labeling. This teaches the model the language and concepts of finance, which the custom pairs then specialize.

- **The combination** gives us both depth (platform-specific accuracy) and breadth (general financial competence) with minimal manual effort.

**Fail-over in production:**
When deployed on Render (no GPU, no Ollama), the backend automatically switches to the Groq API via the `CHAT_PROVIDER=groq` environment variable. If Groq is unavailable, a deterministic template response is served — the system never returns a raw error to the user.

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
- **Dataset preparation**: hybrid strategy fusing hand-written domain-specific Q&A with curated Hugging Face finance datasets (5 configs from AdaptLLM/finance-tasks), train/eval splits, checksum integrity
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
- **Fail-open design**: LLM narrative falls back to deterministic template; chatbot falls back from local GGUF (Ollama) to Groq API to deterministic template, never returning a raw error

### Security & Reliability
- **JWT secrets**: validated at startup to prevent default-secret attacks
- **Password hashing**: bcrypt via passlib with configurable rounds
- **SQL injection prevention**: SQLAlchemy parameterized queries throughout
- **Input validation**: Pydantic models with custom field validators (email, password length, file format)
- **Error handling**: graceful degradation with fallback templates for every external service
- **Rate limiting**: per-endpoint limits via slowapi prevent brute-force auth attacks and API abuse

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
  │  • Compare reports (auto-diff) │
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

  ┌─ ML Pipeline (local dev) ──────────────────────┐
  │  prepare_dataset.py (custom QA + HF datasets)  │
  │       │                                         │
  │       ▼                                         │
  │  train.py (QLoRA on consumer GPU)               │
  │       │                                         │
  │       ▼                                         │
  │  quantize.py (merge adapters → GGUF)            │
  │       │                                         │
  │       ▼                                         │
  │  Ollama serve ◄── GGUF model ──► Local Chatbot  │
  └─────────────────────────────────────────────────┘

  Note: Deployed app on Render bypasses the local
  model and uses Groq API (no GPU required).
```

---

## Key Metrics

- **Analysis time**: ~3 seconds for 12 months of transactions
- **Training time**: ~20 minutes on NVIDIA RTX 3060 (8 GB VRAM); ~30 seconds on RTX 4050 (6 GB VRAM) for 2 epochs
- **Model size**: 3B parameters → 2.1 GB GGUF (Q4_K_M)
- **Dataset**: 337 Q&A pairs (37 custom + 300 from 5 Hugging Face `AdaptLLM/finance-tasks` configs)
- **Risk flags**: 7 distinct checks (volatility, concentration, seasonality, negative streaks, etc.)
- **Auto-trend**: every new analysis shows green/red deltas vs the previous report for the 4 key underwriting signals
- **PDF export**: < 1 second client-side generation
- **Test coverage**: 15+ backend tests for feature extraction + risk scoring
