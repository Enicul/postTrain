#!/bin/bash
# Batch 4 (Plan) — pull-and-run on the A100 box. Three deliverables:
#   A. multi-seed error bars (the single-seed credibility gap)
#   B. Gemma 4 cross-family PROMPTED eval (separate transformers-5.13 venv)
#   C. citation SFT baseline in the LETTERS action space (the decoupling probe)
#
# Paths are relative to training-corpus/scripts/rl (cd below). Two venvs:
#   PY  = training venv (transformers pinned for Qwen train/eval, TRL, peft)
#   GPY = Gemma venv (transformers 5.13; PROMPTED eval only, no training there)
# Progress markers "##### ..." per phase; BATCH4_COMPLETE at the very end.
set -uo pipefail  # keep going past a failing arm; every run dir is its own evidence
cd ~/postTrain/training-corpus/scripts/rl
PY=~/postTrain/.venv-rl/bin/python
GPY=~/postTrain/.venv-gemma/bin/python
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
CENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/citation_real_eval_v1

M15=Qwen/Qwen2.5-1.5B-Instruct
M3=Qwen/Qwen2.5-3B-Instruct
M05=Qwen/Qwen2.5-0.5B-Instruct

# seed-0 artefacts already on disk (their eval jsons feed the aggregates below):
#   SFT 1.5B : runs/sft_qwen15/20260703T1506Z-e571324
#   GRPO-v2 3B (gate-oversample 4) : runs/grpo_v2_qwen3/20260703T1624Z-e571324
#   GRPO 0.5B plain (collapse) : runs/grpo_qwen05/20260703T1507Z-e571324
# seed-0 SFT adapters reused as GRPO init below (see the design note per arm):
SFT3_S0=runs/sft_qwen3/20260703T1623Z-e571324/adapter    # 3B SFT seed-0 adapter
SFT05_S0=runs/sft_qwen05/20260703T1505Z-e571324/adapter  # 0.5B SFT seed-0 adapter
# per-arm kill-check baselines (seed-0 SFT reward@lambda0.3), for the eval print:
BL3=0.8428    # 3B SFT baseline
BL05=0.6061   # 0.5B SFT baseline

########################################################################
echo "##### PHASE A multi-seed error bars (seeds 1,2; aggregate over 0,1,2) $(date -u +%H:%M:%SZ) #####"
# DESIGN NOTE (pre-registered): to isolate GRPO SAMPLING variance from SFT
# variance, GRPO seeds 1,2 REUSE the existing seed-0 SFT adapters as init rather
# than training a fresh per-seed SFT (which would be too slow and would confound
# the two variance sources). SFT variance is measured SEPARATELY, and only at
# 1.5B, via arm (a): each seed retrains SFT-1.5B from scratch and is evaluated,
# so the sft_qwen15 aggregate reflects true SFT-init variance. The 3B-oracle and
# 0.5B-collapse claims are then multi-seed statements about GRPO sampling, off a
# fixed SFT init.
for SEED in 1 2; do
  echo "##### PHASE A seed $SEED $(date -u +%H:%M:%SZ) #####"

  # (a) SFT 1.5B from scratch (measures SFT-init variance) -> eval
  echo "##### A.a SFT 1.5B seed $SEED #####"
  CUDA_VISIBLE_DEVICES=0 $PY build_sft_labels.py --env-dir $ENV --split train --lambda 0.3 \
    --out /tmp/sft_train.jsonl 2>&1 | tail -3
  CUDA_VISIBLE_DEVICES=0 $PY sft_escalation.py --model $M15 --train /tmp/sft_train.jsonl \
    --out-dir runs/sft_qwen15_seed$SEED --seed $SEED 2>&1 | tail -6
  A=$(ls -td runs/sft_qwen15_seed$SEED/[0-9]*/ | head -1)
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M15 \
    --adapter ${A}adapter --seed $SEED --out ${A}sft_test_eval.json 2>&1 | tail -12

  # (b) GRPO-v2 3B gate-oversample 4, init from the seed-0 3B SFT adapter -> eval
  echo "##### A.b GRPO-v2 3B (oversample 4, init=seed-0 3B SFT) seed $SEED #####"
  CUDA_VISIBLE_DEVICES=0 $PY grpo_escalation.py --model $M3 --env-dir $ENV --lambda 0.3 \
    --init-adapter $SFT3_S0 --gate-oversample 4 --out-dir runs/grpo_v2_qwen3_seed$SEED \
    --seed $SEED --save-steps 50 2>&1 | tail -6
  B=$(ls -td runs/grpo_v2_qwen3_seed$SEED/[0-9]*/ | head -1)
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M3 \
    --adapter ${B}adapter --seed $SEED --baseline-reward $BL3 \
    --dump-preds ${B}test_preds.jsonl --out ${B}grpo_v2_test_eval.json 2>&1 | tail -16

  # (c) GRPO 0.5B plain (no oversample, replicate the collapse), init seed-0 0.5B SFT -> eval
  echo "##### A.c GRPO 0.5B plain (collapse replicate, init=seed-0 0.5B SFT) seed $SEED #####"
  CUDA_VISIBLE_DEVICES=0 $PY grpo_escalation.py --model $M05 --env-dir $ENV --lambda 0.3 \
    --init-adapter $SFT05_S0 --out-dir runs/grpo_qwen05_seed$SEED \
    --seed $SEED --save-steps 50 2>&1 | tail -6
  C=$(ls -td runs/grpo_qwen05_seed$SEED/[0-9]*/ | head -1)
  CUDA_VISIBLE_DEVICES=0 $PY eval_escalation_policy.py --env-dir $ENV --split test --model $M05 \
    --adapter ${C}adapter --seed $SEED --baseline-reward $BL05 \
    --dump-preds ${C}test_preds.jsonl --out ${C}grpo_test_eval.json 2>&1 | tail -16
