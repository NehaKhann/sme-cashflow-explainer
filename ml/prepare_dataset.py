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
HF_CONFIGS = ["FPB", "ConvFinQA", "FiQA_SA", "Headline", "NER"]


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


def _make_qa_pair(instruction: str, output: str) -> dict:
    return {"instruction": instruction, "output": output}


# ── HF dataset adapters ──────────────────────────────────────────
# Each adapter converts a row from a finance-tasks config into an
# {"instruction": …, "output": …} pair.


def _adapt_fpb(row: dict) -> dict | None:
    """FPB: classify sentence sentiment (Negative / Neutral / Positive)."""
    opts = row["options"]
    gold = int(row["gold_index"])
    out = opts[gold] if isinstance(opts, list) else eval(opts)[gold]
    return _make_qa_pair(
        f"Classify the sentiment of this financial text: {row['input']}",
        out,
    )


def _adapt_fiqa_sa(row: dict) -> dict | None:
    """FiQA_SA: sentiment classification of a financial social-media post."""
    opts = row["options"]
    gold = int(row["gold_index"])
    out = opts[gold] if isinstance(opts, list) else eval(opts)[gold]
    return _make_qa_pair(
        f"Classify the sentiment of this financial social-media post:\n{row['input']}",
        out,
    )


def _adapt_convfinqa(row: dict) -> dict | None:
    """ConvFinQA: financial question answering (numeric answer)."""
    return _make_qa_pair(
        f"Answer this financial question:\n{row['input']}",
        str(row["label"]),
    )


def _adapt_headline(row: dict) -> dict | None:
    """Headline: does the headline match the financial topic? No / Yes."""
    opts = row["options"]
    gold = int(row["gold_index"])
    out = opts[gold] if isinstance(opts, list) else eval(opts)[gold]
    # input already contains the full question
    return _make_qa_pair(row["input"], out)


def _adapt_ner(row: dict) -> dict | None:
    """NER: extract named entities from a financial sentence."""
    return _make_qa_pair(
        f"Extract the named entities from this financial sentence:\n{row['input']}",
        str(row["label"]),
    )


HF_ADAPTERS = {
    "FPB": _adapt_fpb,
    "FiQA_SA": _adapt_fiqa_sa,
    "ConvFinQA": _adapt_convfinqa,
    "Headline": _adapt_headline,
    "NER": _adapt_ner,
}


def load_hf_finance(samples_per_dataset: int = 300) -> list[dict]:
    records = []
    per_config = samples_per_dataset // len(HF_ADAPTERS)

    for config_name, adapter in HF_ADAPTERS.items():
        loaded = False
        for split_name in ["test", "train"]:
            if loaded:
                break
            try:
                fa = load_dataset("AdaptLLM/finance-tasks", config_name, split=split_name)
                count = 0
                for row in fa:
                    if count >= per_config:
                        break
                    pair = adapter(row)
                    if pair is not None:
                        records.append(pair)
                        count += 1
                print(f"[✓] Loaded {count} samples from finance-tasks/{config_name} ({split_name})")
                loaded = True
            except Exception:
                continue

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
