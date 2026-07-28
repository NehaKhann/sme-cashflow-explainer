# Ledger — SME Cash-Flow Explainer

Turns a raw bank transaction export into an underwriter-readable cash-flow risk
memo. Every number in the final narrative traces back to a specific computed
value — the LLM is only ever allowed to explain figures it was given, never to
invent or restate them differently. This is the core engineering idea of the
project and the thing worth highlighting in interviews/write-ups.

## Why this exists

Small-business loan underwriting for thin-file borrowers (no long credit
history) still leans on a human reading raw bank statements to judge
seasonality, customer concentration risk, and cash-flow volatility. Existing
scoring tools output a number; almost none explain *why* in a way an
underwriter can audit. This project separates "compute the facts" (deterministic
pandas + rule-based risk scoring) from "explain the facts in prose" (LLM),
so the explanation layer can never introduce a number that isn't real.

## Architecture

```
frontend/ (static HTML/CSS/JS, no build step)
  │  fetch()
  ▼
backend/ (FastAPI)
  ├── feature_extraction.py   -- pandas: every number that can ever appear anywhere
  ├── risk_scoring.py         -- deterministic rules, no LLM, fully unit-tested
  └── narrative_generator.py  -- LLM (Groq free tier) explains pre-computed numbers only
  │
  ▼
Groq API (Llama 3.3 70B, free tier) — or a template fallback if no API key is set
```

## Local development

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Runs at `http://localhost:8000`.

Without a `GROQ_API_KEY` set, `/api/analyze` still works—it automatically falls back to a deterministic templated narrative, allowing you to develop and demo the application without any external dependencies.

## Enable Real LLM Responses (Groq)

To use real LLM-generated narratives instead of the fallback:

1. Create a free Groq account and generate an API key:
   - https://console.groq.com
   - No credit card is required for the free tier.

2. Set the `GROQ_API_KEY` environment variable.

### Windows (PowerShell)

In the same PowerShell window where you'll run the backend, execute:

```powershell
$env:GROQ_API_KEY="gsk_your_actual_api_key_here"
```

Example:

```powershell
$env:GROQ_API_KEY="gsk_abcd1234..."
```

> **Note:** This environment variable is only available for the current PowerShell session. You'll need to set it again after closing the terminal.

3. Verify the key is set:

```powershell
echo $env:GROQ_API_KEY
```

If the key is configured correctly, PowerShell will print your API key.

4. Start (or restart) the backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

The application will now use Groq to generate real LLM responses for `/api/analyze`.

### Frontend

No build step — it's plain HTML/CSS/JS.

```bash
cd frontend
python -m http.server 8080
```

Open `http://localhost:8080`. Use the "API endpoint configuration" section at
the bottom of the upload panel to confirm it's pointed at your backend
(defaults to `http://localhost:8000`).

Click **"Use sample data instead"** for an instant demo without needing a CSV —
it uses a small built-in synthetic dataset.

1. Click "Use sample data instead" (or drop a CSV)
2. Click "Analyze cash flow"
3. Wait for the loading spinner → results appear

### Running tests

```bash
cd backend
python -m pytest tests/ -v
```

14 tests covering feature extraction edge cases (missing columns, unparseable
dates, concentration math, negative-flow streak detection) and the risk-scoring
rules.

## Sample data

`sample_data/generate_sample.py` generates a synthetic 12-month transaction
history with an engineered customer-concentration issue and a seasonal
mid-year dip, so the demo always has something interesting to show. Entirely
fabricated — safe to commit and to point recruiters at.

```bash
cd sample_data
python3 generate_sample.py
```

## CSV format

| column | required | notes |
|---|---|---|
| `date` | yes | any pandas-parseable date format |
| `amount` | yes | signed: positive = inflow, negative = outflow |
| `counterparty` | yes | payer/payee name, used for concentration risk |
| `category` | no | e.g. `revenue`, `payroll`, `rent` — defaults to `uncategorized` |

## Deploying for free

**Backend → Render (free web service)**
1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo.
3. Render will detect `render.yaml` automatically (Docker runtime, points at
   `backend/Dockerfile`).
4. Add your `GROQ_API_KEY` as an environment variable in the Render dashboard
   (never commit it to the repo).
5. Note: Render's free tier spins down after inactivity — first request after
   idle takes ~30-60s to wake up. Worth a one-line note on your live demo link
   so it doesn't look broken.

**Frontend → Vercel or Netlify (free static hosting)**
1. Import the repo, set the root directory to `frontend/`.
2. No build command needed — it's static files.
3. Once deployed, open the site and set the API endpoint (in the collapsible
   config panel) to your Render URL.

**Database:** not required for the current MVP (stateless request/response).
If you add persistence (e.g. saving analysis history), Neon's free Postgres
tier is the natural next step — schema-ready via `pgvector` if you later want
to add similarity search across past analyses.

## Design notes

The frontend is intentionally framework-free — a static HTML/CSS/JS site
deploys to Vercel/Netlify with zero build configuration, which matters for a
portfolio piece meant to be clicked and trusted quickly. The visual language
(ruled "ledger" lines, monospace tabular figures, a rotated risk stamp) is
drawn directly from the artifact this tool replaces: a printed underwriting
memo. If you'd rather have this as a React/Next.js app for consistency with
your other projects, say so and I'll port it — the API contract won't change.

## Roadmap ideas (future, not in current MVP)

- Persist analysis history per business (Neon Postgres)
- PDF export of the memo (useful since underwriters often need a filable document)
- Multi-file comparison (quarter-over-quarter trend)
- Support additional bank export formats beyond the generic CSV schema
