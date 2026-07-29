"""
prepare_dataset.py — Build the instruction-tuning dataset for chatbot training.

Pipeline:
  1. Load custom Q&A pairs from data/custom_qa.jsonl (platform-specific knowledge)
  2. Optionally augment with Hugging Face finance-domain datasets
  3. Format every example into a consistent instruction→response template
  4. Split into train / eval sets
  5. Save as JSONL files ready for train.py

Usage:
  python prepare_dataset.py                     # custom data only
  python prepare_dataset.py --with-hf           # include HF finance datasets
  python prepare_dataset.py --output ./data     # custom output directory
"""

import argparse
import json
import os
import random

from datasets import load_dataset

random.seed(42)

CUSTOM_PATH = os.path.join(os.path.dirname(__file__), "data", "custom_qa.jsonl")
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "data")


def load_custom_qa(path: str) -> list[dict]:
    """Load the hand-written Q&A pairs from JSONL."""
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
    """
    Augment with Hugging Face finance-domain datasets.
    This demonstrates the ability to work with real-world HF data.
    """
    records = []

    # --- Financial PhraseBank (sentiment → instruction style) ---
    try:
        fp = load_dataset("financial_phrasebank", "sentences_allagree", split="train")
        for i, row in enumerate(fp):
            if i >= samples_per_dataset // 2:
                break
            records.append({
                "instruction": f"Categorize the sentiment of this financial statement: \"{row['sentence']}\"",
                "output": f"The sentiment of this financial statement is {row['label']}.",
            })
        print(f"[✓] Loaded {len(records) - len(records) + min(samples_per_dataset // 2, len(fp))} "
              f"samples from financial_phrasebank")
    except Exception as e:
        print(f"[!] Could not load financial_phrasebank: {e}")

    # --- Finance-Alpaca (instruction-following in finance domain) ---
    try:
        fa = load_dataset("AdaptLLM/finance-tasks", split="train")
        for i, row in enumerate(fa):
            if i >= samples_per_dataset // 2:
                break
            records.append({
                "instruction": row["instruction"],
                "output": row["output"],
            })
        print(f"[✓] Loaded {min(samples_per_dataset // 2, len(fa))} samples from finance-tasks")
    except Exception as e:
        print(f"[!] Could not load finance-tasks: {e}")

    return records


def format_chat(
    instruction: str,
    output: str,
    system_prompt: str = "You are a helpful assistant specialized in cash-flow underwriting and the Ledger platform. Answer concisely and accurately."
) -> dict:
    """
    Format into the chat-template structure expected by train.py.
    Uses the standard format: system + user + assistant.
    """
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": output},
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare chatbot training dataset")
    parser.add_argument("--with-hf", action="store_true", help="Include Hugging Face finance datasets")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Output directory for train/eval JSONL")
    parser.add_argument("--eval-split", type=float, default=0.1, help="Fraction of data for evaluation")
    args = parser.parse_args()

    records = load_custom_qa(CUSTOM_PATH)

    if args.with_hf:
        hf_records = load_hf_finance()
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

    print(f"\n{'='*50}")
    print(f"Dataset summary:")
    print(f"  Total examples : {len(records)}")
    print(f"  Train split    : {len(train_raw)} ({train_path})")
    print(f"  Eval split     : {len(eval_raw)} ({eval_path})")
    if args.with_hf:
        print(f"  (includes {len(records) - len(load_custom_qa(CUSTOM_PATH))} HF-augmented samples)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
