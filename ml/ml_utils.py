"""
ml_utils.py — Shared utilities for the ML pipeline.
  • Config loading (training_config.json + CLI override)
  • Dataset checksum validation (cross-stage integrity)
  • Formatting function for SFTTrainer
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Any


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "training_config.json")


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load JSON config; falls back to training_config.json in ml/ root."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        if config_path:
            print(f"[!] Config file not found: {path}")
            sys.exit(1)
        return {}
    with open(path) as f:
        return json.load(f)


def merge_config_cli(config: dict, args: argparse.Namespace, builtin_defaults: dict) -> argparse.Namespace:
    """
    Merge config file values into parsed CLI args.
    CLI-explicit values (those differing from builtin_defaults) take precedence.
    """
    ns = vars(args)
    for key, cli_val in ns.items():
        builtin = builtin_defaults.get(key)
        if key in config and cli_val == builtin:
            ns[key] = config[key]
    return args


def compute_file_hash(path: str) -> str:
    """SHA-256 hex digest of a file's content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_data_checksum(data_dir: str, train_file: str, eval_file: str):
    """Write a checksum file for cross-stage validation."""
    checksums = {}
    for name, path in [("train", train_file), ("eval", eval_file)]:
        if os.path.exists(path):
            checksums[name] = compute_file_hash(path)
    out_path = os.path.join(data_dir, "data_checksum.json")
    with open(out_path, "w") as f:
        json.dump(checksums, f, indent=2)
    print(f"[✓] Data checksum saved to {out_path}")
    return checksums


def validate_data_checksum(data_dir: str, train_file: str, eval_file: str):
    """Validate current data files against saved checksum. Warns on mismatch."""
    checksum_path = os.path.join(data_dir, "data_checksum.json")
    if not os.path.exists(checksum_path):
        print("[!] No data_checksum.json found — run prepare_dataset.py again")
        print("    Proceeding anyway (stale data may cause training issues)")
        return

    with open(checksum_path) as f:
        expected = json.load(f)

    mismatches = []
    for name, path in [("train", train_file), ("eval", eval_file)]:
        if name not in expected:
            continue
        if not os.path.exists(path):
            mismatches.append(f"{name}: file missing")
            continue
        actual = compute_file_hash(path)
        if actual != expected[name]:
            mismatches.append(f"{name}: hash mismatch (data changed since prepare_dataset.py)")

    if mismatches:
        print("[!] Data checksum validation failed:")
        for m in mismatches:
            print(f"      {m}")
        print("    Run 'python prepare_dataset.py' to regenerate the dataset.")
        sys.exit(1)
    else:
        print("[✓] Data checksum validated — dataset is up to date")


def formatting_func(example: dict, tokenizer) -> str:
    """
    Explicitly convert a "messages"-format example to text.
    TRL-version-independent because we handle the formatting ourselves.
    """
    messages = example.get("messages", [])
    return tokenizer.apply_chat_template(messages, tokenize=False)
