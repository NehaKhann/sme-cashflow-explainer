"""
augment_dataset.py — Generate synthetic Q&A pairs from seed examples using Groq.

Reads data/custom_qa.jsonl, sends each pair to Groq with instructions to
produce N variations, validates the output, and appends unique new pairs.

Usage:
  python augment_dataset.py                              # 5 variations per seed (default)
  python augment_dataset.py --variations 10              # 10 per seed
  python augment_dataset.py --variations 10 --dry-run    # print without saving
  python augment_dataset.py --model llama-3.3-70b-versatile
"""

import json
import os
import re
import argparse
import time

from groq import Groq

from ml_utils import BASE_DIR

CUSTOM_PATH = os.path.join(BASE_DIR, "data", "custom_qa.jsonl")
AUGMENTED_PATH = os.path.join(BASE_DIR, "data", "custom_qa_augmented.jsonl")

SYSTEM_PROMPT = """You are a data augmentation assistant for a financial underwriting chatbot. Your output must be ONLY a JSON array — nothing else, no explanations, no markdown, no code fences.

Given a question-answer pair, generate variations that:
- Re-phrase the question in different ways (e.g. shorter, more formal, as a keyword query)
- Keep the answer factually identical — do NOT change numbers, names, or technical details
- Cover different user personas (underwriter, business owner, IT admin, student)

Output format — a JSON array of objects, each with "instruction" and "output":

[
  {"instruction": "...", "output": "..."},
  {"instruction": "...", "output": "..."}
]"""


def load_seed_pairs(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            records.append(obj)
    print(f"[✓] Loaded {len(records)} seed pairs from {path}")
    return records


def load_existing_augmented(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    existing = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            existing.add(obj["instruction"].strip().lower())
    print(f"[✓] Loaded {len(existing)} existing augmented pairs (will skip duplicates)")
    return existing


def parse_jsonl_from_response(text: str) -> list[dict]:
    """Extract valid JSON objects from the response, tolerating wrapping."""
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    # Try 1: parse whole response as JSON array
    try:
        arr = json.loads(text)
        if isinstance(arr, list):
            return [obj for obj in arr if isinstance(obj, dict) and "instruction" in obj and "output" in obj]
    except json.JSONDecodeError:
        pass

    # Try 2: use raw_decode to find all JSON values scattered in text
    results = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        try:
            obj, end = decoder.raw_decode(text, idx)
            if isinstance(obj, list):
                results.extend(o for o in obj if isinstance(o, dict) and "instruction" in o and "output" in o)
            elif isinstance(obj, dict) and "instruction" in obj and "output" in obj:
                results.append(obj)
            idx = end
        except json.JSONDecodeError:
            idx += 1

    if results:
        return results

    # Try 3: line-by-line fallback
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if "instruction" in obj and "output" in obj:
                results.append(obj)
        except json.JSONDecodeError:
            pass

    return results


def build_user_prompt(seed: dict, n: int) -> str:
    return f"""Generate {n} unique variations of the following Q&A pair.
Vary the question wording, tone, and phrasing but keep the answer factually identical.

Original:
{json.dumps(seed, ensure_ascii=False)}

Output ONLY a JSON array (exactly {n} elements) — no markdown, no code fences, no extra text:"""


def augment_pairs(
    seed_pairs: list[dict],
    existing_set: set[str],
    client: Groq,
    model: str,
    variations_per_seed: int,
) -> list[dict]:
    new_pairs = []
    total = len(seed_pairs)

    for idx, seed in enumerate(seed_pairs, 1):
        print(f"[{idx}/{total}] Processing: {seed['instruction'][:60]}...")

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(seed, variations_per_seed)},
                    ],
                    temperature=0.8,
                    max_tokens=4096,
                )
                text = response.choices[0].message.content
                parsed = parse_jsonl_from_response(text)

                if not parsed:
                    print(f"    [!] No valid JSON found (attempt {attempt+1}) — raw response (first 300 chars):")
                    print(f"        {text[:300]}")
                    continue

                for pair in parsed:
                    key = pair["instruction"].strip().lower()
                    if key not in existing_set:
                        existing_set.add(key)
                        new_pairs.append(pair)

                print(f"    [+] Added {len([p for p in parsed if p['instruction'].strip().lower() not in existing_set])} new pairs")
                break
            except Exception as e:
                print(f"    [!] API error: {e} (attempt {attempt+1})")
                if attempt < 2:
                    time.sleep(3)

        time.sleep(0.5)

    return new_pairs


def main():
    parser = argparse.ArgumentParser(description="Augment Q&A dataset via Groq")
    parser.add_argument("--variations", type=int, default=5, help="Variations per seed pair")
    parser.add_argument("--model", default="llama-3.3-70b-versatile", help="Groq model")
    parser.add_argument("--dry-run", action="store_true", help="Print count without saving")
    parser.add_argument("--output", default=AUGMENTED_PATH, help="Output path")
    args = parser.parse_args()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[!] GROQ_API_KEY not set. Set it in your environment or .env file.")
        print("    Export it: $env:GROQ_API_KEY = 'your-key'")
        sys.exit(1)

    client = Groq(api_key=api_key)

    seed_pairs = load_seed_pairs(CUSTOM_PATH)
    existing_set = load_existing_augmented(args.output)

    print(f"\nGenerating up to {args.variations} variations each for {len(seed_pairs)} seeds...\n")

    new_pairs = augment_pairs(seed_pairs, existing_set, client, args.model, args.variations)

    print(f"\n{'='*50}")
    print(f"Summary:")
    print(f"  Seeds used       : {len(seed_pairs)}")
    print(f"  New pairs created: {len(new_pairs)}")
    print(f"  Total augmented  : {len(existing_set) + len(new_pairs)}")
    print(f"{'='*50}")

    if args.dry_run:
        print("\n[Dry run] No files written.")
        return

    if new_pairs:
        with open(args.output, "a", encoding="utf-8") as f:
            for pair in new_pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        print(f"\n[✓] Appended {len(new_pairs)} new pairs to {args.output}")


if __name__ == "__main__":
    import sys
    main()
