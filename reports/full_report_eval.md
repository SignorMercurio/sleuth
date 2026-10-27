# Full Report Output Eval

Complete-report contract regression for SLEUTH Step 8.

- Cases: `6`
- Passed: `6`
- Failed: `0`
- Gate pass: `True`

| Case | Pass | Severity | Timeline | Actions | Visible Han chars |
| --- | --- | --- | ---: | ---: | ---: |
| simple-webshell | True | 高危 | 5 | 8 | 2219 |
| no-current-intrusion | True | 低危 | 4 | 2 | 1747 |
| complex-rce-credential | True | 高危 | 5 | 8 | 2420 |
| multi-host-rce | True | 高危 | 5 | 7 | 2564 |
| bloated-revision | True | 高危 | 5 | 5 | 2644 |
| bloated-revision-reviewed | True | 高危 | 5 | 5 | 2274 |

## Failures

- None.

## Evidence boundary

- Reports and findings are synthetic file-backed fixtures.
- Length bands are broad case-specific regression guards, not runtime writing quotas.
- Naturalness and semantic repetition still require blind human review.
