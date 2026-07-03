#!/usr/bin/env python3
"""Plan A3: GRPO a small model on the escalation env reward.

Pull-and-run on an A100. Reward = the env's analytic expected reward for the
plan the model emits (deterministic per parsed plan; advantage comes from
within-group plan diversity across K samples of the same prompt). Optionally
warm-starts from the A2 SFT adapter. Saves adapter + metrics only.

Usage:
  python grpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct \
      --env-dir <ENV> --lambda 0.3 --out-dir runs/grpo_escalation_qwen05b \
      [--init-adapter runs/sft_escalation_qwen05b/adapter]

The pre-registered kill criterion (checked afterward with
eval_escalation_policy.py on the frozen eval-256): GRPO must beat argmax-SFT
by >= 3 reward points AND not drop gate recall, else record "SFT suffices".
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from reward_escalation import EscalationReward, parse_plan, render_prompt
from run_logging import make_log_callback, new_run_dir, write_manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=0.3)
    ap.add_argument("--init-adapter", type=Path, default=None,
                    help="optional SFT adapter to warm-start from")
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="parent dir; each run writes into out-dir/<run_id>/")
    ap.add_argument("--split", default="train", choices=["train", "dev", "all"])
    ap.add_argument("--num-generations", type=int, default=8)  # K
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=1, help="gradient_accumulation_steps")
    ap.add_argument("--save-steps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", default=None,
                    help="checkpoint path (or 'True') to resume_from_checkpoint")
    ap.add_argument("--parent-run", default=None,
                    help="run_id of a failed run this re-run fixes (R4 linkage)")
    args = ap.parse_args()

    import torch
    import transformers
    from datasets import Dataset
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import GRPOConfig, GRPOTrainer

    transformers.set_seed(args.seed)

    reward = EscalationReward(args.env_dir, lam=args.lam)
    run_dir, run_id = new_run_dir(args.out_dir)
    seeds = [(sid, s) for sid, s in reward.env.seeds.items()
             if args.split == "all" or s["split"] == args.split]
    prompts = Dataset.from_list([{"prompt": render_prompt(s), "seed_id": sid}
                                 for sid, s in seeds])

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto")
    if args.init_adapter:
        model = PeftModel.from_pretrained(model, str(args.init_adapter), is_trainable=True)
        peft_cfg = None
    else:
        peft_cfg = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")

    # G5/G6 observability (R3 core): per-completion generations + per-batch
    # reward trace. Buffered file handles, flushed per batch.
    gen_fh = open(run_dir / "generations.jsonl", "a", buffering=1)
    trace_fh = open(run_dir / "reward_trace.jsonl", "a", buffering=1)
    counters = {"step": 0, "batch": 0}

    def reward_fn(completions, seed_id, **_):
        # TRL passes dataset columns (seed_id) aligned with completions
        counters["step"] += 1
        counters["batch"] += 1
        rewards, mix, gate_viol = [], Counter(), 0
        n_gate_needed = 0
        for c, sid in zip(completions, seed_id):
            first, on_fail = parse_plan(c)
            r = reward.plan_reward(sid, first, on_fail)
            rewards.append(r)
            gen_fh.write(json.dumps({
                "step_counter": counters["step"], "seed_id": sid,
                "completion": c, "parsed_plan": [first, on_fail], "reward": r}) + "\n")
            # action mix: cheap / deep / gate; parse_fallback = safest default plan
            if (first, on_fail) == ("gate", "finish"):
                mix["gate"] += 1
            elif first in ("cheap", "deep", "gate"):
                mix[first] += 1
            else:
                mix["parse_fallback"] += 1
            if reward.env.seeds[sid]["requires_human_gate"]:
                n_gate_needed += 1
                if first != "gate":
                    gate_viol += 1
        mean_r = sum(rewards) / max(1, len(rewards))
        trace_fh.write(json.dumps({
            "batch_idx": counters["batch"],
            "mean_reward": round(mean_r, 4),
            "gate_violation_rate": round(gate_viol / max(1, n_gate_needed), 4),
            "action_mix": {"cheap": mix.get("cheap", 0), "deep": mix.get("deep", 0),
                           "gate": mix.get("gate", 0),
                           "parse_fallback": mix.get("parse_fallback", 0)}}) + "\n")
        gen_fh.flush()
        trace_fh.flush()
        return rewards

    cfg = GRPOConfig(
        output_dir=str(run_dir), learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_generations=args.num_generations, max_completion_length=48,
        max_steps=args.steps, logging_steps=10, save_strategy="steps",
        save_steps=args.save_steps, save_total_limit=None, seed=args.seed,
        bf16=True, report_to=[],
    )
    write_manifest(run_dir, run_id, seed=args.seed, argv=sys.argv,
                   config=vars(cfg) if hasattr(cfg, "__dict__") else {},
                   env_seeds_version=reward.env.seeds_version,
                   base_model=args.model, parent_run_id=args.parent_run)
    trainer = GRPOTrainer(
        model=model, args=cfg, train_dataset=prompts,
        reward_funcs=reward_fn, processing_class=tok,
        peft_config=peft_cfg, callbacks=[make_log_callback(run_dir)],
    )
    result = trainer.train(resume_from_checkpoint=args.resume)
    gen_fh.close()
    trace_fh.close()
    trainer.save_model(str(run_dir / "adapter"))
    (run_dir / "metrics.json").write_text(json.dumps({
        "run_id": run_id, "model": args.model, "lambda": args.lam,
        "K": args.num_generations, "steps": args.steps,
        "init_adapter": str(args.init_adapter) if args.init_adapter else None,
        "final_loss": getattr(result, "training_loss", None),
    }, indent=1))
    print(json.dumps({"status": "grpo_done", "run_id": run_id,
                      "adapter": str(run_dir / "adapter")}, indent=1))


if __name__ == "__main__":
    main()
