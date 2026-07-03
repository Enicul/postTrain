#!/bin/bash
cd ~/postTrain/training-corpus/scripts/rl
PY=~/postTrain/.venv-rl/bin/python
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
SFT15=runs/sft_qwen15/20260703T1506Z-e571324/adapter
M15=Qwen/Qwen2.5-1.5B-Instruct

echo "##### R1 GRPO-v2 1.5B gate-oversample x4 $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY grpo_escalation.py --model $M15 --env-dir $ENV --lambda 0.3 \
  --init-adapter $SFT15 --gate-oversample 4 --out-dir runs/grpo_v2_qwen15 --seed 0 \
  --save-steps 50 --parent-run 20260703T1520Z-e571324 2>&1 | tail -6
R1=$(ls -td runs/grpo_v2_qwen15/[0-9]*/ | head -1)
CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M15 \
  --adapter ${R1}adapter --seed 0 --baseline-reward 0.7495 \
  --dump-preds ${R1}test_preds.jsonl --out ${R1}grpo_v2_test_eval.json 2>&1 | tail -16
echo "##### R1 done #####"

echo "##### R2 DPO 1.5B $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY dpo_escalation.py --model $M15 --env-dir $ENV --lambda 0.3 \
  --init-adapter $SFT15 --beta 0.1 --epochs 3 --out-dir runs/dpo_qwen15 --seed 0 \
  --pairs-out runs/dpo_qwen15_pairs.jsonl 2>&1 | tail -6
R2=$(ls -td runs/dpo_qwen15/[0-9]*/ | head -1)
CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M15 \
  --adapter ${R2}adapter --seed 0 --baseline-reward 0.7495 \
  --dump-preds ${R2}test_preds.jsonl --out ${R2}dpo_test_eval.json 2>&1 | tail -16
echo "##### R2 done #####"

echo "##### R3 citation env: prompted baseline then GRPO $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --eval-only --model $M15 --split test \
  --out runs/citation_prompted15_test_eval.json 2>&1 | tail -8
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --model $M15 --out-dir runs/grpo_citation15 \
  --seed 0 --save-steps 50 2>&1 | tail -6
R3=$(ls -td runs/grpo_citation15/[0-9]*/ | head -1)
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --eval-only --model $M15 --adapter ${R3}adapter \
  --split test --out ${R3}citation_grpo_test_eval.json 2>&1 | tail -8
echo "##### R3 done #####"

echo "##### R4 0.5B collapse-prevention ablation: oversample x4 + kl-beta 0.2 $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY grpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV \
  --lambda 0.3 --init-adapter runs/sft_qwen05/20260703T1505Z-e571324/adapter \
  --gate-oversample 4 --kl-beta 0.2 --out-dir runs/grpo_v2_qwen05 --seed 0 \
  --save-steps 50 --parent-run 20260703T1507Z-e571324 2>&1 | tail -6
R4=$(ls -td runs/grpo_v2_qwen05/[0-9]*/ | head -1)
CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test \
  --model Qwen/Qwen2.5-0.5B-Instruct --adapter ${R4}adapter --seed 0 --baseline-reward 0.6061 \
  --dump-preds ${R4}test_preds.jsonl --out ${R4}grpo_v2_test_eval.json 2>&1 | tail -16
echo "##### R4 done #####"
echo NIGHT_BATCH_COMPLETE
