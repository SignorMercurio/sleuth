# Investigation Contracts

- Keep `skills/sleuth/SKILL.md` concise and imperative.
- Keep victim-host investigation read-only. Split conclusions into confirmed
  and unconfirmed findings, and exclude raw sensitive payloads from reports.
- `evals/semantic_config.json` owns the implicit-routing exclusion markers and
  core workflow semantic markers enforced by `scripts/validate.py`. Update the
  markers with any intentional wording change; do not weaken the underlying
  route, evidence-loop, or CVE-attribution boundary to satisfy the check.
- Delegate alarm-driven lookup to the `sas` skill. Its parameter contract is
  `../log0-utils/.agents/skills/sas/SKILL.md`. When that contract changes, keep
  SLEUTH step 1.2, README usage, report naming, findings handoff, and selector
  evals synchronized. Do not duplicate the CLI contract elsewhere.
- Use direct `sas` first for alarms and direct `sls` for delivered
  WAF/SAS/ActionTrail logs.
- Delegate Alibaba Cloud control-plane, dedicated-adapter, and cross-product
  gaps to the read-only `opencli-aliyun-ir` workflow. Its project-local skill
  and source of truth live in the `clis` repository. SLEUTH owns only scenario
  routing and the findings handoff; do not duplicate OpenCLI adapter contracts.
