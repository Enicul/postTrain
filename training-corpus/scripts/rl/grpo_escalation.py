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
                    help="optional SFT adapter to warm-start from (LoRA mode only)")
    ap.add_argument("--init-model", type=Path, default=None,
                    help="full-FT mode: load base weights from a local full_model "
                         "dir (e.g. a full-FT SFT run's <run_dir>/full_model/) "
                         "instead of the hub --model id. E2 honest design: full-FT "
                         "GRPO from the full-FT SFT init.")
    ap.add_argument("--full-finetune", action="store_true",
                    help="train the base model's FULL parameters (no peft/LoRA "
                         "wrapping). Saves the full model into <run_dir>/full_model/. "
                         "Default off keeps the LoRA path byte-identical. E2 probe.")
    ap.add_argument("--optim", default="adamw_torch",
                    help="optimizer passed to GRPOConfig. Default adamw_torch; use "
                         "adamw_bnb_8bit for the 7B full-FT arm (needs bitsandbytes).")
    ap.add_argument("--gradient-checkpointing", action="store_true",
                    help="enable gradient checkpointing in the config (needed at "
                         "3B+/7B full-FT to fit the single A100 80GB).")
    ap.add_argument("--out-dir", type=Path, required=True,
                    help="parent dir; each run writes into out-dir/<run_id>/")
    ap.add_argument("--split", default="train", choices=["train", "dev", "all"])
    ap.add_argument("--num-generations", type=int, default=8)  # K
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--gate-oversample", type=int, default=1,
                    help="repeat every gate-required seed N times in the train "
                         "prompt list. Motivation: on all-violate groups the "
                         "group-relative advantage is identically zero (all K "
                         "samples miss the gate -> same reward -> no signal). "
                         "Duplicating gate seeds seeds mixed groups so some "
                         "member can gate correctly and advantage stops zeroing.")
    ap.add_argument("--kl-beta", type=float, default=None,
                    help="GRPOConfig beta (KL coeff). Default None -> TRL default.")
    ap.add_argument("--grad-accum", type=int, default=1, help="gradient_accumulation_steps")
    ap.add_argument("--save-steps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", default=None,
                    help="checkpoint path (or 'True') to resume_from_checkpoint")
    ap.add_argument("--parent-run", default=None,
                    help="run_id of a failed run this re-run fixes (R4 linkage)")
    args = ap.parse_args()

    # num_generations must divide the per-device batch (TRL groups K samples of
    # one prompt inside a batch); fail loud and early rather than deep in TRL.
    if args.batch_size % args.num_generations != 0:
        ap.error(f"--num-generations ({args.num_generations}) must divide "
                 f"--batch-size ({args.batch_size}); "
                 f"got remainder {args.batch_size % args.num_generations}.")
    if args.gate_oversample < 1:
        ap.error(f"--gate-oversample must be >= 1, got {args.gate_oversample}")

    # full-FT / LoRA combos: keep them explicit and mutually exclusive. An
    # adapter is a LoRA artifact and cannot warm-start a full-param run; the
    # honest full-FT init is a full_model dir via --init-model.
    if args.full_finetune and args.init_adapter:
        ap.error("--full-finetune is incompatible with --init-adapter (an adapter "
                 "is a LoRA artifact); for a full-FT warm start use --init-model "
                 "<full_model dir> instead.")
    if args.init_model and not args.full_finetune:
        ap.error("--init-model only applies in full-FT mode; pass --full-finetune "
                 "(or use --init-adapter for a LoRA warm start).")

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
    # gate-oversample: repeat each gate-required seed N times so mixed groups
    # exist and group-relative advantage stops zeroing on all-violate groups.
    rows, n_gate_rows = [], 0
    for sid, s in seeds:
        reps = args.gate_oversample if s["requires_human_gate"] else 1
        for _ in range(reps):
            rows.append({"prompt": render_prompt(s), "seed_id": sid})
        if s["requires_human_gate"]:
            n_gate_rows += reps
    prompts = Dataset.from_list(rows)

    # full-FT (E2) loads base weights from --init-model (a local full_model dir)
    # when given, else the hub --model id; the tokenizer stays with --model.
    parameterization = "full" if args.full_finetune else "lora"
    load_path = str(args.init_model) if (args.full_finetune and args.init_model) else args.model
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        load_path, torch_dtype=torch.bfloat16, device_map="auto")
    if args.full_finetune:
        # no peft wrapping: all base params are trainable.
        peft_cfg = None
    elif args.init_adapter:
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

    cfg_kw = dict(
        output_dir=str(run_dir), learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_generations=args.num_generations, max_completion_length=48,
        max_steps=args.steps, logging_steps=10, save_strategy="steps",
        save_steps=args.save_steps, save_total_limit=None, seed=args.seed,
        bf16=True, report_to=[],
        optim=args.optim, gradient_checkpointing=args.gradient_checkpointing,
    )
    if args.kl_beta is not None:  # else leave TRL's default beta
        cfg_kw["beta"] = args.kl_beta
    cfg = GRPOConfig(**cfg_kw)
    manifest_cfg = vars(cfg) if hasattr(cfg, "__dict__") else {}
    # record the oversample provenance (not a GRPOConfig field) in the manifest
    manifest_cfg["parameterization"] = parameterization
    manifest_cfg["optim"] = args.optim
    manifest_cfg["init_model"] = str(args.init_model) if args.init_model else None
    manifest_cfg["gate_oversample"] = args.gate_oversample
    manifest_cfg["gate_prompt_rows"] = n_gate_rows
    manifest_cfg["total_prompt_rows"] = len(prompts)
    write_manifest(run_dir, run_id, seed=args.seed, argv=sys.argv,
                   config=manifest_cfg,
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
    # full-FT saves the whole model (eval via --model <dir>, no --adapter);
    # LoRA saves just the adapter into adapter/ (eval via --adapter).
    save_sub = "full_model" if args.full_finetune else "adapter"
    trainer.save_model(str(run_dir / save_sub))
    (run_dir / "metrics.json").write_text(json.dumps({
        "run_id": run_id, "model": args.model, "lambda": args.lam,
        "K": args.num_generations, "batch_size": args.batch_size,
        "gate_oversample": args.gate_oversample, "kl_beta": args.kl_beta,
        "steps": args.steps, "parameterization": parameterization,
        "optim": args.optim, "gradient_checkpointing": args.gradient_checkpointing,
        "init_adapter": str(args.init_adapter) if args.init_adapter else None,
        "init_model": str(args.init_model) if args.init_model else None,
        "final_loss": getattr(result, "training_loss", None),
    }, indent=1))
    print(json.dumps({"status": "grpo_done", "run_id": run_id,
                      "parameterization": parameterization,
                      save_sub: str(run_dir / save_sub)}, indent=1))


if __name__ == "__main__":
    main()
