#!/usr/bin/env python3
"""Plan B: first GRPO run on the citation evidence-chain agentic env.

Same trainer shape as grpo_escalation.py, but the prompt/reward come from
CitationAgenticEnv: the policy emits {"cite": <evidence_id>, "verdict":
<label>} in one generation; reward is the env's process+outcome score
(valid-citation shaping, fabricated-id hard negative, gold-span bonus, verdict
match). Advantage comes from within-group diversity across K samples of the
same claim.

Two modes in one file:
  train (default) : GRPO on split=="train" claims. Writes generations.jsonl +
                    reward_trace.jsonl (mean_reward, fabricated_rate,
                    gold_cite_rate, verdict_acc), plus the usual run
                    provenance. Warm-starts from --init-adapter if given.
  --eval-only     : greedy per-claim generation on --split, reports
                    {verdict_acc, cite_valid_rate, cite_gold_rate,
                    fabricated_rate, mean_reward} to --out. --adapter is
                    optional: with none, this is the PROMPTED BASELINE the
                    trained policy is pre-registered to beat.

Usage:
  # CPU dry parse test (no model): feed a fake completion through env.reward
  python grpo_citation.py --eval-dir $CENV --dry-parse
  # GPU train
  python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
      --out-dir runs/grpo_citation_qwen05b
  # GPU eval (prompted baseline, no adapter)
  python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
      --eval-only --split test --out runs/citation_baseline.json
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


def eval_report(env: CitationAgenticEnv, results: list[dict]) -> dict:
    """Aggregate per-claim env.reward() dicts into the pre-registered metrics."""
    n = max(1, len(results))
    verdict = sum(1 for r in results if r["verdict_ok"]) / n
    cite_valid = sum(1 for r in results if r["cite_ok"]) / n
    cite_gold = sum(1 for r in results if r["cite_gold"]) / n
    # fabricated = a cite was emitted but is not in the pool
    fabricated = sum(1 for r in results
                     if (r["cite_ok"] is False and r["parts"]["citation"] < 0)) / n
    mean_r = sum(r["reward"] for r in results) / n
    return {"n": len(results), "verdict_acc": round(verdict, 4),
            "cite_valid_rate": round(cite_valid, 4),
            "cite_gold_rate": round(cite_gold, 4),
            "fabricated_rate": round(fabricated, 4),
            "mean_reward": round(mean_r, 4)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--eval-dir", type=Path, required=True,
                    help="citation_real_eval_v1 dir (has rows/all.jsonl)")
    ap.add_argument("--action-space", default="raw_id", choices=["raw_id", "letters"],
                    help="raw_id (v1: cite the long evidence_id verbatim) or "
                         "letters (v2, D-2026-07-04-002: cite a menu letter A-F "
                         "that the harness maps back to the id; fabrication = "
                         "off-menu letter). Default raw_id keeps v1 intact.")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="parent dir for train runs; out-dir/<run_id>/")
    ap.add_argument("--init-adapter", type=Path, default=None)
    ap.add_argument("--split", default="train", choices=["train", "dev", "test", "all"])
    ap.add_argument("--num-generations", type=int, default=8)  # K
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--kl-beta", type=float, default=None,
                    help="GRPOConfig beta (KL coeff). Default None -> TRL default.")
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--grad-accum", type=int, default=1, help="gradient_accumulation_steps")
    ap.add_argument("--save-steps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", default=None,
                    help="checkpoint path (or 'True') to resume_from_checkpoint")
    ap.add_argument("--parent-run", default=None,
                    help="run_id of a failed run this re-run fixes (R4 linkage)")
    # eval / dry-parse modes
    ap.add_argument("--eval-only", action="store_true",
                    help="greedy per-claim eval instead of training")
    ap.add_argument("--adapter", type=Path, default=None,
                    help="eval mode: LoRA adapter; omit for the prompted baseline")
    ap.add_argument("--out", type=Path, default=None, help="eval mode: report json path")
    ap.add_argument("--dry-parse", action="store_true",
                    help="CPU: run one fake completion through env.reward and exit "
                         "(no model load), to smoke the reward/parse wiring.")
    args = ap.parse_args()

    env = CitationAgenticEnv(args.eval_dir, action_space=args.action_space)

    # ---- CPU dry parse test: no torch, verify reward wiring on a fake completion
    if args.dry_parse:
        cid = next(c for c, m in env.claims.items() if m["split"] in ("test", "all", "train"))
        gold = env.claims[cid]["gold_evidence_id"]
        gold_label = env.claims[cid]["gold_label"]
        if args.action_space == "letters":
            lmap = env.letter_map(cid, K_CANDIDATES)
            gold_cite = next((l for l, e in lmap.items() if e == gold), "A")
            fab_cite = "Z"  # off-menu letter -> the v2 fabricated hard negative
        else:
            gold_cite, fab_cite = gold, "NOPE:block:999"
        good = json.dumps({"cite": gold_cite, "verdict": gold_label})
        fab = json.dumps({"cite": fab_cite, "verdict": "insufficient"})
        rep = eval_report(env, [env.reward(cid, good), env.reward(cid, fab)])
        print(json.dumps({"status": "dry_parse_ok", "action_space": args.action_space,
                          "claim": cid, "gold_cite": gold_cite, "fab_cite": fab_cite,
                          "perfect_play": env.reward(cid, good),
                          "fabricated": env.reward(cid, fab),
                          "report_over_the_two": rep}, ensure_ascii=False, indent=1))
        return

    ids = [cid for cid, m in env.claims.items()
           if args.split == "all" or m["split"] == args.split]

    # train-mode preconditions checked BEFORE heavy imports so they fail loud
    # GPU-free (mirrors grpo_escalation's early validation).
    if not args.eval_only:
        if args.out_dir is None:
            ap.error("--out-dir is required for training (omit --eval-only)")
        if args.batch_size % args.num_generations != 0:
            ap.error(f"--num-generations ({args.num_generations}) must divide "
                     f"--batch-size ({args.batch_size}); "
                     f"got remainder {args.batch_size % args.num_generations}.")

    # heavy imports inside main so --help / --dry-parse work GPU-free
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    transformers.set_seed(args.seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    # ---- eval / prompted-baseline mode ---------------------------------------
    if args.eval_only:
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16, device_map="auto")
        if args.adapter:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, str(args.adapter))
        model.eval()
        results = []
        for cid in ids:
            msgs = [{"role": "user", "content": env.render_prompt(cid, K_CANDIDATES)}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            enc = tok(text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=48, do_sample=False,
                                     pad_token_id=tok.pad_token_id or tok.eos_token_id)
            comp = tok.decode(gen[0][enc.input_ids.shape[1]:], skip_special_tokens=True)
            results.append(env.reward(cid, comp))
        rep = eval_report(env, results)
        rep.update({"split": args.split, "model": args.model,
                    "action_space": args.action_space,
                    "adapter": str(args.adapter) if args.adapter else None,
                    "mode": "adapter" if args.adapter else "prompted_baseline"})
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
        return

    # ---- train mode ----------------------------------------------------------
    from datasets import Dataset
    from peft import LoraConfig, PeftModel
    from trl import GRPOConfig, GRPOTrainer

    run_dir, run_id = new_run_dir(args.out_dir)
    prompts = Dataset.from_list(
        [{"prompt": env.render_prompt(cid, K_CANDIDATES), "claim_id": cid} for cid in ids])

    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto")
    if args.init_adapter:
        model = PeftModel.from_pretrained(model, str(args.init_adapter), is_trainable=True)
        peft_cfg = None
    else:
        peft_cfg = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")

    gen_fh = open(run_dir / "generations.jsonl", "a", buffering=1)
    trace_fh = open(run_dir / "reward_trace.jsonl", "a", buffering=1)
    counters = {"step": 0, "batch": 0}

    def reward_fn(completions, claim_id, **_):
        counters["step"] += 1
        counters["batch"] += 1
        rewards, res = [], []
        verdict_mix = Counter()
        for c, cid in zip(completions, claim_id):
            d = env.reward(cid, c)
            rewards.append(d["reward"])
            res.append(d)
            cite, verdict = env.parse(c)
            verdict_mix[verdict or "none"] += 1
            gen_fh.write(json.dumps({
                "step_counter": counters["step"], "claim_id": cid,
                "completion": c, "cite": cite, "verdict": verdict,
                "reward": d["reward"], "parts": d["parts"]}, ensure_ascii=False) + "\n")
        n = max(1, len(res))
        trace_fh.write(json.dumps({
            "batch_idx": counters["batch"],
            "mean_reward": round(sum(rewards) / n, 4),
            "fabricated_rate": round(
                sum(1 for d in res if d["cite_ok"] is False
                    and d["parts"]["citation"] < 0) / n, 4),
            "gold_cite_rate": round(sum(1 for d in res if d["cite_gold"]) / n, 4),
            "verdict_acc": round(sum(1 for d in res if d["verdict_ok"]) / n, 4),
            "verdict_mix": dict(verdict_mix)}, ensure_ascii=False) + "\n")
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
    )
    if args.kl_beta is not None:
        cfg_kw["beta"] = args.kl_beta
    cfg = GRPOConfig(**cfg_kw)
    manifest_cfg = vars(cfg) if hasattr(cfg, "__dict__") else {}
    manifest_cfg["k_candidates"] = K_CANDIDATES
    manifest_cfg["n_train_claims"] = len(prompts)
    manifest_cfg["action_space"] = args.action_space
    write_manifest(run_dir, run_id, seed=args.seed, argv=sys.argv,
                   config=manifest_cfg,
                   env_seeds_version=f"citation_real_eval_v1/action_space={args.action_space}",
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
        "run_id": run_id, "model": args.model, "K": args.num_generations,
        "batch_size": args.batch_size, "kl_beta": args.kl_beta, "steps": args.steps,
        "action_space": args.action_space,
        "init_adapter": str(args.init_adapter) if args.init_adapter else None,
        "final_loss": getattr(result, "training_loss", None),
    }, indent=1))
    print(json.dumps({"status": "grpo_citation_done", "run_id": run_id,
                      "adapter": str(run_dir / "adapter")}, indent=1))


if __name__ == "__main__":
    main()
