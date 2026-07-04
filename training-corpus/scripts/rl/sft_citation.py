#!/usr/bin/env python3
"""Plan B: LoRA SFT baseline for the citation task in the LETTERS action space.

The decoupling probe (batch 4, pre-registered bar iii). GRPO's citation-component
reward moved cite_gold but NOT verdict_acc (EXP-2026-07-04-003). Does plain
SUPERVISED training on the gold (letter, verdict) move verdict_acc where the RL
citation objective did not? This is the SFT baseline that answers it.

Training rows come from CitationAgenticEnv split=="train" (62 claims), rendered
in the letters action space so the prompt is identical to the letters GRPO / eval
ruler:
  prompt     = env.render_prompt(claim_id)          # lettered candidate menu
  completion = {"cite": "<gold letter>", "verdict": "<gold label>"}   # one line

CRITICAL: the letter for the gold evidence depends on the candidate ORDERING, so
the gold letter is looked up through env.letter_map(claim_id) (the env's own
render==score mapping) and NEVER re-derived. --labels-only asserts every gold
letter maps back to the gold evidence_id (zero mismatches) before any training.

LoRA config mirrors sft_escalation.py; run_logging provenance; save_total_limit
None. Evaluate the adapter with:
  python grpo_citation.py --eval-only --action-space letters \
      --adapter runs/sft_citation15/<RUN_ID>/adapter --split test --out <...>.json

Usage:
  # CPU, no torch: label mix + gold-letter mapping check (asserts 0 mismatches)
  python sft_citation.py --eval-dir $CENV --labels-only
  # GPU train
  python sft_citation.py --model Qwen/Qwen2.5-1.5B-Instruct --eval-dir $CENV \
      --out-dir runs/sft_citation15 --seed 0
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from citation_agentic_env import CitationAgenticEnv
from run_logging import make_log_callback, new_run_dir, write_manifest

K_CANDIDATES = 6


def build_rows(env: CitationAgenticEnv, split: str) -> tuple[list[dict], list[dict]]:
    """Build SFT rows for the letters action space + a per-claim mapping audit.

    Returns (rows, audit). Each row carries chat-style `messages` (prompt user
    turn + gold-JSON assistant turn). audit rows record the gold evidence_id, the
    resolved gold letter, and whether letter_map maps that letter back to the gold
    id (the mismatch guard). The gold letter comes ONLY from env.letter_map;
    it is never re-derived from candidate order here.
    """
    rows, audit = [], []
    ids = [cid for cid, m in env.claims.items()
           if split == "all" or m["split"] == split]
    for cid in ids:
        c = env.claims[cid]
        gold_eid = c["gold_evidence_id"]
        gold_label = c["gold_label"]
        lmap = env.letter_map(cid, K_CANDIDATES)  # env's own render==score mapping
        # invert via the env's mapping only: find the letter whose id IS the gold id
        gold_letter = next((ltr for ltr, eid in lmap.items() if eid == gold_eid), None)
        # round-trip guard: the letter must map back to the gold evidence_id
        maps_back = gold_letter is not None and lmap.get(gold_letter) == gold_eid
        audit.append({"claim_id": cid, "gold_evidence_id": gold_eid,
                      "gold_letter": gold_letter, "gold_label": gold_label,
                      "maps_back": maps_back, "n_candidates": len(lmap)})
        if gold_letter is None:
            continue  # can't build a supervised target without a gold letter
        prompt = env.render_prompt(cid, K_CANDIDATES)
        completion = json.dumps({"cite": gold_letter, "verdict": gold_label},
                                ensure_ascii=False)
        rows.append({
            "claim_id": cid,
            "prompt": prompt,
            "completion": " " + completion,
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion},
            ],
            "gold_letter": gold_letter, "gold_label": gold_label,
        })
    return rows, audit


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--eval-dir", type=Path, required=True,
                    help="citation_real_eval_v1 dir (has rows/all.jsonl)")
    ap.add_argument("--split", default="train", choices=["train", "dev", "test", "all"])
    ap.add_argument("--out-dir", type=Path, default=None,
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
    ap.add_argument("--labels-only", action="store_true",
                    help="CPU, no torch: print n_rows + letter/label mix and the "
                         "gold-letter mapping audit (asserts 0 mismatches), then "
                         "exit. Verifies env.letter_map gold mapping before any "
                         "GPU run.")
    args = ap.parse_args()

    # letters action space so prompt == the letters GRPO / eval ruler
    env = CitationAgenticEnv(args.eval_dir, action_space="letters")
    rows, audit = build_rows(env, args.split)

    # ---- CPU labels-only mode: mapping audit + mix, no torch ------------------
    if args.labels_only:
        mismatches = [a for a in audit if not a["maps_back"]]
        letter_mix = Counter(r["gold_letter"] for r in rows)
        label_mix = Counter(r["gold_label"] for r in rows)
        for a in audit:
            print(json.dumps(a, ensure_ascii=False))
        summary = {"status": "labels_only", "split": args.split,
                   "n_claims": len(audit), "n_rows": len(rows),
                   "letter_mix": dict(sorted(letter_mix.items())),
                   "label_mix": dict(sorted(label_mix.items())),
                   "mapping_mismatches": len(mismatches)}
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        # CRITICAL: every gold letter must map back to the gold evidence_id
        assert not mismatches, f"gold-letter mapping mismatches: {mismatches}"
        return

    if args.out_dir is None:
        ap.error("--out-dir is required for training (omit --labels-only)")
    # hard guard before spending GPU time: the supervised targets must be sound
    mismatches = [a for a in audit if not a["maps_back"]]
    if mismatches:
        raise SystemExit(f"refusing to train: gold-letter mapping mismatches: {mismatches}")

    # heavy imports inside main so --help / --labels-only work without a GPU stack
    import torch
    import transformers
    from datasets import Dataset
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
    ds = Dataset.from_list([{"messages": r["messages"]} for r in rows])

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
    manifest_cfg = vars(cfg) if hasattr(cfg, "__dict__") else {}
    manifest_cfg["action_space"] = "letters"
    manifest_cfg["n_train_rows"] = len(rows)
    manifest_cfg["k_candidates"] = K_CANDIDATES
    write_manifest(run_dir, run_id, seed=args.seed, argv=sys.argv,
                   config=manifest_cfg,
                   env_seeds_version="citation_real_eval_v1/action_space=letters",
                   base_model=args.model, parent_run_id=args.parent_run)
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds,
                         peft_config=peft_cfg, processing_class=tok,
                         callbacks=[make_log_callback(run_dir)])
    result = trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(str(run_dir / "adapter"))
    (run_dir / "metrics.json").write_text(json.dumps({
        "run_id": run_id, "model": args.model, "action_space": "letters",
        "split": args.split, "train_rows": len(rows), "epochs": args.epochs,
        "lr": args.lr, "final_loss": result.training_loss,
    }, indent=1))
    print(json.dumps({"status": "sft_citation_done", "run_id": run_id,
                      "adapter": str(run_dir / "adapter"),
                      "train_rows": len(rows),
                      "final_loss": result.training_loss}, indent=1))


if __name__ == "__main__":
    main()
