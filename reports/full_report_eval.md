# Full Report Output Eval

Complete-report contract regression for SLEUTH Step 8.

- Cases: `4`
- Passed: `4`
- Failed: `0`
- Gate pass: `True`

| Case | Pass | Severity | Timeline | Actions | Visible Han chars |
| --- | --- | --- | ---: | ---: | ---: |
| simple-webshell | True | 高危 | 5 | 6 | 2260 |
| no-current-intrusion | True | 低危 | 4 | 2 | 1804 |
| complex-rce-credential | True | 高危 | 5 | 8 | 2750 |
| multi-host-rce | True | 高危 | 5 | 8 | 3207 |

## Failures

- None.

## Evidence boundary

- Reports and findings are synthetic file-backed fixtures.
- Length bands are broad case-specific regression guards, not runtime writing quotas.
- Naturalness and semantic repetition still require blind human review.
