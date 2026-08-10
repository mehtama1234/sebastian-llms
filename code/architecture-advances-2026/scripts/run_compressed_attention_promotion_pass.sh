#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$ROOT_DIR/scripts/run_long_context_variant_plan.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_long_context_variant_execute.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_training_followup.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_training_diagnosis.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_training_stress_followup.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_training_stress_assessment.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_speed_tail_assessment.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_promotion_benchmark_matrix.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_promotion_assessment.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_promotion_memo.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_remediation_plan.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_remediation_execute.sh" >/dev/null
bash "$ROOT_DIR/scripts/run_compressed_attention_promotion_validate.sh"