done

echo "##### PHASE A aggregate over seeds {0,1,2} (CPU, stdlib) $(date -u +%H:%M:%SZ) #####"
mkdir -p runs/agg
# SFT 1.5B: seed-0 fixed path + the two freshly-trained seeds (glob resolves the run dirs)
$PY aggregate_seeds.py --config sft_qwen15 --out runs/agg/sft_qwen15.json \
  runs/sft_qwen15/20260703T1506Z-e571324/sft_test_eval.json \
  runs/sft_qwen15_seed1/[0-9]*/sft_test_eval.json \
  runs/sft_qwen15_seed2/[0-9]*/sft_test_eval.json
# GRPO-v2 3B (the 3B-oracle claim):
$PY aggregate_seeds.py --config grpo_v2_qwen3 --out runs/agg/grpo_v2_qwen3.json \
  runs/grpo_v2_qwen3/20260703T1624Z-e571324/grpo_v2_test_eval.json \
  runs/grpo_v2_qwen3_seed1/[0-9]*/grpo_v2_test_eval.json \
  runs/grpo_v2_qwen3_seed2/[0-9]*/grpo_v2_test_eval.json
# GRPO 0.5B plain (the 0.5B-collapse claim):
$PY aggregate_seeds.py --config grpo_qwen05 --out runs/agg/grpo_qwen05.json \
  runs/grpo_qwen05/20260703T1507Z-e571324/grpo_test_eval.json \
  runs/grpo_qwen05_seed1/[0-9]*/grpo_test_eval.json \
  runs/grpo_qwen05_seed2/[0-9]*/grpo_test_eval.json

########################################################################
echo "##### PHASE B Gemma 4 cross-family PROMPTED eval ($GPY, transformers-5.13) $(date -u +%H:%M:%SZ) #####"
# PROMPTED only (no training on this venv). --loader auto: Gemma 4 is
# Gemma4ForConditionalGeneration, so AutoModelForCausalLM may fail -> fall back
# to AutoModelForImageTextToText. --chat-template wraps the rendered prompt as a
# single user turn (Gemma-it template). Same escalation test split + ruler.
mkdir -p runs/gemma_prompted
E2B=google/gemma-3n-E2B-it   # effective ~2.3B (MatFormer)
E4B=google/gemma-3n-E4B-it   # effective ~4.5B (MatFormer)
CUDA_VISIBLE_DEVICES=0 $GPY eval_escalation_policy.py --env-dir $ENV --split test \
  --model $E2B --loader auto --chat-template --seed 0 \
  --dump-preds runs/gemma_prompted/e2b_test_preds.jsonl \
  --out runs/gemma_prompted/e2b_test_eval.json 2>&1 | tail -16
CUDA_VISIBLE_DEVICES=0 $GPY eval_escalation_policy.py --env-dir $ENV --split test \
  --model $E4B --loader auto --chat-template --seed 0 \
  --dump-preds runs/gemma_prompted/e4b_test_preds.jsonl \
  --out runs/gemma_prompted/e4b_test_eval.json 2>&1 | tail -16

########################################################################
echo "##### PHASE C citation SFT baseline (letters action space, the decoupling probe) $(date -u +%H:%M:%SZ) #####"
# sft_citation.py 1.5B seed 0 -> eval via grpo_citation.py --eval-only letters
CUDA_VISIBLE_DEVICES=0 $PY sft_citation.py --model $M15 --eval-dir $CENV \
  --out-dir runs/sft_citation15 --seed 0 2>&1 | tail -8
SC=$(ls -td runs/sft_citation15/[0-9]*/ | head -1)
CUDA_VISIBLE_DEVICES=0 $PY grpo_citation.py --eval-only --action-space letters --model $M15 \
  --eval-dir $CENV --adapter ${SC}adapter --split test \
  --out ${SC}citation_sft_test_eval.json 2>&1 | tail -8

echo BATCH4_COMPLETE
