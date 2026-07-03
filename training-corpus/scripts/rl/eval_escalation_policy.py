#!/usr/bin/env python3
"""Score a policy on the frozen escalation eval, for A1 (prompted) and A4.

Two input modes:
  --pred-file P.jsonl   rows {"seed_id"|"qid","first","on_fail"} (any external
                        policy, e.g. a prompted-small-model dump). qid uses the
                        env anon mapping.
  --model / --adapter   load a HF model (+optional LoRA adapter), generate a
                        plan per seed at temperature 0, parse, score. This is
                        how SFT/GRPO adapters are evaluated.

Reports reward (lambda sweep), gate recall, mean cost, mean success, and the
pre-registered kill-criteria comparison when --baseline-reward is given.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from reward_escalation import EscalationReward, parse_plan, render_prompt

LAMBDAS = [0.1, 0.3, 0.6]


def majority_plan(plans: list[tuple[str, str]]) -> tuple[str, str]:
    """Most common (first, on_fail) plan across N samples; ties -> first seen
    among the most-common (Counter.most_common preserves insertion order)."""
    return Counter(plans).most_common(1)[0][0]


def score_samples(reward: EscalationReward, samples_of: dict, ids: list[str]) -> dict:
    """Per-sample-averaged metrics over N plans/seed: every sampled plan is
    scored, then averaged (so a seed with N samples contributes N scores)."""
    env = reward.env
    out = {}
    for lam in LAMBDAS:
        reward.lam = lam
        tot_r = tot_c = succ = 0.0
        gn = hit = 0
        n_scored = 0
        for sid in ids:
            seed = env.seeds[sid]
            gate_needed = seed["requires_human_gate"]
            p = env.p[sid]
            for first, on_fail in samples_of[sid]:
                n_scored += 1
                if gate_needed:
                    gn += 1
                    if first == "gate":
                        hit += 1
                tot_r += reward.plan_reward(sid, first, on_fail)
                if first == "gate":
                    c, s = env.c_gate, (1.0 if gate_needed else 0.0)
                elif first == "deep":
                    c, s = env.c_deep, 1.0
                elif on_fail == "escalate":
                    c, s = env.c_cheap + (1 - p) * env.c_deep, 1.0
                else:
                    c, s = env.c_cheap, p
                tot_c += c
                succ += s
        n = max(1, n_scored)
        out[lam] = {"reward": round(tot_r / n, 4), "cost": round(tot_c / n, 4),
                    "success": round(succ / n, 4), "gate_recall": round(hit / max(1, gn), 4)}
    return out


def gate_action_presence_rate(reward: EscalationReward, samples_of: dict, ids: list[str]) -> dict:
    """Fraction of gate-needed seeds where >=1 of the N samples chose 'gate'.

    Distinguishes a DECODING-mode collapse (gate mass survives under sampling,
    presence high, but greedy gate_recall=0) from a knowledge loss (presence
    also 0). See the pre-registered bar in README (F-2026-07-04-002 follow-up)."""
    env = reward.env
    gate_ids = [sid for sid in ids if env.seeds[sid]["requires_human_gate"]]
    present = sum(1 for sid in gate_ids
                  if any(first == "gate" for first, _ in samples_of[sid]))
    return {"gate_needed_seeds": len(gate_ids), "seeds_with_gate_in_samples": present,
            "gate_action_presence_rate": round(present / max(1, len(gate_ids)), 4)}


def score(reward: EscalationReward, plan_of: dict, ids: list[str]) -> dict:
    env = reward.env
    out = {}
    for lam in LAMBDAS:
        reward.lam = lam
        tot_r = tot_c = succ = 0.0
        gn = hit = 0
        for sid in ids:
            first, on_fail = plan_of[sid]
            seed = env.seeds[sid]
            gate_needed = seed["requires_human_gate"]
            if gate_needed:
                gn += 1
                if first == "gate":
                    hit += 1
            tot_r += reward.plan_reward(sid, first, on_fail)
            p = env.p[sid]
            if first == "gate":
                c, s = env.c_gate, (1.0 if gate_needed else 0.0)
            elif first == "deep":
                c, s = env.c_deep, 1.0
            elif on_fail == "escalate":
                c, s = env.c_cheap + (1 - p) * env.c_deep, 1.0
            else:
                c, s = env.c_cheap, p
            tot_c += c
            succ += s
        n = len(ids)
        out[lam] = {"reward": round(tot_r / n, 4), "cost": round(tot_c / n, 4),
                    "success": round(succ / n, 4), "gate_recall": round(hit / max(1, gn), 4)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--split", default="test", choices=["dev", "test", "all"])
    ap.add_argument("--pred-file", type=Path, default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--adapter", type=Path, default=None)
    ap.add_argument("--baseline-reward", type=float, default=None,
                    help="argmax-SFT reward at lambda 0.3 for the kill check")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="model mode: sampling temperature. 0 (default) = greedy, "
                         "argmax, unchanged behaviour.")
    ap.add_argument("--n-samples", type=int, default=1,
                    help="model mode: N plans sampled per seed. 1 (default) = "
                         "greedy single decode. N>1 samples at --temperature and "
                         "reports BOTH per-sample-averaged and majority-vote-plan "
                         "metrics plus gate_action_presence_rate "
                         "(F-2026-07-04-002 follow-up).")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dump-preds", type=Path, default=None,
                    help="model mode only: write per-seed jsonl {seed_id, first, "
                         "on_fail, gate_needed, oracle_action, completion} so the "
                         "exact missed gate seeds are identifiable.")
    args = ap.parse_args()

    reward = EscalationReward(args.env_dir, lam=0.3)
    ids = [sid for sid, s in reward.env.seeds.items()
           if args.split == "all" or s["split"] == args.split]
    plan_of: dict[str, tuple[str, str]] = {}
    samples_of: dict[str, list[tuple[str, str]]] = {}  # sampled-mode: N plans/seed
    sampled_mode = bool(args.model) and args.n_samples > 1

    if args.pred_file:
        mapping = {}
        mp = args.env_dir / "env_anon_mapping.json"
        if mp.exists():
            mapping = json.loads(mp.read_text())
        for line in args.pred_file.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            sid = r.get("seed_id") or mapping.get(r.get("qid"))
            if sid in reward.env.seeds:
                plan_of[sid] = (r["first"], r["on_fail"])
    elif args.model:
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        transformers.set_seed(args.seed)
        tok = AutoTokenizer.from_pretrained(args.model)
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16, device_map="auto")
        if args.adapter:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, str(args.adapter))
        model.eval()
        dump_fh = None
        if args.dump_preds:
            args.dump_preds.parent.mkdir(parents=True, exist_ok=True)
            dump_fh = args.dump_preds.open("w", encoding="utf-8")
        for sid in ids:
            seed = reward.env.seeds[sid]
            msgs = [{"role": "user", "content": render_prompt(seed)}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            enc = tok(text, return_tensors="pt").to(model.device)
            if sampled_mode:
                # N samples/seed at temperature T (num_return_sequences batches them)
                with torch.no_grad():
                    gen = model.generate(
                        **enc, max_new_tokens=48, do_sample=True,
                        temperature=args.temperature, num_return_sequences=args.n_samples,
                        pad_token_id=tok.pad_token_id or tok.eos_token_id)
                plans = []
                for row in gen:
                    comp = tok.decode(row[enc.input_ids.shape[1]:], skip_special_tokens=True)
                    plans.append(parse_plan(comp))
                samples_of[sid] = plans
                plan_of[sid] = majority_plan(plans)  # majority-vote plan for the point metric
                if dump_fh is not None:
                    dump_fh.write(json.dumps({
                        "seed_id": sid, "majority_first": plan_of[sid][0],
                        "majority_on_fail": plan_of[sid][1],
                        "gate_needed": bool(seed["requires_human_gate"]),
                        "oracle_action": reward.env.oracle_action(sid, 0.3),
                        "samples": [{"first": f, "on_fail": o} for f, o in plans]},
                        ensure_ascii=False) + "\n")
            else:
                with torch.no_grad():
                    gen = model.generate(**enc, max_new_tokens=48, do_sample=False,
                                         pad_token_id=tok.pad_token_id or tok.eos_token_id)
                comp = tok.decode(gen[0][enc.input_ids.shape[1]:], skip_special_tokens=True)
                first, on_fail = parse_plan(comp)
                plan_of[sid] = (first, on_fail)
                if dump_fh is not None:
                    dump_fh.write(json.dumps({
                        "seed_id": sid, "first": first, "on_fail": on_fail,
                        "gate_needed": bool(seed["requires_human_gate"]),
                        "oracle_action": reward.env.oracle_action(sid, 0.3),
                        "completion": comp}, ensure_ascii=False) + "\n")
        if dump_fh is not None:
            dump_fh.close()
    else:
        raise SystemExit("provide --pred-file or --model")

    missing = [s for s in ids if s not in plan_of]
    for s in missing:  # unparseable/absent -> safest legal plan
        plan_of[s] = ("gate", "finish")
        if sampled_mode:
            samples_of[s] = [("gate", "finish")]
    # majority-vote-plan metrics (point metrics use plan_of, which is the
    # majority plan per seed in sampled mode, the single decode otherwise)
    res = score(reward, plan_of, ids)
    report = {"split": args.split, "n": len(ids), "missing_filled_as_gate": len(missing),
              "scores": res}
    if sampled_mode:
        report["decode"] = {"mode": "sampled", "temperature": args.temperature,
                            "n_samples": args.n_samples}
        report["scores_majority_vote"] = res           # alias: `scores` above IS the majority-vote plan
        report["scores_per_sample_avg"] = score_samples(reward, samples_of, ids)
        report["gate_action_presence"] = gate_action_presence_rate(reward, samples_of, ids)
    else:
        report["decode"] = {"mode": "greedy", "temperature": args.temperature,
                            "n_samples": args.n_samples}
    if args.baseline_reward is not None:
        delta = res[0.3]["reward"] - args.baseline_reward
        report["kill_check_lambda0.3"] = {
            "policy_reward": res[0.3]["reward"], "baseline_reward": args.baseline_reward,
            "delta": round(delta, 4), "gate_recall": res[0.3]["gate_recall"],
            "beats_baseline_by_3pts_and_holds_gate":
                bool(delta >= 0.03 and res[0.3]["gate_recall"] >= 0.99),
        }
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
