# Output Quality Scorecard

This v0 scorecard compares static without-skill and with-skill outputs using assertion grading.

- Cases: `5`
- Baseline pass rate: `22.33`
- With-skill pass rate: `100.0`
- Delta: `77.67`
- Regressions: `0`
- Blind A/B pairs: `5`
- Gate pass: `True`

Blind review artifacts are generated separately so reviewers can inspect A/B outputs without seeing the answer key.
Run output review adjudication after reviewer decisions are recorded; pending cases should stay pending rather than being counted as human agreement.

## Case Results

| Case | Baseline | With Skill | Delta | Winner | Failed With-Skill Assertions |
| --- | ---: | ---: | ---: | --- | --- |
| overview-from-findings | 0.0 | 100.0 | 100.0 | with_skill | None |
| response-actions | 25.0 | 100.0 | 75.0 | with_skill | None |
| single-atime-claim | 33.33 | 100.0 | 66.67 | with_skill | None |
| attack-mapping-evidence | 33.33 | 100.0 | 66.67 | with_skill | None |
| cloud-evidence-coverage | 20.0 | 100.0 | 80.0 | with_skill | None |

## Failure Taxonomy

- No with-skill assertion failures.

## Next Fixes

- Add holdout cases before using this as a release gate.
- Promote repeated failed assertions into the output-risk profile.
- Keep assertions tied to material deliverables, not phrasing trivia.
