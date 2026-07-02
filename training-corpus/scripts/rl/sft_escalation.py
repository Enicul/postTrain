#!/usr/bin/env python3
"""Plan A2: LoRA SFT a small model on oracle escalation labels.

Pull-and-run on an A100. Trains a tiny adapter (Qwen2.5-0.5B/1.5B default) to
imitate the analytic oracle policy. This is the "does supervision suffice?"
baseline that GRPO must beat. Saves the adapter + metrics only (no base
weights) to stay git-light.

Usage:
  python build_sft_labels.py --env-dir <ENV> --split train --lambda 0.3 \
      --out sft_train.jsonl
  python sft_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct \
      --train sft_train.jsonl --out-dir runs/sft_escalation_qwen05b

Then evaluate with eval_escalation_policy.py against the frozen eval-256.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--train", type=Path, required=True, help="JSONL from build_sft_labels.py")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--max-seq-len", type=int, default=1024)
    ap.add_argument("--lora-r", type=int, default=16)
    args = ap.parse_args()

    # heavy imports inside main so --help works without a GPU stack
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    ds = load_dataset("json", data_files=str(args.train), split="train")

    def to_text(ex):
        return {"text": tok.apply_chat_template(ex["messages"], tokenize=False,
                                                add_generation_prompt=False)}

    ds = ds.map(to_text, remove_columns=[c for c in ds.column_names if c != "messages"])

    peft_cfg = LoraConfig(
        r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM",
    )
    cfg = SFTConfig(
        output_dir=str(args.out_dir), num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size, learning_rate=args.lr,
        max_seq_length=args.max_seq_len, logging_steps=10, save_strategy="epoch",
        bf16=True, report_to=[],
    )
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds,
                         peft_config=peft_cfg, processing_class=tok)
    result = trainer.train()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.out_dir / "adapter"))
    (args.out_dir / "metrics.json").write_text(json.dumps({
        "model": args.model, "train_file": str(args.train),
        "train_rows": len(ds), "epochs": args.epochs, "lr": args.lr,
        "final_loss": result.training_loss,
    }, indent=1))
    print(json.dumps({"status": "sft_done", "adapter": str(args.out_dir / "adapter"),
                      "final_loss": result.training_loss}, indent=1))


if __name__ == "__main__":
    main()
