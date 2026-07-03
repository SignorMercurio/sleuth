# Output Quality Scorecard

This v0 scorecard compares static without-skill and with-skill outputs using assertion grading.

- Cases: `5`
- Baseline pass rate: `0.0`
- With-skill pass rate: `100.0`
- Delta: `100.0`
- Regressions: `0`
- Blind A/B pairs: `5`
- Gate pass: `True`

Blind review artifacts are generated separately so reviewers can inspect A/B outputs without seeing the answer key.
Run output review adjudication after reviewer decisions are recorded; pending cases should stay pending rather than being counted as human agreement.

## Case Results

| Case | Baseline | With Skill | Delta | Winner | Failed With-Skill Assertions |
| --- | ---: | ---: | ---: | --- | --- |
| overview-from-findings | 0.0 | 100.0 | 100.0 | with_skill | None |
| response-actions | 0.0 | 100.0 | 100.0 | with_skill | None |
| single-atime-claim | 0.0 | 100.0 | 100.0 | with_skill | None |
| attack-mapping-evidence | 0.0 | 100.0 | 100.0 | with_skill | None |
| cloud-evidence-coverage | 0.0 | 100.0 | 100.0 | with_skill | None |

## Failure Taxonomy

- No with-skill assertion failures.

## Real model-executed cross-check

The `100.0` delta above is a **static fixture** comparison: the baseline is a hand-written
straw man. On 2026-07-03 one case (`overview-from-findings`) was re-run with **real
claude-fable-5 sub-agent output** for both variants — baseline given no skill material,
with-skill given the writing rules. Evidence: `reports/output_execution_runs.json`,
snapshots under `evals/output/fixtures/overview-from-findings.*.model.md`.

Honest result: **baseline 80 / with-skill 80 / delta 0** — both fail only
`use-defanged-protocol`. Two things this exposes:

1. A real model baseline scores 80, not the fixture's 0. The static delta is inflated;
   treat it as reproducibility evidence, not a measure of skill effect.
2. `use-defanged-protocol` (requires `hxxp`) is fixture-shaped: this findings has an
   IP-form IoC, not a URL, so neither variant writes `hxxp`. Meanwhile the with-skill
   output *did* defang the IP to `203.0.113[.]45` while the baseline left it raw — a real
   skill increment that **no current assertion rewards**.

Caveat on the generated `output_execution_runs.md`: its `duration_ms` (~21ms) and token
counts reflect the replay harness, not the live ~13s generation; tokens are the sub-agent
totals, marked estimated. The `output_sha256` values are the authoritative artifact.

## Next Fixes

- Add a `no-raw-attacker-ip` assertion (and relax `use-defanged-protocol` to accept IP *or*
  URL defang) so the eval rewards the IP-defang increment the model-run surfaced; regenerate
  the blind pack and answer key after.
- Swap the straw-man baselines for held-out real baselines so the delta reflects skill effect.
- Add holdout cases before using this as a release gate.
- Keep assertions tied to material deliverables, not phrasing trivia.
