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
Adjudication is complete: reviewer `mercury`, 5/5 agreement (`reports/output_review_adjudication.json`). These are static-fixture pairs, so 5/5 confirms the harness rather than real-holdout skill strength; the reviewer also flagged a wordiness/meta-clause issue now captured in `references/report_style.md`.

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

The first pass scored **baseline 80 / with-skill 80 / delta 0** — both failing only the
fixture-shaped `use-defanged-protocol` (requires `hxxp`), which this IP-form findings never
produces, while the real skill increment (defanging the IP to `203.0.113[.]45` vs the
baseline's raw `203.0.113.45`) went unrewarded by any assertion. That exposed a rubric gap,
not a skill gap.

Fixed in a **separate** case (`overview-from-findings-modelrun`, def in
`evals/output/model_run_case.jsonl`) so the blind-pack rubric and the closed adjudication
stay untouched: dropped `use-defanged-protocol` (URL-shaped, N/A to an IP IoC) and added
`no-raw-attacker-ip` (forbids the raw dotted IP; the `[.]` defang passes because
`run_output_eval.normalize` preserves punctuation). Re-run result:

- **baseline 80 / with-skill 100 / delta +20**, both model-executed (claude-fable-5).
- baseline fails only `no-raw-attacker-ip` (writes the raw IP); with-skill passes all five.
- This is the first delta that reflects a real skill effect rather than a straw-man gap.

Caveat on the generated `output_execution_runs.md`: its `duration_ms` (~20ms) and token
counts reflect the replay harness, not the live ~13s generation; tokens are the sub-agent
totals, marked estimated. The `output_sha256` values are the authoritative artifact.
Reproduce via skill-creator's `run_output_execution.py` (external harness, like every
sleuth eval) — the in-repo `model_run_runner.py` only replays the graded text.

## Next Fixes

- Port `no-raw-attacker-ip` into the main `cases.jsonl` rubric and regenerate the blind pack
  + answer key (deferred: it invalidates the closed adjudication, so batch it with the next
  blind review round).
- Swap the straw-man baselines for held-out real baselines so the static delta reflects skill
  effect the way the model-run delta now does.
- Add holdout cases before using this as a release gate.
- Keep assertions tied to material deliverables, not phrasing trivia.
