#!/usr/bin/env python3
"""Plan A-DPO: preference-optimize a small model on the escalation task.

Same task, same prompt renderer, and same reward ruler as SFT/GRPO, but the
signal is a preference pair per seed instead of a single oracle label or a
group of sampled rewards:

  prompt   : the same render_prompt(seed) used everywhere.
  chosen   : the analytic ORACLE plan JSON (argmax expected reward).
  rejected : the WRONG-action plan with the highest expected reward for that
             seed - the *most tempting mistake*. Computed from the env's
             analytic expected_rewards, excluding the oracle strategy, then
             rendered in the same one-line {"first":..,"on_fail":..} JSON.

Rationale: "oracle vs most-tempting-wrong" makes DPO push probability mass off
the single closest competitor rather than off a random wrong plan, which is
where an argmax-SFT policy actually leaks reward (e.g. cheap_finish vs
cheap_then_escalate, or a missed gate that scores well on cost).

CPU-buildable: `--pairs-only` builds and dumps the pairs with stdlib only (no
torch), so the pair design is inspectable without the GPU stack. The trainer
path (TRL 0.15.2 DPOTrainer) keeps all heavy imports inside main() after arg
parsing so `--help` and `--pairs-only` never need torch.

Usage:
  # CPU: build + inspect the 160 pairs
  python dpo_escalation.py --env-dir $ENV --lambda 0.3 --pairs-only \
      --pairs-out /tmp/dpo_pairs.jsonl
  # GPU: DPO from the SFT adapter
  python dpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV \
      --init-adapter runs/sft_qwen05b/<RUN_ID>/adapter \
      --out-dir runs/dpo_qwen05b --beta 0.1

Evaluate the resulting adapter with eval_escalation_policy.py on the SAME
frozen eval-256 as SFT/GRPO (identical ruler; see README pre-registered
criteria).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from reward_escalation import EscalationReward, render_prompt
from run_logging import make_log_callback, new_run_dir, write_manifest

# expected_rewards() key -> (first, on_fail) plan, so a strategy can be rendered
# in the same one-line JSON as chosen/rejected.
STRAT_TO_PLAN = {
    "gate": ("gate", "finish"),
    "deep": ("deep", "finish"),
    "cheap_finish": ("cheap", "finish"),
    "cheap_then_escalate_on_fail": ("cheap", "escalate"),
}


def plan_json(first: str, on_fail: str) -> str:
    """One-line plan JSON, identical format to build_sft_labels completions."""
    return json.dumps({"first": first, "on_fail": on_fail}, ensure_ascii=False)


def build_pairs(reward: EscalationReward, split: str) -> list[dict]:
    """One preference pair per seed in `split`: oracle vs most-tempting-wrong.

    chosen  = oracle strategy (argmax expected reward).
    rejected= the highest-expected-reward strategy that is NOT the oracle plan.
    """
    env = reward.env
    pairs = []
    for sid, seed in env.seeds.items():
        if split != "all" and seed["split"] != split:
            continue
        er = env.expected_rewards(sid, reward.lam)
        oracle_key = max(er, key=er.get)
        oracle_plan = STRAT_TO_PLAN[oracle_key]
        # most tempting wrong = argmax expected reward over the non-oracle plans
        wrong_key = max((k for k in er if k != oracle_key), key=er.get)
        wrong_plan = STRAT_TO_PLAN[wrong_key]
        pairs.append({
            "seed_id": sid,
            "prompt": render_prompt(seed),
            "chosen": " " + plan_json(*oracle_plan),
            "rejected": " " + plan_json(*wrong_plan),
            # provenance for inspection (not consumed by DPOTrainer)
            "oracle_key": oracle_key, "wrong_key": wrong_key,
            "gate_needed": bool(seed["requires_human_gate"]),
            "chosen_er": round(er[oracle_key], 4),
            "rejected_er": round(er[wrong_key], 4),
        })
    return pairs


def summarize(pairs: list[dict]) -> dict:
    """Label-mix + sanity summary for the pair set."""
    chosen_mix = Counter(p["oracle_key"] for p in pairs)
    rejected_mix = Counter(p["wrong_key"] for p in pairs)
    n_equal = sum(1 for p in pairs if p["chosen"].strip() == p["rejected"].strip())
    n_wrong_ge = sum(1 for p in pairs if p["rejected_er"] > p["chosen_er"] + 1e-9)
    return {
        "n_pairs": len(pairs),
        "gate_pairs": sum(1 for p in pairs if p["gate_needed"]),
        "chosen_mix": dict(chosen_mix),
        "rejected_mix": dict(rejected_mix),
        "pairs_with_chosen_eq_rejected": n_equal,
        "pairs_where_rejected_beats_chosen_er": n_wrong_ge,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=0.3)
    ap.add_argument("--split", default="train", choices=["train", "dev", "all"])
    ap.add_argument("--init-adapter", type=Path, default=None,
                    help="SFT adapter to init from (recommended: DPO refines SFT)")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="parent dir; each run writes into out-dir/<run_id>/ "
                         "(required unless --pairs-only)")
    ap.add_argument("--pairs-out", type=Path, default=None,
                    help="also dump the built pairs jsonl here for inspection")
    ap.add_argument("--pairs-only", action="store_true",
                    help="build + summarize (+optionally dump) pairs, then exit. "
                         "Stdlib only: no torch import, runs on CPU.")
    ap.add_argument("--beta", type=float, default=0.1, help="DPO beta")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--lr", type=float, default=5e-6)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=1, help="gradient_accumulation_steps")
    ap.add_argument("--max-prompt-len", type=int, default=768)
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", default=None,
                    help="checkpoint path (or 'True') to resume_from_checkpoint")
    ap.add_argument("--parent-run", default=None,
                    help="run_id of a failed run this re-run fixes (R4 linkage)")
    args = ap.parse_args()

    reward = EscalationReward(args.env_dir, lam=args.lam)
    pairs = build_pairs(reward, args.split)
    summary = summarize(pairs)

    if args.pairs_out:
        args.pairs_out.parent.mkdir(parents=True, exist_ok=True)
        with args.pairs_out.open("w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    if args.pairs_only:
        print(json.dumps({"status": "pairs_built", "split": args.split,
                          "lambda": args.lam, **summary,
                          "pairs_out": str(args.pairs_out) if args.pairs_out else None},
                         ensure_ascii=False, indent=1))
        return

    if args.out_dir is None:
        ap.error("--out-dir is required unless --pairs-only")
    # fail loud if the pair set is degenerate (identical chosen/rejected)
    if summary["pairs_with_chosen_eq_rejected"]:
        ap.error(f"{summary['pairs_with_chosen_eq_rejected']} pairs have "
                 f"chosen == rejected; refusing to train on degenerate prefs.")

    # heavy imports inside main so --help / --pairs-only work GPU-free
    import torch
    import transformers
    from datasets import Dataset
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    transformers.set_seed(args.seed)
    run_dir, run_id = new_run_dir(args.out_dir)

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto")
    if args.init_adapter:
        # refine the SFT adapter; trainable, ref = same base with adapter disabled
        model = PeftModel.from_pretrained(model, str(args.init_adapter), is_trainable=True)
        peft_cfg = None
    else:
        peft_cfg = LoraConfig(
            r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")

    ds = Dataset.from_list([{"prompt": p["prompt"], "chosen": p["chosen"],
                             "rejected": p["rejected"]} for p in pairs])

    cfg = DPOConfig(
        output_dir=str(run_dir), beta=args.beta, num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum, learning_rate=args.lr,
        max_prompt_length=args.max_prompt_len, max_length=args.max_len,
        logging_steps=10, save_strategy="epoch", save_total_limit=None,
        seed=args.seed, bf16=True, report_to=[],
    )
    manifest_cfg = vars(cfg) if hasattr(cfg, "__dict__") else {}
    manifest_cfg["pair_summary"] = summary
    write_manifest(run_dir, run_id, seed=args.seed, argv=sys.argv,
                   config=manifest_cfg, env_seeds_version=reward.env.seeds_version,
                   base_model=args.model, parent_run_id=args.parent_run)
    trainer = DPOTrainer(
        model=model, ref_model=None, args=cfg, train_dataset=ds,
        processing_class=tok, peft_config=peft_cfg,
        callbacks=[make_log_callback(run_dir)],
    )
    result = trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(str(run_dir / "adapter"))
    (run_dir / "metrics.json").write_text(json.dumps({
        "run_id": run_id, "model": args.model, "lambda": args.lam,
        "beta": args.beta, "epochs": args.epochs, "n_pairs": summary["n_pairs"],
        "init_adapter": str(args.init_adapter) if args.init_adapter else None,
        "final_loss": getattr(result, "training_loss", None),
    }, indent=1))
    print(json.dumps({"status": "dpo_done", "run_id": run_id,
                      "adapter": str(run_dir / "adapter")}, indent=1))


if __name__ == "__main__":
    main()
