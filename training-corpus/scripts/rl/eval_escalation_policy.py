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
from pathlib import Path

from reward_escalation import EscalationReward, parse_plan, render_prompt

LAMBDAS = [0.1, 0.3, 0.6]


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
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    reward = EscalationReward(args.env_dir, lam=0.3)
    ids = [sid for sid, s in reward.env.seeds.items()
           if args.split == "all" or s["split"] == args.split]
    plan_of: dict[str, tuple[str, str]] = {}

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
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.model)
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16, device_map="auto")
        if args.adapter:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, str(args.adapter))
        model.eval()
        for sid in ids:
            msgs = [{"role": "user", "content": render_prompt(reward.env.seeds[sid])}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            enc = tok(text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=48, do_sample=False,
                                     pad_token_id=tok.pad_token_id or tok.eos_token_id)
            comp = tok.decode(gen[0][enc.input_ids.shape[1]:], skip_special_tokens=True)
            plan_of[sid] = parse_plan(comp)
    else:
        raise SystemExit("provide --pred-file or --model")

    missing = [s for s in ids if s not in plan_of]
    for s in missing:  # unparseable/absent -> safest legal plan
        plan_of[s] = ("gate", "finish")
    res = score(reward, plan_of, ids)
    report = {"split": args.split, "n": len(ids), "missing_filled_as_gate": len(missing),
              "scores": res}
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
