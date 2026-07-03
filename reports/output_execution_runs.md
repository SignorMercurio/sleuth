# Output Execution Runs

This report records how output-eval variants were produced and whether timing or token evidence is observed or estimated.

- Cases: `1`
- Variant runs: `2`
- Command executed: `2`
- Model executed: `2`
- Recorded fixtures: `0`
- Timing observed: `2`
- Token observed: `0`
- Token estimated: `2`
- Delta: `0.0`
- Gate pass: `True`

Command runner evidence is present. This proves the eval harness executed an external command, but it is not provider-backed model evidence unless the runner reports model metadata.

## Runs

| Case | Variant | Mode | Model | Duration ms | Tokens | Score | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| overview-from-findings | baseline | model | claude-fable-5 | 20.82 | 22892 | 80.0 | pass |
| overview-from-findings | with_skill | model | claude-fable-5 | 21.64 | 23279 | 80.0 | pass |

## Next Fixes

- Keep recorded fixtures as reproducible baselines, but do not describe them as model-executed evidence.
- Use `scripts/provider_output_eval_runner.py` for provider-backed holdout cases when release confidence depends on real generation behavior.
- Compare timing, token cost, and assertion deltas before promoting a skill to governed reuse.
