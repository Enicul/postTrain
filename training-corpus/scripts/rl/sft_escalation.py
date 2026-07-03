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
import sys
from pathlib import Path

from run_logging import make_log_callback, new_run_dir, write_manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--train", type=Path, required=True, help="JSONL from build_sft_labels.py")
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="parent dir; each run writes into out-dir/<run_id>/")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=1, help="gradient_accumulation_steps")
    ap.add_argument("--max-seq-len", type=int, default=1024)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", default=None,
                    help="checkpoint path (or 'True') to resume_from_checkpoint")
    ap.add_argument("--parent-run", default=None,
                    help="run_id of a failed run this re-run fixes (R4 linkage)")
    args = ap.parse_args()

    # heavy imports inside main so --help works without a GPU stack
    import torch
    import transformers
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    transformers.set_seed(args.seed)

    # run provenance + never-overwrite: land in out_dir/<run_id>/ (G8,G7)
    run_dir, run_id = new_run_dir(args.out_dir)

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
        output_dir=str(run_dir), num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum, learning_rate=args.lr,
        max_seq_length=args.max_seq_len, logging_steps=10, save_strategy="epoch",
        save_total_limit=None, seed=args.seed, bf16=True, report_to=[],
    )
    write_manifest(run_dir, run_id, seed=args.seed, argv=sys.argv,
                   config=vars(cfg) if hasattr(cfg, "__dict__") else {},
                   env_seeds_version=None, base_model=args.model,
                   parent_run_id=args.parent_run)
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds,
                         peft_config=peft_cfg, processing_class=tok,
                         callbacks=[make_log_callback(run_dir)])
    result = trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(str(run_dir / "adapter"))
    (run_dir / "metrics.json").write_text(json.dumps({
        "run_id": run_id, "model": args.model, "train_file": str(args.train),
        "train_rows": len(ds), "epochs": args.epochs, "lr": args.lr,
        "final_loss": result.training_loss,
    }, indent=1))
    print(json.dumps({"status": "sft_done", "run_id": run_id,
                      "adapter": str(run_dir / "adapter"),
                      "final_loss": result.training_loss}, indent=1))


if __name__ == "__main__":
    main()
