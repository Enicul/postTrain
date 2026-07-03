#!/bin/bash
cd ~/postTrain/training-corpus/scripts/rl
PY=../../../.venv-rl/bin/python
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
mkdir -p runs/a1_prompted
echo "{\"purpose\":\"A1 motivation gate - prompted base models, no training\",\"git_sha\":\"$(git -C ~/postTrain rev-parse --short HEAD)\",\"started_utc\":\"$(date -u +%Y%m%dT%H%M%SZ)\",\"gpu\":\"$(CUDA_VISIBLE_DEVICES=0 nvidia-smi --query-gpu=name --format=csv,noheader -i 0)\",\"split\":\"test\",\"seed\":0}" > runs/a1_prompted/a1_manifest.json
for SIZE in 0.5B 1.5B 3B 7B; do
  TAG=$(echo $SIZE | tr -d .B | tr "[:upper:]" "[:lower:]")
  echo "=== A1 Qwen2.5-${SIZE}-Instruct $(date -u +%H:%M:%SZ) ==="
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test \
    --model Qwen/Qwen2.5-${SIZE}-Instruct --seed 0 \
    --out runs/a1_prompted/qwen${TAG}_test_eval.json 2>&1 | tail -15
  echo "=== done ${SIZE}, exit $? ==="
done
echo A1_BATCH_COMPLETE
