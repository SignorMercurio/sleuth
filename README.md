# SLEUTH

An agent skill for security incident response in Claude Code and Codex. It runs read-only forensic commands on compromised hosts through the SIREN MCP server, reconstructs attack chains, and delivers verified findings mapped to MITRE ATT&CK. Formal incident reports are generated only after the user explicitly requests or confirms one.

Investigation outputs and optional reports are generated in Simplified Chinese by design (the skill targets Chinese-speaking SOC teams); this README is in English for discoverability.

## Features

- **Two investigation modes**: alarm-, asset-, or instance-scoped investigation, plus free-form host triage
- **Capability preflight**: checks which host, cloud, sub-agent, and web evidence sources are available before investigation; missing coverage sets an upper bound on conclusion confidence
- **Per-alarm-type investigation playbooks** (webshell, miner, reverse shell, brute force, ransomware, …) + **cross-cutting tradecraft guides** (log analysis, reverse reasoning, cloud forensics, threat intel, …) + specialized guides (cloud-log routing, OOB/DNSLog, IIS upload tracing) + **MITRE ATT&CK mapping**. See `skills/sleuth/references/playbook_index.md` for the routing table
- **Parallel command orchestration**: independent remote commands are dispatched in a single round to cut investigation time
- **Question-driven evidence loop**: after a bounded baseline, each follow-up must answer a named question that can change classification, scope, or response; branches stop when they add no decision-relevant evidence
- **Strictly read-only**: runs only commands that don't change system state (read files, list processes/network/services, inspect logs), never destructive or install commands; evidence integrity is preserved
- **Adversarial verification gate**: every load-bearing claim is independently refuted before delivery (sub-agent or inline) to guard against false attribution
- **Evidence-gated vulnerability attribution**: CVEs are investigated only when evidence points to vulnerability exploitation; credential abuse, exposed configuration, and other non-vulnerability entry paths are reported as such instead of being forced into a CVE
- **Report confirmation gate**: investigations stop after verified findings by default; a formal `IR-....md` report is created only when the user explicitly requests or confirms it
- **Isolated report writer**: after report confirmation, a fresh writer sees only the verified findings, template, and writing rules when sub-agents are available; it cannot access SIREN or the investigation transcript, and both writer and orchestrator run the same pre-delivery QA
- **Context-isolation sub-agents**: heavy log / SLS / full-disk output is dredged by a sub-agent (or inline) that returns only conclusions, keeping the orchestrator's context lean
- **Multi-host engagements**: hosts are investigated one by one (SIREN works per client), each landing a verified `*.findings.md` worksheet; if the user confirms a report, the findings are merged into one report (see *Multi-host and merge* below)
- **Optional Markdown incident report**: after user confirmation, the engagement writes one named `IR-....md` from the bundled Dossier-style template, using the findings worksheets as the only source of facts
- **Human writing style**: report prose follows `skills/sleuth/references/report_style.md` and bundled, sanitized IR excerpts; corpus rules live in `skills/sleuth/assets/style/README.md`

## Prerequisites

- **Claude Code or Codex**: latest stable. The installable skill follows the open agent skills format under `skills/sleuth/` (`SKILL.md` with optional `references/`, `assets/`, and `agents/openai.yaml` metadata).
- **SIREN MCP server**: the skill depends on SIREN list-client and remote-run tools, usually exposed as `mcp__siren__ls` and `mcp__siren__run`. Configure SIREN as an MCP server in the client you use before running the skill.
- **`$sas` skill**: required for alarm-driven lookup.
- **Optional `sls` skill**: the first choice for WAF / SAS / ActionTrail cloud-log cross-validation.
- **Optional `opencli-aliyun-ir` skill**: used after direct `sas` / `sls` for Alibaba Cloud control-plane state, dedicated adapters, internal consoles, cross-product correlation, and explicit coverage gaps.

## Install

### Codex: user-scope install

Codex discovers user skills from `$HOME/.agents/skills`. Install from GitHub with the `skills` CLI:

```bash
npx skills add SignorMercurio/sleuth -y -g -a codex
```

For active development, symlink this checkout instead of cloning a second copy:

```bash
mkdir -p ~/.agents/skills
ln -s /path/to/sleuth/skills/sleuth ~/.agents/skills/sleuth
```

Codex also scans repository-scoped skills under `.agents/skills` from the current working directory up to the repo root.

