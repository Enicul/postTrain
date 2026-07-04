#!/usr/bin/env python3
"""Plan C: ONE round of Training-Free GRPO rollouts (a GPU-bound primitive).

The orchestrator (Claude, outside this script) runs the round-by-round loop
from `training_free_grpo.run`; this script provides step 1+2 of a round on a
real model:

  1. rollout: for each of the first-N TRAIN seeds, sample K completions from
     `--model` at `--temperature`, with the current experience library (`--library`,
     optional JSON) injected into the system prompt via the SAME block format as
     `training_free_grpo.ExperienceLibrary.as_prompt_block`.
  2. semantic advantage: score every completion with the analytic
     `EscalationReward.plan_reward` (TRAIN-only, deterministic per parsed plan)
     and, per seed, contrast best-vs-worst where reward spread > 0
     (`training_free_grpo.semantic_advantage`), sorted by advantage desc.

Outputs into `--out DIR` (a run dir under it, never overwritten):
  * rollouts.jsonl     {seed_id, completion, plan:{first,on_fail}, reward}
  * contrasts.json     the semantic-advantage pairs (the raw material the
                       orchestrator distills <=3 lessons from)
  * round_summary.json mean reward, gate-violation rate, action mix, library sha
  * run_manifest.json  full provenance (run_logging.write_manifest)

Library injection reuses eval's build_prompt so a scored eval and a rollout see
byte-identical prompts. TEST is never touched here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from eval_escalation_policy import build_prompt
from reward_escalation import EscalationReward, parse_plan
from run_logging import new_run_dir, write_manifest
from training_free_grpo import ExperienceLibrary, Lesson, semantic_advantage


def load_library(path: Path | None) -> ExperienceLibrary:
    """Load a lessons JSON into an ExperienceLibrary. Accepts either a bare list
    of lesson dicts or {"final_library": [...]} / {"lessons": [...]} wrappers
    (the shapes training_free_grpo.run emits and the orchestrator hand-edits).
    Each lesson dict needs lesson_id, trigger, rule; round_added is optional."""
    if path is None:
        return ExperienceLibrary()
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("final_library") or raw.get("lessons") or []
    lessons = [Lesson(lesson_id=l["lesson_id"], trigger=l["trigger"],
                      rule=l["rule"], round_added=l.get("round_added", 0))
               for l in raw]
    return ExperienceLibrary(lessons)


def library_block_and_sha(lib: ExperienceLibrary) -> tuple[str, str]:
    """The as_prompt_block() text + its sha256 ('' block -> sha of empty str)."""
    block = lib.as_prompt_block()
    return block, hashlib.sha256(block.encode("utf-8")).hexdigest()


def select_seed_ids(reward: EscalationReward, split: str, n: int) -> list[str]:
    """Deterministic first-N seeds of `split`, sorted by seed_id."""
    ids = sorted(sid for sid, s in reward.env.seeds.items() if s["split"] == split)
    return ids[:n]


def summarize(rollouts: list[dict], reward: EscalationReward,
              lib_sha: str) -> dict:
    """Round-level metrics: mean reward, gate-violation rate (gate-needed seeds
    whose sampled plan did not gate), action mix over all completions."""
    n = max(1, len(rollouts))
    mean_reward = round(sum(r["reward"] for r in rollouts) / n, 4)
    first_mix = Counter(r["plan"]["first"] for r in rollouts)
    onfail_mix = Counter(r["plan"]["on_fail"] for r in rollouts)
    gate_needed = viol = 0
    for r in rollouts:
        if reward.env.seeds[r["seed_id"]]["requires_human_gate"]:
            gate_needed += 1
            if r["plan"]["first"] != "gate":
                viol += 1
    return {"n_rollouts": len(rollouts), "mean_reward": mean_reward,
            "gate_needed_rollouts": gate_needed,
            "gate_violation_rate": round(viol / max(1, gate_needed), 4),
            "action_mix_first": dict(first_mix),
            "action_mix_on_fail": dict(onfail_mix),
            "library_sha256": lib_sha}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--split", default="train", choices=["train", "dev", "test", "all"])
    ap.add_argument("--seed-subset", type=int, default=60,
                    help="deterministic first-N seeds of --split, sorted by seed_id")
    ap.add_argument("--library", type=Path, default=None,
                    help="optional lessons JSON; injected via the SAME block format "
                         "as training_free_grpo.ExperienceLibrary.as_prompt_block")
    ap.add_argument("--k", type=int, default=8, help="sampled completions per seed")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--lambda", dest="lam", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--loader", default="causal", choices=["causal", "auto"])
    ap.add_argument("--out", type=Path, required=True,
                    help="parent dir; the round writes into out/<run_id>/")
    ap.add_argument("--parent-run", default=None,
                    help="run_id of the prior round (provenance chain)")
    args = ap.parse_args()

    reward = EscalationReward(args.env_dir, lam=args.lam)
    lib = load_library(args.library)
    block, lib_sha = library_block_and_sha(lib)
    extra_system = block or None  # empty library -> byte-identical prompt
    ids = select_seed_ids(reward, args.split, args.seed_subset)
    if not ids:
        raise SystemExit(f"no seeds for split={args.split}")

    run_dir, run_id = new_run_dir(args.out)

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    transformers.set_seed(args.seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if args.loader == "causal":
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16, device_map="auto")
    else:
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.model, torch_dtype=torch.bfloat16, device_map="auto")
        except (ValueError, KeyError, OSError, TypeError) as e:
            from transformers import AutoModelForImageTextToText
            print(json.dumps({"loader_fallback": "AutoModelForImageTextToText",
                              "causal_error": str(e)[:200]}))
            model = AutoModelForImageTextToText.from_pretrained(
                args.model, torch_dtype=torch.bfloat16, device_map="auto")
    model.eval()

    def build_input(prompt_text: str):
        msgs = [{"role": "user", "content": prompt_text}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        return tok(text, return_tensors="pt").to(model.device)

    rollouts: list[dict] = []
    for sid in ids:
        seed = reward.env.seeds[sid]
        enc = build_input(build_prompt(seed, extra_system))
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=48, do_sample=True,
                temperature=args.temperature, num_return_sequences=args.k,
                pad_token_id=tok.pad_token_id or tok.eos_token_id)
        for row in gen:
            comp = tok.decode(row[enc.input_ids.shape[1]:], skip_special_tokens=True)
            first, on_fail = parse_plan(comp)
            r = reward.plan_reward(sid, first, on_fail)
            rollouts.append({"seed_id": sid, "completion": comp,
                             "plan": {"first": first, "on_fail": on_fail},
                             "reward": round(r, 4)})

    # semantic advantage per seed (best-vs-worst where spread>0), sorted desc
    by_seed: dict[str, list[dict]] = {}
    for r in rollouts:
        by_seed.setdefault(r["seed_id"], []).append(
            {"seed_id": r["seed_id"], "completion": r["completion"],
             "plan": r["plan"], "reward": r["reward"]})
    contrasts = [c for c in (semantic_advantage(g) for g in by_seed.values()) if c]
    contrasts.sort(key=lambda c: -c["advantage"])

    summary = summarize(rollouts, reward, lib_sha)

    (run_dir / "rollouts.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rollouts),
        encoding="utf-8")
    (run_dir / "contrasts.json").write_text(
        json.dumps(contrasts, ensure_ascii=False, indent=1), encoding="utf-8")
    (run_dir / "round_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    write_manifest(
        run_dir, run_id, seed=args.seed, argv=sys.argv,
        config={"model": args.model, "split": args.split,
                "seed_subset": args.seed_subset, "n_seeds": len(ids), "k": args.k,
                "temperature": args.temperature, "lam": args.lam,
                "library_path": str(args.library) if args.library else None,
                "library_sha256": lib_sha, "n_lessons": len(lib.lessons)},
        env_seeds_version=reward.env.seeds_version,
        base_model=args.model, parent_run_id=args.parent_run)

    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir),
                      "n_seeds": len(ids), "n_rollouts": len(rollouts),
                      "n_contrasts": len(contrasts), **summary}, ensure_ascii=False,
                     indent=1))


if __name__ == "__main__":
    main()
