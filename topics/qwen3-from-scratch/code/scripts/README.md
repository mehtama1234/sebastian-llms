# Scripts

Place reproducible entrypoints here for:

- reference model inspection
- scratch model smoke tests
- weight loading
- parity evaluation

These scripts assume the environment is already prepared, for example:

```bash
cd /home/manishmehta/ui-projects/sebastian-llms/code/qwen3-parity
. .venv/bin/activate
```

Or, for a torch-enabled fallback environment:

```bash
source /home/manishmehta/projects/physical-ai-lab/.venv/bin/activate
```

Current script:

- `run_reference_inspect.sh`
- `run_scratch_config_snapshot.sh`
- `compare_config_snapshots.sh`
- `run_weight_mapping_snapshot.sh`
- `run_weight_manifest.sh`
- `run_tiny_smoke.sh`
- `run_real_subset_probe.sh`
- `run_layer0_forward_parity.sh`
- `run_prefix_logits_parity.sh`
- `run_full_prompt_set_parity.sh`
