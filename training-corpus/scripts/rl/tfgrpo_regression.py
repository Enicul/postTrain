#!/usr/bin/env python3
"""Plan C: no-regression GATE primitive (a GPU-bound scoring pass).

Score one experience library against a FIXED regression set (default: the dev
split, greedy decode) and return mean reward + gate recall. The orchestrator
calls this on the CURRENT library and on a TRIAL library (current + a candidate
lesson); it accepts the lesson only if the trial does not drop reward on the
regression set - the natural-language analogue of GRPO's no-regression check in
`training_free_grpo.run` (`regression_reward(trial) >= before`).

Greedy by default so the gate is a stable, low-variance point measurement (the
same decode the final eval uses). Library injection reuses eval's build_prompt,
so this scores the exact prompt a `--extra-system-file` eval would score.
Loads the model ONCE per call; the round loop makes at most a couple of calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval_escalation_policy import build_prompt
from reward_escalation import EscalationReward, parse_plan
from tfgrpo_rollout import library_block_and_sha, load_library


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--split", default="dev", choices=["dev", "train", "test", "all"],
                    help="the fixed regression set (default: dev)")
    ap.add_argument("--library", type=Path, default=None,
                    help="lessons JSON to score (omit for the no-library baseline)")
    ap.add_argument("--lambda", dest="lam", type=float, default=0.3)
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="0 (default) = greedy; the gate is a point measurement")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--loader", default="causal", choices=["causal", "auto"])
    ap.add_argument("--out", type=Path, required=True, help="write the result json here")
    args = ap.parse_args()

    reward = EscalationReward(args.env_dir, lam=args.lam)
    lib = load_library(args.library)
    block, lib_sha = library_block_and_sha(lib)
    extra_system = block or None
    ids = sorted(sid for sid, s in reward.env.seeds.items()
                 if args.split == "all" or s["split"] == args.split)
    if not ids:
        raise SystemExit(f"no seeds for split={args.split}")

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

    do_sample = args.temperature > 0.0
    tot_r = 0.0
    gn = hit = 0
    for sid in ids:
        seed = reward.env.seeds[sid]
        enc = build_input(build_prompt(seed, extra_system))
        with torch.no_grad():
            kw = {"max_new_tokens": 48,
                  "pad_token_id": tok.pad_token_id or tok.eos_token_id}
            if do_sample:
                gen = model.generate(**enc, do_sample=True,
                                     temperature=args.temperature, **kw)
            else:
                gen = model.generate(**enc, do_sample=False, **kw)
        comp = tok.decode(gen[0][enc.input_ids.shape[1]:], skip_special_tokens=True)
        first, on_fail = parse_plan(comp)
        tot_r += reward.plan_reward(sid, first, on_fail)
        if seed["requires_human_gate"]:
            gn += 1
            if first == "gate":
                hit += 1

    result = {
        "split": args.split, "n": len(ids),
        "lam": args.lam, "temperature": args.temperature,
        "decode": "sampled" if do_sample else "greedy",
        "mean_reward": round(tot_r / len(ids), 4),
        "gate_recall": round(hit / max(1, gn), 4),
        "gate_needed": gn,
        "library_path": str(args.library) if args.library else None,
        "library_sha256": lib_sha, "n_lessons": len(lib.lessons),
        "model": args.model,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
