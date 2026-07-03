#!/bin/bash
cd ~/postTrain/training-corpus/scripts/rl
PY=~/postTrain/.venv-rl/bin/python
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
declare -A SFT_ADAPTER=( [05]="runs/sft_qwen05/20260703T1505Z-e571324/adapter" [15]="runs/sft_qwen15/20260703T1506Z-e571324/adapter" )
declare -A BASELINE=( [05]="0.6061" [15]="0.7495" )
declare -A MODEL=( [05]="Qwen/Qwen2.5-0.5B-Instruct" [15]="Qwen/Qwen2.5-1.5B-Instruct" )
for TAG in 05 15; do
  echo "=== A3 GRPO ${MODEL[$TAG]} start $(date -u +%H:%M:%SZ) ==="
  CUDA_VISIBLE_DEVICES=0 $PY grpo_escalation.py --model ${MODEL[$TAG]} --env-dir $ENV \
    --lambda 0.3 --init-adapter ${SFT_ADAPTER[$TAG]} \
    --out-dir runs/grpo_qwen${TAG} --seed 0 --save-steps 50 2>&1 | tail -10
  RUN=$(ls -td runs/grpo_qwen${TAG}/*/ | head -1)
  echo "=== A3 eval ${TAG} adapter: $RUN (baseline ${BASELINE[$TAG]}) ==="
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test \
    --model ${MODEL[$TAG]} --adapter ${RUN}adapter --seed 0 \
    --baseline-reward ${BASELINE[$TAG]} --out ${RUN}grpo_test_eval.json 2>&1 | tail -20
  echo "=== done ${TAG} ==="
done
echo A3_BATCH_COMPLETE
