# ML Pipeline — Ledger Chatbot

Fine-tune a small language model on cash-flow underwriting knowledge using **QLoRA**, convert it to **GGUF**, and serve it locally via **Ollama**.

## Pipeline Overview

```text
training_config.json ──────┐
                           ▼
custom_qa.jsonl ─┐        │
                 ├─▶ prepare_dataset.py ──▶ train.py ──▶ merge + convert ──▶ Ollama
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

# If you get huggingface-hub / datasets version conflicts:
#   pip install "datasets>=4,<6" "huggingface-hub>=1.0"
```

### 1. Prepare dataset

```bash
python prepare_dataset.py --with-hf
```

### 2. Fine-tune with QLoRA

```bash
# Recommended for 6 GB GPUs (RTX 4050 etc.)
python train.py --config training_config.json --disable-wandb --batch-size 2 --max-seq-len 512

# Other useful variants
python train.py --disable-wandb
python train.py --config training_config.json --disable-wandb --lr 1e-4
```

At the end of training a folder is created, e.g. `output/ledger-chatbot-YYYYMMDD_HHMM/`.

### 3. Merge LoRA adapters (on CPU)

Because 6 GB GPUs often run out of memory during merging:

```powershell
# Automatically use the latest training folder
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

### 4. Convert to GGUF

Use the official converter included in the project (`llama.cpp-temp`):

```powershell
# Create gguf folder
New-Item -ItemType Directory -Path "$($latest.FullName)\gguf" -Force | Out-Null

# Convert
python llama.cpp-temp\convert_hf_to_gguf.py `
  "$($latest.FullName)\merged" `
  --outfile "$($latest.FullName)\gguf\ledger-chatbot-fp16.gguf" `
  --outtype f16
```

### 5. Create a correct Modelfile

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

### 6. Register & run with Ollama

```powershell
ollama create ledger-chatbot -f "$($latest.FullName)\Modelfile"
ollama run ledger-chatbot
```

### 7. Start Ollama server (for the backend)

```bash
ollama serve
```

## Troubleshooting

### HuggingFace / datasets errors

```bash
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\datasets--AdaptLLM--finance-tasks" -ErrorAction Ignore
pip install "datasets>=4,<6" "huggingface-hub>=1.0"
```

### GGUF conversion fails with `No module named 'conversion'`

Do not use the small `convert_hf_to_gguf.py` in the `ml/` root.

Always use the official one inside `llama.cpp-temp/`.

### Ollama error: `unknown parameter 'max_tokens'`

Ollama does not support `max_tokens`. Use `num_predict` instead (already fixed in the Modelfile above).

### Modelfile points to non-existent `.gguf`

Make sure the `FROM` line points to the real file you just created (`ledger-chatbot-fp16.gguf`).

## GPU / CPU Setup

| Mode | Setup | Training Speed |
|------|-------|----------------|
| GPU (CUDA) | NVIDIA + `pip install torch ... --index-url https://download.pytorch.org/whl/cu124` | ~15–40 min |
| GPU (Metal) | Apple Silicon | ~30–60 min |
| CPU | No GPU | Several hours |

Ollama automatically uses the GPU for inference when available.

## Dataset

| Source | Description | Examples |
|--------|-------------|----------|
| `data/custom_qa.jsonl` | Hand-written Q&A about Ledger and underwriting | 37 |
| Hugging Face (optional) | `AdaptLLM/finance-tasks` | ~300 |

Every example is formatted as a chat template with system / user / assistant roles.

## Configuration

All scripts share `training_config.json`. CLI arguments override the config file.

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

- `prepare_dataset.py` writes `data/data_checksum.json`
- `train.py` validates the checksums before starting
- The active config is saved to `output/<run>/active_config.json`

## Training: QLoRA

QLoRA = 4-bit quantization + Low-Rank Adapters.

| Parameter | Default | Notes |
|-----------|---------|-------|
| Base model | `Llama-3.2-3B-Instruct-bnb-4bit` | Already 4-bit quantized |
| LoRA rank | 16 | |
| LoRA alpha | 32 | |
| Learning rate | 2e-4 | |
| Batch size | 2–4 | Use 2 for 6 GB GPUs |
| Max seq length | 512–1024 | Use 512 for 6 GB GPUs |

## File Reference

| File / Folder | Purpose |
|---------------|---------|
| `training_config.json` | Shared hyperparameters |
| `prepare_dataset.py` | Builds the training dataset |
| `train.py` | QLoRA fine-tuning |
| `quantize.py` | (Legacy) Merge + quantize |
| `llama.cpp-temp/` | Official GGUF converter (use this) |
| `evaluate.py` | Evaluation script |
| `output/<run>/` | Adapters, merged model, GGUF, Modelfile |
| `output/<run>/merged/` | Full merged model |
| `output/<run>/gguf/` | Final GGUF file for Ollama |

## Notes

- The adapter weights are small (~20 MB) and can be committed to git.
- The full merged model and GGUF files are large — keep them in `.gitignore`.
- For production, serve the model via Ollama’s API (`http://localhost:11434`).
- On servers without a GPU (e.g. Render), set `CHAT_PROVIDER=groq` in the backend to use the Groq API instead.