#!/bin/bash
cd ~/postTrain/training-corpus/scripts/rl
PY=~/postTrain/.venv-rl/bin/python
CEVAL=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/citation_real_eval_v1
M15=Qwen/Qwen2.5-1.5B-Instruct
echo "##### R3fix citation: prompted baseline $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --eval-only --eval-dir $CEVAL --model $M15 --split test \
  --out runs/citation_prompted15_test_eval.json 2>&1 | tail -8
echo "##### R3fix citation: GRPO train $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --eval-dir $CEVAL --model $M15 \
  --out-dir runs/grpo_citation15 --seed 0 --save-steps 50 2>&1 | tail -6
R3=$(ls -td runs/grpo_citation15/[0-9]*/ | head -1)
echo "##### R3fix citation: GRPO eval ($R3) $(date -u +%H:%M:%SZ) #####"
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --eval-only --eval-dir $CEVAL --model $M15 \
  --adapter ${R3}adapter --split test --out ${R3}citation_grpo_test_eval.json 2>&1 | tail -8
echo NIGHT3_COMPLETE
