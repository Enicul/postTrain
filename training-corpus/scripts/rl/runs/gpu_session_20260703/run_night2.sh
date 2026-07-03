#!/bin/bash
cd ~/postTrain/training-corpus/scripts/rl
PY=~/postTrain/.venv-rl/bin/python
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1

for SIZE in 3B 7B; do
  TAG=$(echo $SIZE | tr -d .B | tr "[:upper:]" "[:lower:]")
  M=Qwen/Qwen2.5-${SIZE}-Instruct
  BS=16; GA=1; [ "$SIZE" = "7B" ] && BS=8 && GA=2
  echo "##### SCALE-SFT ${SIZE} $(date -u +%H:%M:%SZ) #####"
  CUDA_VISIBLE_DEVICES=0 $PY sft_escalation.py --model $M --train sft_train.jsonl \
    --out-dir runs/sft_qwen${TAG} --seed 0 --grad-accum $GA 2>&1 | tail -5
  SFT=$(ls -td runs/sft_qwen${TAG}/[0-9]*/ | head -1)
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M \
    --adapter ${SFT}adapter --seed 0 --dump-preds ${SFT}test_preds.jsonl \
    --out ${SFT}sft_test_eval.json 2>&1 | tail -14
  SFT_REWARD=$($PY -c "import json;print(json.load(open(\"${SFT}sft_test_eval.json\"))[\"scores\"][\"0.3\"][\"reward\"])")
  echo "##### SCALE-GRPO-v2 ${SIZE} (baseline $SFT_REWARD) $(date -u +%H:%M:%SZ) #####"
  CUDA_VISIBLE_DEVICES=0 $PY grpo_escalation.py --model $M --env-dir $ENV --lambda 0.3 \
    --init-adapter ${SFT}adapter --gate-oversample 4 --batch-size $BS --grad-accum $GA \
    --out-dir runs/grpo_v2_qwen${TAG} --seed 0 --save-steps 50 2>&1 | tail -6
  G=$(ls -td runs/grpo_v2_qwen${TAG}/[0-9]*/ | head -1)
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M \
    --adapter ${G}adapter --seed 0 --baseline-reward $SFT_REWARD \
    --dump-preds ${G}test_preds.jsonl --out ${G}grpo_v2_test_eval.json 2>&1 | tail -16
  echo "##### ${SIZE} done #####"
done
echo NIGHT2_COMPLETE
