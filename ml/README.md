# ML Pipeline — Ledger Chatbot

Fine-tune a small language model on cash-flow underwriting knowledge using **QLoRA**, quantize it to **GGUF**, and serve it locally via **Ollama**.

## Pipeline Overview

```
custom_qa.jsonl ─┐
                 ├─▶ prepare_dataset.py ──▶ train.py ──▶ quantize.py ──▶ Ollama
HF datasets ─────┘     (build dataset)      (QLoRA)      (GGUF)
```

## Quick Start (full pipeline)

```bash
cd ml
pip install -r requirements.txt

# 1. Prepare dataset (custom Q&A + optional HF finance data)
python prepare_dataset.py --with-hf

# 2. Fine-tune with QLoRA (requires GPU with ≥8GB VRAM)
python train.py

# 3. Merge adapters + quantize to GGUF for Ollama
python quantize.py --adapters ./output/ledger-chatbot-<timestamp>

# 4. Serve with Ollama
ollama create ledger-chatbot -f ./output/ledger-chatbot-<timestamp>/Modelfile
ollama run ledger-chatbot
```

## Dataset

| Source | Description | Examples |
|---|---|---|
| `data/custom_qa.jsonl` | Hand-written Q&A about Ledger and underwriting | 50 |
| Hugging Face (optional) | `financial_phrasebank`, `AdaptLLM/finance-tasks` | ~600 |

Every example is formatted as a chat template:
```
{"messages": [
  {"role": "system", "content": "..."},
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]}
```

### What the model learns

- Platform features (upload, analyze, compare, export)
- Financial metrics (volatility, concentration, seasonality, DSCR)
- Risk scoring methodology
- CSV format requirements
- Architecture and deployment

## Training: QLoRA

**QLoRA** (Quantized Low-Rank Adaptation) combines:

1. **4-bit NormalFloat quantization** — compresses the base model 4× using `bitsandbytes`
2. **Low-Rank Adapters (LoRA)** — trains small rank-decomposition matrices instead of full weights
3. **Double quantization** — quantizes the quantization constants for additional memory savings

### Hyperparameters

| Parameter | Default | Description |
|---|---|---|
| Base model | `unsloth/Llama-3.2-3B-Instruct-bnb-4bit` | Pre-quantized 3B model |
| LoRA rank | 16 | Low-rank matrix dimension |
| LoRA alpha | 32 | Scaling factor (2× rank) |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` | All linear layers in attention + FFN |
| Learning rate | 2×10⁻⁴ | Cosine schedule with 5% warmup |
| Batch size | 4 | Per-device (adjust for your GPU) |
| Epochs | 2 | 1-3 sufficient for small dataset |
| Precision | bf16 | Brain float 16 for training stability |

### Memory requirements

| Model | QLoRA VRAM | Full FT VRAM |
|---|---|---|
| Llama 3.2 3B | ~6-8 GB | ~24 GB |
| Mistral 7B | ~10-12 GB | ~56 GB |

Training with QLoRA on a 3B model runs on any NVIDIA GPU with ≥8GB VRAM (RTX 3060+).

## Quantization: GGUF

After merging LoRA adapters, the model is converted to **GGUF** format and quantized:

| Type | Size (3B) | Quality |
|---|---|---|
| `q4_k_m` | ~2.0 GB | Good (default) |
| `q5_k_m` | ~2.5 GB | Higher |
| `q8_0` | ~3.5 GB | Best |

The GGUF format allows running inference on CPU with `llama.cpp` or `Ollama`.

### Ollama integration

```bash
ollama create ledger-chatbot -f ./output/<run>/Modelfile
ollama run ledger-chatbot
```

The Modelfile sets:
- System prompt (underwriting expert persona)
- Chat template
- Temperature (0.7), top_p (0.9), max_tokens (512)

## Evaluation

```bash
python evaluate.py --model ./output/<run>/merged
```

| Metric | Description |
|---|---|
| Perplexity | Lower is better; measures prediction quality on held-out data |
| Sample responses | Qualitative review of answers to common questions |
| Consistency | Same question → similar answer across multiple runs |

## File Reference

| File | Purpose |
|---|---|
| `data/custom_qa.jsonl` | Hand-written instruction→response pairs |
| `prepare_dataset.py` | Assembles and formats the training dataset |
| `train.py` | QLoRA fine-tuning with SFTTrainer |
| `quantize.py` | Merge adapters + GGUF conversion + quantization |
| `evaluate.py` | Perplexity and qualitative evaluation |
| `requirements.txt` | Python dependencies |
| `output/<run>/` | Trained adapters, merged model, GGUF files, Modelfile |

## Notes

- The base model is already 4-bit quantized (`bnb-4bit`) before LoRA is applied, which is the "Q" in QLoRA.
- The fine-tuned adapter weights are small (~20 MB) and can be committed to git. The full merged model and GGUF files are large and should be ignored.
- For production deployment, serve the GGUF model via Ollama's API (http://localhost:11434).
