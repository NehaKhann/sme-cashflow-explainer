"""
quantize.py — Merge LoRA adapters and quantize to GGUF for Ollama.

Pipeline:
  1. Load the base model + trained LoRA adapters from train.py
  2. Merge adapters into the base model (produces a single weights file)
  3. Convert to Hugging Face safetensors format
  4. Convert to GGUF format using llama.cpp
  5. Apply multiple quantization levels for comparison
  6. Generate a Modelfile for Ollama

Prerequisites:
  • llama.cpp must be installed (pip install llama-cpp-python or build from source)
  • The trained LoRA adapter directory from train.py

Usage:
  python quantize.py --adapters ./output/ledger-chatbot-20250201_120000
  python quantize.py --adapters ./output/ledger-chatbot-20250201_120000 --quant q4_k_m
  python quantize.py --adapters ... --skip-llamacpp      # only merge, no GGUF

Output:
  ./output/<run_name>/gguf/ledger-chatbot-<quant>.gguf   # GGUF model file
  ./output/<run_name>/Modelfile                           # Ollama model definition
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from ml_utils import load_config, merge_config_cli

# ---------------------------------------------------------------------------
# Supported quantization levels (llama.cpp)
# ---------------------------------------------------------------------------
QUANT_TYPES = {
    "q4_k_m": "Q4_K_M — 4-bit, good balance of size vs quality (~2 GB for 3B)",
    "q5_k_m": "Q5_K_M — 5-bit, higher quality (~2.5 GB for 3B)",
    "q8_0":   "Q8_0   — 8-bit, best quality (~3.5 GB for 3B)",
}

DEFAULT_QUANT = "q4_k_m"


def parse_args():
    builtin = {"quant": DEFAULT_QUANT, "skip_llamacpp": False, "llama_cpp_repo": None, "config": None}
    parser = argparse.ArgumentParser(description="Merge LoRA adapters and quantize to GGUF")
    parser.add_argument("--config", default=None, help="Path to training_config.json")
    parser.add_argument("--adapters", required=True, help="Path to LoRA adapter directory from train.py")
    parser.add_argument("--quant", default=DEFAULT_QUANT, choices=list(QUANT_TYPES.keys()) + ["all"],
                        help="Quantization level(s). 'all' generates every level.")
    parser.add_argument("--skip-llamacpp", action="store_true",
                        help="Skip GGUF conversion (merge + save safetensors only)")
    parser.add_argument("--llama-cpp-repo", default=None,
                        help="Path to local llama.cpp repo (if convert.py not in PATH)")
    args = parser.parse_args()
    config = load_config(args.config)
    args = merge_config_cli(config, args, builtin)
    return args


def merge_and_save(adapter_path: str) -> str:
    """
    Load base model + LoRA adapters, merge, and save as safetensors.
    Returns the path to the merged model directory.
    """
    # Load training config to know the base model
    config_path = os.path.join(adapter_path, "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        base_model_name = config.get("model", "")
    else:
        base_model_name = ""

    if not base_model_name:
        print("[!] Could not determine base model from config.json.")
        print("    Please specify the base model manually or ensure config.json exists.")
        sys.exit(1)

    print(f"[1/4] Loading base model: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    print(f"[2/4] Loading LoRA adapters from {adapter_path}")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model = model.merge_and_unload()  # Merge adapters into base weights

    merged_dir = os.path.join(adapter_path, "merged")
    os.makedirs(merged_dir, exist_ok=True)

    print(f"[3/4] Saving merged model to {merged_dir}")
    model.save_pretrained(merged_dir, safe_serialization=True)
    tokenizer.save_pretrained(merged_dir)

    # Verify the files
    safetensors_files = [f for f in os.listdir(merged_dir) if f.endswith(".safetensors")]
    total_size = sum(os.path.getsize(os.path.join(merged_dir, f)) for f in safetensors_files)
    print(f"    Saved {len(safetensors_files)} safetensors files ({total_size / 1e9:.2f} GB)")

    return merged_dir


def convert_to_gguf(merged_dir: str, adapter_path: str, quant: str, llama_cpp_repo: str | None):
    """
    Convert merged safetensors to GGUF using llama.cpp's convert.py,
    then apply the requested quantization level.
    """
    gguf_dir = os.path.join(adapter_path, "gguf")
    os.makedirs(gguf_dir, exist_ok=True)

    # Step 1: Convert safetensors → FP16 GGUF
    fp16_path = os.path.join(gguf_dir, "ledger-chatbot-fp16.gguf")
    convert_script = "convert_hf_to_gguf.py"

    # Locate the conversion script
    if llama_cpp_repo:
        convert_script = os.path.join(llama_cpp_repo, convert_script)
    else:
        # Check if `llama.cpp` (C++ repo) cloned locally exposes it via PATH
        which = shutil.which(convert_script)
        if which:
            convert_script = which
        else:
            # Common install locations
            for candidate in (
                os.path.expanduser("~/llama.cpp/convert_hf_to_gguf.py"),
                os.path.expanduser("~/llama.cpp/convert/convert_hf_to_gguf.py"),
            ):
                if os.path.exists(candidate):
                    convert_script = candidate
                    break

    print(f"[GGUF] Converting {merged_dir} → {fp16_path}")
    print(f"       Using script: {convert_script}")

    if not os.path.exists(convert_script):
        print("[!] convert_hf_to_gguf.py not found. Install llama.cpp or provide --llama-cpp-repo")
        print("    Skipping GGUF conversion. Merged safetensors are available at:")
        print(f"    {merged_dir}")
        return None

    try:
        subprocess.run(
            [sys.executable, convert_script, merged_dir, "--outfile", fp16_path, "--outtype", "f16"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[!] GGUF conversion failed: {e}")
        return None

    # Step 2: Quantize the FP16 GGUF
    quants = [quant] if quant != "all" else list(QUANT_TYPES.keys())
    quant_paths = {}

    for q in quants:
        q_path = os.path.join(gguf_dir, f"ledger-chatbot-{q}.gguf")
        print(f"[GGUF] Quantizing to {q}: {fp16_path} → {q_path}")

        quantize_bin = shutil.which("llama-quantize")
        if not quantize_bin and llama_cpp_repo:
            candidate = os.path.join(llama_cpp_repo, "llama-quantize")
            if os.name == "nt":
                candidate += ".exe"
            if os.path.exists(candidate):
                quantize_bin = candidate

        if not quantize_bin:
            print("[!] llama-quantize not found in PATH or --llama-cpp-repo")
            print("    Skipping quantization. Install llama.cpp or use --skip-llamacpp")
            continue

        try:
            subprocess.run([quantize_bin, fp16_path, q_path, q.upper()], check=True)
            q_size = os.path.getsize(q_path)
            print(f"       Done. Size: {q_size / 1e9:.2f} GB")
            quant_paths[q] = q_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[!] Quantization for {q} failed: {e}")
            print("    Make sure llama-quantize is installed and in your PATH.")

    return quant_paths


def generate_modelfile(adapter_path: str, quant: str):
    """Generate a Modelfile for Ollama pointing to the GGUF file."""
    gguf_dir = os.path.join(adapter_path, "gguf")
    quant_name = quant if quant != "all" else DEFAULT_QUANT
    gguf_path = os.path.join(gguf_dir, f"ledger-chatbot-{quant_name}.gguf")

    modelfile_content = f"""# Modelfile for Ledger Chatbot
