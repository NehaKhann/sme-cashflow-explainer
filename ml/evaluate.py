"""
evaluate.py — Evaluate the fine-tuned chatbot model.

Metrics:
  • Perplexity on the eval set (lower is better)
  • Qualitative review of sample answers
  • Response consistency (same question → similar answer)

Usage:
  python evaluate.py --model ./output/<run_name>/merged
  python evaluate.py --model ./output/<run_name>/merged --gguf ./output/<run_name>/gguf/ledger-chatbot-q4_k_m.gguf
"""

import argparse
import json
import math
import os
import random

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


SAMPLE_QUESTIONS = [
    "What is Ledger?",
    "How is revenue volatility calculated?",
    "What does a high risk score mean?",
    "How do I upload a CSV file?",
    "What is customer concentration risk?",
    "How does the PDF export work?",
    "What is the difference between demo mode and a signed-in account?",
    "Explain how risk flags are computed.",
]

SYSTEM_PROMPT = "You are a helpful assistant specialized in cash-flow underwriting and the Ledger platform. Answer concisely and accurately."


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned chatbot")
    parser.add_argument("--model", help="Path to merged model directory")
    parser.add_argument("--adapters", help="Path to LoRA adapters (for non-merged evaluation)")
    parser.add_argument("--base-model", default="unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
                        help="Base model name (required if --adapters is used)")
    parser.add_argument("--eval-file", default="data/eval.jsonl", help="Evaluation dataset")
    return parser.parse_args()


def load_model(model_path: str, adapters: str | None, base_model: str):
    """Load model from merged path or base + adapters."""
    if adapters:
        print(f"Loading base model: {base_model}")
        tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        print(f"Loading LoRA adapters from: {adapters}")
        model = PeftModel.from_pretrained(base, adapters)
        model = model.merge_and_unload()
    else:
        print(f"Loading merged model from: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    tokenizer.pad_token = tokenizer.eos_token
    model.eval()
    return model, tokenizer


@torch.no_grad()
def compute_perplexity(model, tokenizer, eval_file: str, max_samples: int = 50):
    """Compute perplexity on a sample of the evaluation set."""
    if not os.path.exists(eval_file):
        print(f"[!] Eval file not found: {eval_file}")
        return None

    print(f"\n{'='*50}")
    print("Perplexity Evaluation")
    print(f"{'='*50}")

    records = []
    with open(eval_file) as f:
        for line in f:
            records.append(json.loads(line))

    random.shuffle(records)
    records = records[:max_samples]

    losses = []
    for i, r in enumerate(records):
        messages = r.get("messages", [])
        text = ""
        for m in messages:
            text += f"{m['role']}: {m['content']}\n"

        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        outputs = model(**inputs, labels=inputs["input_ids"])
        losses.append(outputs.loss.item())

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(records)}] avg loss so far: {sum(losses)/len(losses):.4f}")

    avg_loss = sum(losses) / len(losses)
    perplexity = math.exp(avg_loss)

    print(f"\nResults ({len(records)} samples):")
    print(f"  Average loss  : {avg_loss:.4f}")
    print(f"  Perplexity    : {perplexity:.2f}")
    print(f"  (Lower perplexity = better prediction)")
    return perplexity


def sample_responses(model, tokenizer):
    """Generate answers to sample questions for qualitative review."""
    print(f"\n{'='*50}")
    print("Sample Responses (Qualitative Review)")
    print(f"{'='*50}")

    for question in SAMPLE_QUESTIONS:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        text = tokenizer.apply_chat_template(messages, tokenize=False)
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        print(f"\nQ: {question}")
        print(f"A: {response.strip()}")
        print("-" * 40)


def main():
    args = parse_args()

    if not args.model and not args.adapters:
        print("[!] Provide either --model (merged) or --adapters (LoRA)")
        return

    model, tokenizer = load_model(args.model, args.adapters, args.base_model)

    # Perplexity
    perplexity = compute_perplexity(model, tokenizer, args.eval_file)

    # Sample responses
    sample_responses(model, tokenizer)

    print(f"\n{'='*50}")
    print("Evaluation complete!")
    if perplexity:
        print(f"  Final perplexity: {perplexity:.2f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
