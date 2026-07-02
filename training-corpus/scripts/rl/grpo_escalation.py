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
from pathlib import Path

from reward_escalation import EscalationReward, render_prompt


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=0.3)
    ap.add_argument("--init-adapter", type=Path, default=None,
                    help="optional SFT adapter to warm-start from")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--split", default="train", choices=["train", "dev", "all"])
    ap.add_argument("--num-generations", type=int, default=8)  # K
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import GRPOConfig, GRPOTrainer

    reward = EscalationReward(args.env_dir, lam=args.lam)
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

    def reward_fn(completions, seed_id, **_):
        # TRL passes dataset columns (seed_id) aligned with completions
        return [reward.completion_reward(sid, c) for c, sid in zip(completions, seed_id)]

    cfg = GRPOConfig(
        output_dir=str(args.out_dir), learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        num_generations=args.num_generations, max_completion_length=48,
        max_steps=args.steps, logging_steps=10, save_strategy="steps",
        save_steps=args.steps, bf16=True, report_to=[],
    )
    trainer = GRPOTrainer(
        model=model, args=cfg, train_dataset=prompts,
        reward_funcs=reward_fn, processing_class=tok,
        peft_config=peft_cfg,
    )
    result = trainer.train()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.out_dir / "adapter"))
    (args.out_dir / "metrics.json").write_text(json.dumps({
        "model": args.model, "lambda": args.lam, "K": args.num_generations,
        "steps": args.steps, "init_adapter": str(args.init_adapter) if args.init_adapter else None,
        "final_loss": getattr(result, "training_loss", None),
    }, indent=1))
    print(json.dumps({"status": "grpo_done", "adapter": str(args.out_dir / "adapter")}, indent=1))


if __name__ == "__main__":
    main()
