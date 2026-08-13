# Full Report Output Eval

Complete-report contract regression for SLEUTH Step 8.

- Cases: `4`
- Passed: `4`
- Failed: `0`
- Gate pass: `True`

| Case | Pass | Severity | Timeline | Actions | Visible Han chars |
| --- | --- | --- | ---: | ---: | ---: |
| simple-webshell | True | 高危 | 5 | 6 | 1674 |
| no-current-intrusion | True | 低危 | 4 | 2 | 1551 |
| complex-rce-credential | True | 高危 | 5 | 7 | 1766 |
| multi-host-rce | True | 高危 | 6 | 7 | 2008 |

## Failures

- None.

## Evidence boundary

- Reports and findings are synthetic file-backed fixtures.
- Length bands are broad case-specific regression guards, not runtime writing quotas.
- Naturalness and semantic repetition still require blind human review.
