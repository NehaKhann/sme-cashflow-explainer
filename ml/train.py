"""
train.py — QLoRA fine-tuning of a small LLM for the Ledger chatbot.

Usage:
  python train.py                                       # default config
  python train.py --config path.json                    # custom config
  python train.py --model unsloud/... --epochs 3        # CLI overrides config
  python train.py --device cpu                          # force CPU
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

import numpy as np
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

from ml_utils import (
    BASE_DIR, load_config, merge_config_cli,
    validate_data_checksum, formatting_func,
)

DEFAULT_MODEL = "unsloth/Llama-3.2-3B-Instruct-bnb-4bit"
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_BASE = os.path.join(BASE_DIR, "output")


def detect_device():
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9
        print(f"[GPU] {gpu_name} ({gpu_mem:.1f} GB VRAM)")
        print(f"[GPU] CUDA version: {torch.version.cuda}")
        return "cuda"
    elif torch.backends.mps.is_available():
        print("[GPU] Apple Metal (MPS) detected")
        return "mps"
    else:
        print("[CPU] No GPU detected")
        return "cpu"


def parse_args():
    builtin = {
        "model": DEFAULT_MODEL,
        "train_file": os.path.join(DATA_DIR, "train.jsonl"),
        "eval_file": os.path.join(DATA_DIR, "eval.jsonl"),
        "epochs": 2, "lr": 2e-4, "rank": 16, "alpha": 32,
        "batch_size": 4, "grad_accum": 2, "max_seq_len": 1024,
        "device": None, "seed": 42,
        "disable_wandb": False, "run_name": None, "config": None,
    }
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning")
    parser.add_argument("--config", default=None, help="Path to training_config.json")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Base model HF ID")
    parser.add_argument("--train-file", default=os.path.join(DATA_DIR, "train.jsonl"))
    parser.add_argument("--eval-file", default=os.path.join(DATA_DIR, "eval.jsonl"))
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--alpha", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=2)
    parser.add_argument("--max-seq-len", type=int, default=1024)
    parser.add_argument("--device", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--disable-wandb", action="store_true")
    parser.add_argument("--run-name", default=None)
    args = parser.parse_args()
    config = load_config(args.config)
    args = merge_config_cli(config, args, builtin)
    return args


def create_quantization_config():
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )


def create_lora_config(rank: int, alpha: int):
    return LoraConfig(
        r=rank, lora_alpha=alpha,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none", lora_dropout=0.05, task_type="CAUSAL_LM",
    )


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main():
    args = parse_args()
    set_seed(args.seed)

    run_name = args.run_name or f"ledger-chatbot-{datetime.now().strftime('%Y%m%d_%H%M')}"
    output_dir = os.path.join(OUTPUT_BASE, run_name)
    os.makedirs(output_dir, exist_ok=True)

    # Save training config for reproducibility
    with open(os.path.join(output_dir, "config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    # -------------------------------------------------------------------
    # 0. Detect device
    # -------------------------------------------------------------------
    device = args.device or detect_device()
    is_gpu = device != "cpu"
    if not is_gpu:
        print("[WARNING] Training on CPU — extremely slow")
    else:
        print(f"[GPU] Training on {device.upper()}")

    torch_dtype = torch.bfloat16 if is_gpu else torch.float32

    # -------------------------------------------------------------------
    # 1. Load & validate dataset (cross-stage integrity)
    # -------------------------------------------------------------------
    print(f"[1/5] Loading dataset from {args.train_file} and {args.eval_file}")
    for f in (args.train_file, args.eval_file):
        if not os.path.exists(f):
            print(f"[!] File not found: {f}")
            print("    Run 'python prepare_dataset.py' first.")
            sys.exit(1)

    validate_data_checksum(DATA_DIR, args.train_file, args.eval_file)

    dataset = load_dataset("json", data_files={"train": args.train_file, "eval": args.eval_file})
    if len(dataset["train"]) == 0:
        print("[!] Training dataset is empty")
        sys.exit(1)

    # -------------------------------------------------------------------
    # 2. Load base model + tokenizer
    # -------------------------------------------------------------------
    print(f"[2/5] Loading base model: {args.model}")

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.chat_template = tokenizer.chat_template or (
        "{% for message in messages %}"
        "{% if message['role'] == 'system' %}{{ message['content'] }}\n\n{% endif %}"
        "{% if message['role'] == 'user' %}{{ message['content'] }}\n{% endif %}"
        "{% if message['role'] == 'assistant' %}{{ message['content'] }}\n{% endif %}"
        "{% endfor %}"
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=create_quantization_config() if is_gpu else None,
        device_map="auto" if is_gpu else None,
        trust_remote_code=True,
        torch_dtype=torch_dtype,
    )

    if is_gpu:
        model = prepare_model_for_kbit_training(model)
        model.gradient_checkpointing_enable()
    else:
        for param in model.parameters():
            param.requires_grad = False

    # -------------------------------------------------------------------
    # 3. Apply LoRA adapters
    # -------------------------------------------------------------------
    print(f"[3/5] Applying LoRA adapters (rank={args.rank}, alpha={args.alpha})")
    peft_config = create_lora_config(args.rank, args.alpha)
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # -------------------------------------------------------------------
    # 4. Configure training — use explicit formatting_func
    # -------------------------------------------------------------------
    print(f"[4/5] Setting up SFTTrainer ({args.epochs} epochs, lr={args.lr})")

    steps_per_epoch = max(1, len(dataset["train"]) // (args.batch_size * args.grad_accum))
    eval_every = max(1, steps_per_epoch // 5)
    save_every = eval_every * 2

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=is_gpu,
        learning_rate=args.lr,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        bf16=is_gpu,
        fp16=False,
        logging_steps=max(1, steps_per_epoch // 10),
        eval_strategy="steps",
        eval_steps=eval_every,
        save_strategy="steps",
        save_steps=save_every,
        save_total_limit=2,
        load_best_model_at_end=steps_per_epoch >= eval_every,
        metric_for_best_model="eval_loss",
        dataloader_num_workers=0 if os.name == "nt" else 2,
        dataloader_pin_memory=is_gpu,
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
        formatting_func=lambda ex: formatting_func(ex, tokenizer),
    )

    # -------------------------------------------------------------------
    # 5. Train and save
    # -------------------------------------------------------------------
    print(f"[5/5] Starting training")
    try:
        trainer.train()
    except Exception as e:
        print(f"[!] Training failed: {e}")
        sys.exit(1)

    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save the active config alongside the run
    with open(os.path.join(output_dir, "active_config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    print(f"\n{'='*60}")
    print(f"Training complete!")
    print(f"  Run name     : {run_name}")
    print(f"  LoRA weights : {output_dir}")
    print(f"  Config       : {output_dir}/active_config.json")
    print(f"  Next step    : python quantize.py --adapters {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
