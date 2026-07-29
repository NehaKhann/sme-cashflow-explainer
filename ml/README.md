# ML Pipeline — Ledger Chatbot

Fine-tune a small language model on cash-flow underwriting knowledge using **QLoRA**, quantize it to **GGUF**, and serve it locally via **Ollama**.

## Pipeline Overview

```
training_config.json ──────┐
                          ▼
custom_qa.jsonl ─┐        │
                 ├─▶ prepare_dataset.py ──▶ train.py ──▶ quantize.py ──▶ Ollama
HF datasets ─────┘     (build dataset)      (QLoRA)      (GGUF)
                          │                    │
                          ▼                    ▼
                   data_checksum.json    active_config.json
                          │              (run output)
                          ▼
                     validated at
                     train start
```

## Quick Start (full pipeline)

```bash
cd ml
pip install -r requirements.txt

# 1. Prepare dataset (custom Q&A + optional HF finance data)
python prepare_dataset.py --with-hf

# 2. Fine-tune with QLoRA (auto-detects GPU)
python train.py                                    # uses default config
python train.py --config my_config.json            # custom config
python train.py --lr 1e-4 --epochs 3               # CLI overrides config

# 3. Merge adapters + quantize to GGUF for Ollama
python quantize.py --adapters ./output/ledger-chatbot-<timestamp>

# 4. Serve with Ollama
ollama create ledger-chatbot -f ./output/ledger-chatbot-<timestamp>/Modelfile
ollama run ledger-chatbot
```

### GPU / CPU Setup

The script auto-detects your hardware. Install the appropriate PyTorch build:

**NVIDIA GPU (CUDA) — recommended:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```
Trainer prints GPU name and VRAM on launch. Requires ≥8 GB VRAM for Llama 3.2 3B.

**Apple Silicon (MPS):**
```bash
pip install torch torchvision torchaudio
```
Automatically uses the Metal Performance Shaders backend.

**CPU only (not recommended for training):**
```bash
pip install torch torchvision torchaudio
```
Training will be very slow (hours). Inference via Ollama GGUF works fine on CPU.

**Ollama GPU acceleration:**
Ollama automatically uses your GPU for inference. Verify with:
- Windows: Task Manager → Performance → GPU
- Linux: `nvidia-smi` or `ollama ps`
- macOS: Activity Monitor → GPU History

## Dataset

| Source | Description | Examples |
|---|---|---|
| `data/custom_qa.jsonl` | Hand-written Q&A about Ledger and underwriting | 50 |
| Hugging Face (optional) | [`financial_phrasebank`](https://huggingface.co/datasets/financial_phrasebank), [`AdaptLLM/finance-tasks`](https://huggingface.co/datasets/AdaptLLM/finance-tasks) | ~600 |

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

## Configuration

All four scripts share a single `training_config.json` in the `ml/` root. CLI arguments take precedence over the config file, which takes precedence over built-in defaults.

```bash
# Priority: CLI arg > config file > built-in default
python train.py                                    # built-in defaults
python train.py --config my_config.json            # file overrides
python train.py --config my_config.json --lr 1e-4  # CLI wins
```

Parameters in `training_config.json`:

```json
{
    "model": "unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
    "epochs": 2,
    "lr": 0.0002,
    "rank": 16,
    "alpha": 32,
    "batch_size": 4,
    "grad_accum": 2,
    "max_seq_len": 1024,
    "seed": 42,
    "eval_split": 0.1,
    "samples_per_dataset": 300,
    "quant": "q4_k_m"
}
```

## Cross-Stage Data Integrity

Every script validates that training data hasn't been modified since `prepare_dataset.py` was last run:

1. `prepare_dataset.py` writes `data/data_checksum.json` (SHA-256 hashes of `train.jsonl` and `eval.jsonl`)
2. `train.py` reads this file at startup — if hashes don't match, training aborts with a clear message
3. The active config (merged from file + CLI) is saved to `output/<run>/active_config.json` for traceability

This prevents silent training on stale or corrupted data.

## Training: QLoRA

**QLoRA** (Quantized Low-Rank Adaptation) combines:

1. **4-bit NormalFloat quantization** — compresses the base model 4× using `bitsandbytes`
2. **Low-Rank Adapters (LoRA)** — trains small rank-decomposition matrices instead of full weights
3. **Double quantization** — quantizes the quantization constants for additional memory savings

### Hyperparameters

| Parameter | Config Key | Default | Description |
|---|---|---|---|
| Base model | `model` | `unsloth/Llama-3.2-3B-Instruct-bnb-4bit` | Pre-quantized 3B model |
| LoRA rank | `rank` | 16 | Low-rank matrix dimension |
| LoRA alpha | `alpha` | 32 | Scaling factor (2× rank) |
| Target modules | — | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` | All linear layers in attention + FFN |
| Learning rate | `lr` | 2×10⁻⁴ | Cosine schedule with 5% warmup |
| Batch size | `batch_size` | 4 | Per-device (adjust for your GPU) |
| Epochs | `epochs` | 2 | 1-3 sufficient for small dataset |
| Precision | — | bf16 | Brain float 16 for training stability |
| Gradient accum. | `grad_accum` | 2 | Steps before optimizer update |
| Max seq. length | `max_seq_len` | 1024 | Truncation length |
| Seed | `seed` | 42 | Reproducibility (torch + numpy + python) |
| Eval split | `eval_split` | 0.1 | Fraction held out for evaluation |
| HF samples | `samples_per_dataset` | 300 | Per-dataset HF augmentation cap |
| Quantization | `quant` | `q4_k_m` | Default GGUF quant level |

### Memory requirements

| Model | QLoRA VRAM | Full FT VRAM | GGUF Inference RAM |
|---|---|---|---|
| Llama 3.2 3B | ~6-8 GB | ~24 GB | ~2-4 GB (CPU) |
| Mistral 7B | ~10-12 GB | ~56 GB | ~4-8 GB (CPU) |

Training with QLoRA on a 3B model runs on any NVIDIA GPU with ≥8GB VRAM (RTX 3060+, GTX 1080 Ti). For inference, the quantized GGUF model runs efficiently on CPU via Ollama with minimal RAM overhead.

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
|---|---|---|
| `training_config.json` | Shared hyperparameter defaults for all scripts |
| `ml_utils.py` | Shared helpers: config loading, checksum validation, formatting func |
| `data/custom_qa.jsonl` | Hand-written instruction→response pairs |
| `data/data_checksum.json` | SHA-256 hashes for cross-stage integrity (auto-generated) |
| `prepare_dataset.py` | Assembles and formats the training dataset |
| `train.py` | QLoRA fine-tuning with SFTTrainer |
| `quantize.py` | Merge adapters + GGUF conversion + quantization |
| `evaluate.py` | Perplexity and qualitative evaluation |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Excludes large binaries (`.gguf`, `.safetensors`, `output/`) |
| `output/<run>/` | Trained adapters, merged model, GGUF files, Modelfile, active_config.json |

## Notes

- The base model is already 4-bit quantized (`bnb-4bit`) before LoRA is applied, which is the "Q" in QLoRA.
- The fine-tuned adapter weights are small (~20 MB) and can be committed to git. The full merged model and GGUF files are large and should be ignored.
- For production deployment, serve the GGUF model via Ollama's API (http://localhost:11434).
