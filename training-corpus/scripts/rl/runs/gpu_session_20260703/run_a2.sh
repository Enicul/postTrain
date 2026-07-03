#!/bin/bash
set -e
cd ~/postTrain/training-corpus/scripts/rl
PY=~/postTrain/.venv-rl/bin/python
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
$PY build_sft_labels.py --env-dir $ENV --split train --lambda 0.3 --out sft_train.jsonl
echo "labels built: $(wc -l < sft_train.jsonl) rows"
for SIZE in 0.5B 1.5B; do
  TAG=$(echo $SIZE | tr -d .B | tr "[:upper:]" "[:lower:]")
  echo "=== A2 SFT Qwen2.5-${SIZE} start $(date -u +%H:%M:%SZ) ==="
  CUDA_VISIBLE_DEVICES=0 $PY sft_escalation.py --model Qwen/Qwen2.5-${SIZE}-Instruct \
    --train sft_train.jsonl --out-dir runs/sft_qwen${TAG} --seed 0 2>&1 | tail -8
  RUN=$(ls -td runs/sft_qwen${TAG}/*/ | head -1)
  echo "=== A2 eval ${SIZE} adapter: $RUN ==="
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test \
    --model Qwen/Qwen2.5-${SIZE}-Instruct --adapter ${RUN}adapter --seed 0 \
    --out ${RUN}sft_test_eval.json 2>&1 | tail -12
  echo "=== done ${SIZE} ==="
done
echo A2_BATCH_COMPLETE
