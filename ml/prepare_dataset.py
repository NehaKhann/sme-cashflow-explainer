"""
prepare_dataset.py — Build the instruction-tuning dataset for chatbot training.

Pipeline:
  1. Load custom Q&A pairs from data/custom_qa.jsonl (platform-specific knowledge)
  2. Optionally augment with Hugging Face finance-domain datasets
  3. Format every example into a consistent instruction->response template
  4. Split into train / eval sets
  5. Save as JSONL files ready for train.py

Usage:
  python prepare_dataset.py                     # custom data only
  python prepare_dataset.py --with-hf           # include HF finance datasets
  python prepare_dataset.py --config path.json  # custom config
"""

import argparse
import json
import os
import random
import sys

import numpy as np
from datasets import load_dataset

from ml_utils import BASE_DIR, load_config, merge_config_cli, write_data_checksum

CUSTOM_PATH = os.path.join(BASE_DIR, "data", "custom_qa.jsonl")
DEFAULT_OUT = os.path.join(BASE_DIR, "data")

SENTIMENT_LABELS = {0: "negative", 1: "neutral", 2: "positive"}


def load_custom_qa(path: str) -> list[dict]:
    """Load the hand-written Q&A pairs from JSONL."""
    if not os.path.exists(path):
        print(f"[!] Custom Q&A file not found: {path}")
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            records.append({
                "instruction": obj["instruction"],
                "output": obj["output"],
            })
    print(f"[✓] Loaded {len(records)} custom Q&A pairs from {path}")
    return records


def load_hf_finance(samples_per_dataset: int = 300) -> list[dict]:
    records = []

    try:
        fp = load_dataset("financial_phrasebank", "sentences_allagree", split="train")
        count = 0
        for i, row in enumerate(fp):
            if i >= samples_per_dataset // 2:
                break
            label_text = SENTIMENT_LABELS.get(row["label"], str(row["label"]))
            records.append({
                "instruction": f"Categorize the sentiment of this financial statement: \"{row['sentence']}\"",
                "output": f"The sentiment of this financial statement is {label_text}.",
            })
            count += 1
        print(f"[✓] Loaded {count} samples from financial_phrasebank")
    except Exception as e:
        print(f"[!] Could not load financial_phrasebank: {e}")

    try:
        fa = load_dataset("AdaptLLM/finance-tasks", split="train")
        count = 0
        for i, row in enumerate(fa):
            if i >= samples_per_dataset // 2:
                break
            records.append({
                "instruction": row["instruction"],
                "output": row["output"],
            })
            count += 1
        print(f"[✓] Loaded {count} samples from finance-tasks")
    except Exception as e:
        print(f"[!] Could not load finance-tasks: {e}")

    return records


def format_chat(
    instruction: str,
    output: str,
    system_prompt: str = "You are a helpful assistant specialized in cash-flow underwriting and the Ledger platform. Answer concisely and accurately."
) -> dict:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": output},
        ],
    }


def parse_args():
    builtin = {
        "seed": 42, "eval_split": 0.1, "samples_per_dataset": 300,
        "with_hf": False, "output": DEFAULT_OUT, "config": None,
    }
    parser = argparse.ArgumentParser(description="Prepare chatbot training dataset")
    parser.add_argument("--with-hf", action="store_true", help="Include Hugging Face finance datasets")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Output directory for train/eval JSONL")
    parser.add_argument("--eval-split", type=float, default=0.1, help="Fraction of data for evaluation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling")
    parser.add_argument("--config", default=None, help="Path to training_config.json")
    parser.add_argument("--samples-per-dataset", type=int, default=300, help="Samples per HF dataset")
    args = parser.parse_args()
    config = load_config(args.config)
    args = merge_config_cli(config, args, builtin)
    return args


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    records = load_custom_qa(CUSTOM_PATH)
    custom_count = len(records)

    if args.with_hf:
        hf_records = load_hf_finance(args.samples_per_dataset)
        records.extend(hf_records)

    random.shuffle(records)

    split_idx = int(len(records) * (1 - args.eval_split))
    train_raw = records[:split_idx]
    eval_raw = records[split_idx:]

    os.makedirs(args.output, exist_ok=True)

    train_path = os.path.join(args.output, "train.jsonl")
    eval_path = os.path.join(args.output, "eval.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_raw:
            f.write(json.dumps(format_chat(r["instruction"], r["output"])) + "\n")

    with open(eval_path, "w", encoding="utf-8") as f:
        for r in eval_raw:
            f.write(json.dumps(format_chat(r["instruction"], r["output"])) + "\n")

    # Write checksum for cross-stage validation
    write_data_checksum(args.output, train_path, eval_path)

    print(f"\n{'='*50}")
    print(f"Dataset summary:")
    print(f"  Total examples : {len(records)}")
    print(f"  Train split    : {len(train_raw)} ({train_path})")
    print(f"  Eval split     : {len(eval_raw)} ({eval_path})")
    if args.with_hf:
        print(f"  (includes {len(records) - custom_count} HF-augmented samples)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
