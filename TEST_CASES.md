# Test Cases — Ledger Cash-Flow Underwriting

## Setup

```bash
cd sample_data
python generate_sample.py        # creates sme_transactions_sample.csv
```

The sample has 12 months of data with:
- **Customer concentration** — Acme Retail Co dominates revenue
- **Seasonal dip** — June/July revenue drops from ~$8K to ~$3.5K
- **Negative streaks** — multiple months of net-negative cash flow

---

## 1. Demo mode (no account)

| Step | Action | Expected result |
|---|---|---|
| 1 | Open the deployed URL | Landing page loads with hero, feature cards, dark mode toggle |
| 2 | Click **Try Demo** | Auto-login as demo user, sidebar shows Upload + Reports tabs |
| 3 | Upload `sme_transactions_sample.csv` | File uploads, analyzes, risk memo renders with score + flags |
| 4 | Click any flag (e.g. revenue volatility) | Scrolling or highlight works |
| 5 | Click **Export PDF** | A4 PDF downloads with full memo |
| 6 | Click **View Transactions** | Sortable transaction table with pagination |
| 7 | Close tab / refresh | Demo session persists until explicit logout |

---

## 2. Full auth flow

| Step | Action | Expected result |
|---|---|---|
| 1 | Click **Sign Up** | Sign-up card with email, password, display name |
| 2 | Fill form (password ≥ 8 chars) | Account created, auto-logged into dashboard |
| 3 | Click **Logout** | Redirected to landing page |
| 4 | Click **Sign In** | Login card appears |
| 5 | Enter credentials | Dashboard loads with empty report list |
| 6 | Upload a CSV | Analysis runs, report saved to account |
| 7 | Logout → Login again | Report list shows the previous analysis |

### Edge cases

| Test | Expected |
|---|---|
| Sign up with existing email | Error: email already registered |
| Login with wrong password | Error: invalid credentials |
| Sign up with password < 8 chars | Error: password too short |

---

## 3. Upload & analysis

### Happy path

| Step | Action | Expected |
|---|---|---|
| 1 | Click **Upload** tab | Drag-drop zone + IntakeSection with currency selector |
| 2 | Drop `sme_transactions_sample.csv` | File accepted, preview shows row count |
| 3 | Select **EUR** currency dropdown | Dropdown shows 10 currencies |
| 4 | Click **Analyze** | Spinner → risk memo renders |
| 5 | Verify metrics | values match computed output |
| 6 | Check risk flags | At least `REVENUE_VOLATILITY` and `CUSTOMER_CONCENTRATION` should fire |

### Bad CSV

| Test | Expected |
|---|---|
| Upload a `.txt` or image | Error: only CSV accepted |
| Upload CSV missing `amount` column | Error: missing required column |
| Upload CSV with all non-numeric `amount` | Error: cannot parse amounts |
| Upload empty CSV | Error: no data rows |

### Multi-upload

| Test | Expected |
|---|---|
| Analyze twice | Two reports in the Reports list |
| Delete one report | Only that report removed |
| Use **Clear All** | All reports deleted |

---

## 4. Report history & compare

### Reports list

| Step | Action | Expected |
|---|---|---|
| 1 | Upload 2+ CSVs | Reports tab shows all with timestamps |
| 2 | Click a report row | Risk memo loaded from database |
| 3 | Refresh page → navigate to Reports → click | Persisted — data survives reload |

### Compare

| Step | Action | Expected |
|---|---|---|
| 1 | With ≥2 reports, click **Compare** | Two dropdowns to select reports |
| 2 | Pick report A and report B | Side-by-side view with deltas |
| 3 | Compare the deltas | Green = improvement, red = worsening |
| 4 | Close compare | Back to report list |

---

## 5. Chatbot

### Local (CHAT_PROVIDER=ollama)

| Step | Action | Expected |
|---|---|---|
| 1 | Click FAB (bottom-right circle) | Chat panel slides up |
| 2 | Type "What does revenue volatility mean?" | Streaming response from fine-tuned model |
| 3 | Type "How do I upload a CSV?" | Model answers from training data |
| 4 | Click **Clear** | Message history erased |
| 5 | Click FAB again | Panel closes |

### Deployed (CHAT_PROVIDER=groq)

| Step | Action | Expected |
|---|---|---|
| 1 | Open chatbot | Works identically, but uses Groq API |
| 2 | Ask platform questions | Answers may differ since it's a general model |
| 3 | Verify GROQ_API_KEY is set | If missing, chatbot returns error message |

### Error states

| Test | Expected |
|---|---|
| Ollama not running (local) | "Cannot connect to Ollama" error in chat |
| GROQ_API_KEY missing (deployed) | "GROQ_API_KEY is not set" error |
| Network disconnect mid-stream | SSE stream cuts, error shown in UI |

---

## 6. Dark mode

| Step | Action | Expected |
|---|---|---|
| 1 | Click dark toggle (landing page header) | Full page switches to dark theme |
| 2 | Click dark toggle (sidebar bottom) | Also toggles, state is shared |
| 3 | Refresh page | Dark mode persists (localStorage) |
| 4 | Toggle off | Returns to light theme |
| 5 | Try demo with dark mode on | All pages render correctly in dark |

---

## 7. PDF export

| Step | Action | Expected |
|---|---|---|
| 1 | Open any risk memo | **Export PDF** button visible |
| 2 | Click **Export PDF** | PDF downloads within 1-2 seconds |
| 3 | Open PDF | A4 layout, all metrics, narrative, flags rendered |
| 4 | Compare export with on-screen data | Every number matches exactly |

---

## 8. Responsive / mobile

| Step | Viewport | Expected |
|---|---|---|
| 1 | ≤900px | Top nav collapses to hamburger menu |
| 2 | ≤768px | Feature cards stack vertically |
| 3 | ≤640px | Sidebar becomes bottom drawer |
| 4 | ≤480px | Chatbot goes full-screen (100% × 100%) |
| 5 | Mobile | Upload, analyze, compare all work |

---

## 9. Performance

| Test | Expected |
|---|---|
| Upload a CSV with 5000 rows | Analysis completes within a few seconds |
| Rapid-click Analyze twice | Second request waits for first, no duplicate reports |
| Open chatbot while analysis running | Both work independently (no blocking) |
| Switch tabs quickly | No UI freezes or layout shifts |

---

## 10. ML pipeline (local only)

```bash
cd ml
pip install -r requirements.txt
python prepare_dataset.py --with-hf              # builds + validates
python train.py                                   # QLoRA fine-tune
python quantize.py --adapters ./output/<run>      # merge → GGUF
ollama create ledger-chatbot -f ./output/<run>/Modelfile
ollama serve
```

| Test | Expected |
|---|---|
| Prepare without Hugging Face | Uses only local `custom_qa.jsonl` (50 examples) |
| Train on CPU (no GPU) | Works, slow, no 4-bit quantization |
| Quantize without adapters | Error message, not a crash |
| Evaluate | `python evaluate.py` prints BERTScore + ROUGE |
| Train with corrupted dataset | Checksum validation fails, aborts |
