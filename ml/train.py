"""
train.py — QLoRA fine-tuning of a small LLM for the Ledger chatbot.

This script demonstrates the full fine-tuning pipeline:
  • 4-bit NormalFloat quantization (bitsandbytes)
  • LoRA adapters via PEFT (rank=16, alpha=32)
  • SFTTrainer from TRL (supervised fine-tuning)
  • Gradient checkpointing for memory efficiency
  • WandB logging (optional)

Base model: Llama 3.2 3B Instruct (or Mistral 7B Instruct for more capacity).

Usage:
  python train.py                                       # default: Llama 3.2 3B
  python train.py --model mistralai/Mistral-7B-Instruct-v0.3
  python train.py --epochs 3 --lr 2e-4 --rank 32       # custom hyperparams
  python train.py --disable-wandb                       # no logging

Output:
  Saves LoRA adapter weights to ./output/<run_name>/   (a few MB)
  These adapters are merged and quantized by quantize.py
"""

import argparse
import json
import os
import sys
from datetime import datetime

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    HfArgumentParser,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "unsloth/Llama-3.2-3B-Instruct-bnb-4bit"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "output")


def parse_args():
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning for Ledger chatbot")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Base model HF ID or path")
    parser.add_argument("--train-file", default=os.path.join(DATA_DIR, "train.jsonl"), help="Training data (JSONL)")
    parser.add_argument("--eval-file", default=os.path.join(DATA_DIR, "eval.jsonl"), help="Evaluation data (JSONL)")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=2e-4, help="Peak learning rate")
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank (r)")
    parser.add_argument("--alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device train batch size")
    parser.add_argument("--grad-accum", type=int, default=2, help="Gradient accumulation steps")
    parser.add_argument("--max-seq-len", type=int, default=1024, help="Maximum sequence length")
    parser.add_argument("--disable-wandb", action="store_true", help="Disable Weights & Biases logging")
    parser.add_argument("--run-name", default=None, help="Experiment run name")
    return parser.parse_args()


def create_quantization_config():
    """4-bit NormalFloat quantization for QLoRA."""
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",                # NormalFloat 4-bit
        bnb_4bit_use_double_quant=True,            # Double quantization (saves ~0.5GB)
        bnb_4bit_compute_dtype=torch.bfloat16,     # Compute in bf16 for stability
    )


def create_lora_config(rank: int, alpha: int):
    """LoRA adapter configuration targeting attention projections."""
    return LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules=[                            # Standard modules for Llama/Mistral
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        lora_dropout=0.05,
        task_type="CAUSAL_LM",
    )


def main():
    args = parse_args()
    run_name = args.run_name or f"ledger-chatbot-{datetime.now().strftime('%Y%m%d_%H%M')}"
    output_dir = os.path.join(OUTPUT_BASE, run_name)
    os.makedirs(output_dir, exist_ok=True)

    # Save training config for reproducibility
    with open(os.path.join(output_dir, "config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    # -----------------------------------------------------------------------
    # 1. Load dataset
    # -----------------------------------------------------------------------
    print(f"[1/5] Loading dataset from {args.train_file} and {args.eval_file}")
    if not os.path.exists(args.train_file):
        print(f"[!] Training file not found: {args.train_file}")
        print("    Run 'python prepare_dataset.py' first.")
        sys.exit(1)

    dataset = load_dataset("json", data_files={"train": args.train_file, "eval": args.eval_file})

    # -----------------------------------------------------------------------
    # 2. Load quantized base model + tokenizer
    # -----------------------------------------------------------------------
    print(f"[2/5] Loading base model: {args.model}")
    print("     (4-bit NF4 quantization via bitsandbytes)")

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token          # Ensure pad token exists
    tokenizer.chat_template = tokenizer.chat_template or (
        "{% for message in messages %}"
        "{% if message['role'] == 'system' %}{{ message['content'] }}\n\n{% endif %}"
        "{% if message['role'] == 'user' %}{{ message['content'] }}\n{% endif %}"
        "{% if message['role'] == 'assistant' %}{{ message['content'] }}\n{% endif %}"
        "{% endfor %}"
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=create_quantization_config(),
        device_map="auto",                             # Distribute across available GPUs/CPU
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    # Prepare for k-bit training (gradient checkpointing, frozen base)
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()

    # -----------------------------------------------------------------------
    # 3. Apply LoRA adapters (PEFT)
    # -----------------------------------------------------------------------
    print(f"[3/5] Applying LoRA adapters (rank={args.rank}, alpha={args.alpha})")
    peft_config = create_lora_config(args.rank, args.alpha)
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()                 # Should show ~0.1% trainable

    # -----------------------------------------------------------------------
    # 4. Configure training (SFTTrainer)
    # -----------------------------------------------------------------------
    print(f"[4/5] Setting up SFTTrainer ({args.epochs} epochs, lr={args.lr})")

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        learning_rate=args.lr,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        bf16=True,                                     # bfloat16 for modern GPUs
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="wandb" if not args.disable_wandb else "none",
        run_name=run_name,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        tokenizer=tokenizer,
        max_seq_length=args.max_seq_len,
        dataset_text_field=None,                       # Using messages format
        dataset_kwargs={"skip_prepare_dataset": True}, # Already formatted
    )

    # -----------------------------------------------------------------------
    # 5. Train and save
    # -----------------------------------------------------------------------
    print(f"[5/5] Starting training — saving to {output_dir}")
    try:
        trainer.train()
    except Exception as e:
        print(f"[!] Training failed: {e}")
        print("    Check GPU memory (need ~8GB for 3B, ~12GB for 7B)")
        sys.exit(1)

    # Save the LoRA adapter weights (small: a few MB)
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"\n{'='*60}")
    print(f"Training complete!")
    print(f"  Run name     : {run_name}")
    print(f"  LoRA weights : {output_dir}")
    print(f"  Trainable    : ~0.1% of base parameters")
    print(f"  Next step    : python quantize.py --adapters {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