# Generated by quantize.py
# Quantization: {quant_name}

FROM {gguf_path}

# System prompt that sets the assistant persona
SYSTEM \"\"\"You are Ledger Assistant, an expert in cash-flow underwriting and financial analysis. You help users understand the Ledger platform, interpret financial metrics, and analyze cash-flow data. Answer concisely, accurately, and always ground your responses in the computed data.
\"\"\"

# Template for chat format
TEMPLATE \"\"\"{{ if .System }}<|system|>
{{ .System }}
{{ end }}<|user|>
{{ .Prompt }}
<|assistant|>
{{ .Response }}
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER max_tokens 512
"""
    modelfile_path = os.path.join(adapter_path, "Modelfile")
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    print(f"\n[✓] Modelfile generated: {modelfile_path}")
    print(f"    To use with Ollama:")
    print(f"      ollama create ledger-chatbot -f {modelfile_path}")
    print(f"      ollama run ledger-chatbot")

    return modelfile_path


def main():
    args = parse_args()

    if not os.path.isdir(args.adapters):
        print(f"[!] Adapter directory not found: {args.adapters}")
        sys.exit(1)

    # Step 1-3: Merge adapters and save safetensors
    merged_dir = merge_and_save(args.adapters)

    # Step 4: Convert to GGUF and quantize
    quant_paths = None
    if not args.skip_llamacpp:
        quant_paths = convert_to_gguf(merged_dir, args.adapters, args.quant, args.llama_cpp_repo)

    # Step 5: Generate Modelfile (only if GGUF was created)
    if not args.skip_llamacpp:
        generate_modelfile(args.adapters, args.quant)

    print(f"\n{'='*60}")
    print(f"Quantization complete!")
    print(f"  Merged model  : {merged_dir}")
    if quant_paths:
        for q, path in quant_paths.items():
            size = os.path.getsize(path) / 1e9
            print(f"  GGUF ({q})     : {path} ({size:.2f} GB)")
    print(f"  Modelfile     : {os.path.join(args.adapters, 'Modelfile')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