### Claude Code: `npx skills`

Uses the community CLI [vercel-labs/skills](https://github.com/vercel-labs/skills):

```bash
npx skills add SignorMercurio/sleuth -a claude-code
```

### Manual copy or rsync

For Claude Code, copy to `~/.claude/skills/sleuth`. For Codex, copy to `~/.agents/skills/sleuth` or a repo-scoped `.agents/skills/sleuth`.

```bash
# Codex
rsync -avz ./sleuth/skills/sleuth/ \
  <host>:~/.agents/skills/sleuth/

# Claude Code
rsync -avz ./sleuth/skills/sleuth/ \
  <host>:~/.claude/skills/sleuth/
```

After install, run `/skills` in Claude Code or mention `$sleuth` / use the skills selector in Codex to confirm the skill is loaded. It activates automatically when the context matches and can also be invoked explicitly.

## Usage

### Alarm-driven mode

Provide:
- Aliyun tenant **UID**
- One SAS lookup selector:
  - Numeric alarm **`Id`** returned by a SAS alarm list
  - Security Center **asset UUID**
  - ECS **instance ID**
- SIREN **Client ID** (if omitted, the skill lists available clients for you to pick)

The skill passes the UID and supplied selector to `$sas`, obtains the relevant alarm context, and runs the matching playbook end to end.

Asset UUID and ECS instance selectors return an alarm list. SLEUTH uses the returned alarm set as a whole, continues pagination as needed for the requested scope, and looks up individual alarm details by their numeric `Id` only when they are needed to support the investigation. Multiple alarms do not require choosing a single primary alarm. If a report is confirmed, they still produce one incident report; list-scoped report filenames omit `event_id`.

### Free-form mode

When there is no alarm, asset, or instance selector, provide the Client ID plus a short description of the anomaly (e.g. "process X at 100% CPU", "suspicious file at /tmp/x.sh"). The skill starts from broad triage and narrows down from there.

### Multi-host and merge

Name several hosts / Client IDs (or point at an alarm affecting multiple assets) and the skill investigates them sequentially, writes one `*.findings.md` worksheet per host, and returns verified findings without creating a formal report by default. After confirmation, it merges everything into a single report (`IR-{date}-{primary-host}-multiN-{type}.md`). Handing it several existing `IR-*.md` reports and explicitly asking to merge them counts as report confirmation and triggers merge-only mode. The skill skips evidence collection steps 1-6, treats the reports as findings input, runs step 7 verification for any new cross-report claim, then produces one consolidated report.

## Layout

```
.
├── CHANGELOG.md                            # Visible workflow and safety-guardrail changes
├── manifest.json                           # Package metadata: owner, maturity, review cadence, budget tier
├── requirements.txt                        # Exact Python dependency pins for repository checks
├── skills/
│   └── sleuth/
│       ├── SKILL.md                        # Resident layer: safety rails, mode routing, 8-step skeleton, report gate
│       ├── agents/
│       │   ├── interface.yaml              # Canonical cross-target interface contract
│       │   └── openai.yaml                 # Codex app metadata and SIREN MCP dependency hint
│       ├── assets/
│       │   ├── report.md                   # Markdown report template copied from dossier/report.md
│       │   └── style/                      # Tracked, sanitized writing samples; curated-ir-excerpts.md is preferred
│       └── references/
│           ├── preflight_probe.md          # Pre-flight capability probe: gaps → confidence ceilings
│           ├── workflow_recon.md           # Step 1-2 detail: mode routing, client/host list, first sweep
│           ├── workflow_tracing.md         # Step 3-6 detail: playbook routing, cloud cross-validation, ATT&CK, residual risk
│           ├── workflow_delivery.md        # Step 7-8 detail: verification gate handoff, findings, report generation
│           ├── playbook_index.md           # Step-3 routing table into the guides below
│           ├── invest_*.md                 # Investigation playbooks, one per alarm type
│           ├── tech_*.md                   # Cross-cutting tradecraft guides
│           ├── attack_framework.md         # ATT&CK tactic/technique reference
│           ├── runtime_compat.md           # Cross-client tool mapping, sub-agents, SIREN failure handling
│           ├── report_naming.md            # IR-….md filename format, event_type slugs, multi-host rule
│           ├── findings_spec.md            # Per-host findings worksheet: the investigation→report handoff
│           ├── report_writing_rules.md     # Template block-by-block filling + project-specific constraints
│           ├── report_style.md             # Writing style guide distilled from hand-written articles
│           ├── cloud_log_queries.md        # WAF / SAS / ActionTrail log routing
│           ├── sas_sls_host_telemetry.md   # SAS SLS host telemetry queries (env-specific gotchas)
│           ├── oob_dnslog_investigation.md # dnslog.cn / interact.sh / OOB callbacks
│           ├── ssh_login_attribution_sas.md # SSH login source attribution via SAS telemetry
│           ├── recon_residual.md           # Residual-risk follow-ups after the 6-axis sweep
│           ├── verification_checklist.md   # Adversarial verification gate run before delivery
│           └── aspnet_webshell_upload_tracing.md # ASP.NET webshell upload tracing
├── scripts/
│   ├── validate.py                         # Frontmatter, link, and orphan checks
│   ├── permission_probe.py                 # Runtime trust and read-only guardrail anchors
│   └── gen_trust_report.py                 # Secret, script-surface, dependency, and package-hash evidence
├── evals/
│   ├── output/                             # Synthetic complete-report contract fixtures
│   └── runtime/                            # Mock SIREN, scenarios, transcript compliance, and fault tests
└── reports/                                # Generated trust evidence, scorecards, blind review, and waivers
```

Loading is two-phase. `SKILL.md` is the only resident layer: safety rails, investigation-mode routing, the 8-step skeleton, and the report confirmation gate. Everything else under `skills/sleuth/references/` is loaded on demand. The skill reads the relevant `workflow_*.md` file when a phase starts and loads playbooks, tradecraft guides, and writing rules only when the current alarm or scenario needs them. This keeps the initial context small.

## Optional report output examples

By default, the skill returns a concise verified investigation result and does not create a formal report. After the user explicitly requests or confirms a report, the skill writes one Markdown report into the cwd:

- `IR-20260417-web01-webshell-123456.md`: alarm-driven, alarm `Id` `123456`
- `IR-20260417-web01-webshell.md`: asset- or instance-scoped alarm set
- `IR-20260417-db-prod-rce.md`: free-form mode
- `IR-20260417-web01-multi3-miner-123456.md`: multi-host engagement (3 hosts, primary `web01`)

Each report file is copied from `skills/sleuth/assets/report.md` in this repo and from the same relative path inside the installed skill, then filled for the specific incident.

Event-type slugs (e.g. `webshell`, `rce`, `unknown`) are documented in `skills/sleuth/references/report_naming.md`, the single source of truth for the full table.

## Validation

Install the pinned repository-check dependency, then run the full baseline from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py
python3 scripts/permission_probe.py
python3 scripts/gen_trust_report.py --check
python3 evals/output/validate_full_reports.py
python3 evals/runtime/run_mock_siren_tests.py
git diff --check
```

`scripts/gen_trust_report.py --check` is read-only. If it reports stale evidence after a package, script, dependency, or tracked-file change, run `python3 scripts/gen_trust_report.py` once and commit the refreshed `reports/trust_report.json` and `reports/trust_report.md`.

The complete-report fixtures and mock SIREN suite are contract regressions. They verify report structure, runtime policy, scenario evidence, fault handling, transcript compliance, and concurrency, but they do not prove that an agent reaches the right conclusion. Use the manual drill in `evals/runtime/README.md` for model-behavior review, and keep blind human report review as a separate gate.

## Contributing

Playbooks and tradecraft guides live in `skills/sleuth/references/`, and the report template lives in `skills/sleuth/assets/report.md`. Everything is plain Markdown. PRs adding new attack types or environment-specific tradecraft are welcome. Keep generic command recipes out of the references: the model already knows them, so the guides carry judgment rules, environment-specific gotchas, and concrete attacker indicators instead.

Report-writing rules are layered, one authoritative home per rule: block-local fill rules live in the template's HTML comments, cross-cutting constraints in `skills/sleuth/references/report_writing_rules.md`, and prose style in `skills/sleuth/references/report_style.md`. Put a new rule in its matching layer rather than restating it across files. Template changes (including its comments) should be made in the upstream `dossier` project and then synced into this skill.

After changing report rules, regenerate the affected fixtures under `evals/output/fixtures/full_reports/` through an isolated Step 8 writer, run the validation commands above, and review the Chinese prose manually against the style guide.
