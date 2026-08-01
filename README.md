# SLEUTH

An agent skill for security incident response in Claude Code and Codex. It runs read-only forensic commands on compromised hosts through the SIREN MCP server, reconstructs attack chains, and produces incident reports mapped to MITRE ATT&CK.

Reports and supporting materials are generated in Simplified Chinese by design (the skill targets Chinese-speaking SOC teams); this README is in English for discoverability.

## Features

- **Two investigation modes**: alarm-, asset-, or instance-scoped investigation, plus free-form host triage
- **Per-alarm-type investigation playbooks** (webshell, miner, reverse shell, brute force, ransomware, …) + **cross-cutting tradecraft guides** (log analysis, reverse reasoning, cloud forensics, threat intel, …) + specialized guides (cloud-log routing, OOB/DNSLog, IIS upload tracing) + **MITRE ATT&CK mapping**. See `skills/sleuth/references/playbook_index.md` for the routing table
- **Parallel command orchestration**: independent remote commands are dispatched in a single round to cut investigation time
- **Strictly read-only**: runs only commands that don't change system state (read files, list processes/network/services, inspect logs), never destructive or install commands; evidence integrity is preserved
- **Adversarial verification gate**: every load-bearing claim is independently refuted before the report (sub-agent or inline) to guard against false attribution
- **Isolated report writer**: when sub-agents are available, a fresh writer sees only the verified findings, template, and writing rules; it cannot access SIREN or the investigation transcript, and both writer and orchestrator run the same pre-delivery QA
- **Context-isolation sub-agents**: heavy log / SLS / full-disk output is dredged by a sub-agent (or inline) that returns only conclusions, keeping the orchestrator's context lean
- **Multi-host engagements**: hosts are investigated one by one (SIREN works per client), each landing a verified `*.findings.md` worksheet; the deliverable is always a single merged report (see *Multi-host and merge* below)
- **Markdown incident report**: each engagement writes one named `IR-....md` from the bundled Dossier-style template, using the findings worksheets as the only source of facts
- **Human writing style**: report prose follows `skills/sleuth/references/report_style.md` and bundled, sanitized IR excerpts; corpus rules live in `skills/sleuth/assets/style/README.md`

## Prerequisites

- **Claude Code or Codex**: latest stable. The installable skill follows the open agent skills format under `skills/sleuth/` (`SKILL.md` with optional `references/`, `assets/`, and `agents/openai.yaml` metadata).
- **SIREN MCP server**: the skill depends on SIREN list-client and remote-run tools, usually exposed as `mcp__siren__ls` and `mcp__siren__run`. Configure SIREN as an MCP server in the client you use before running the skill.
- **`$sas` skill**: required for alarm-driven lookup.
- **Optional `sls` skill**: used only when cloud-side WAF / SAS / ActionTrail logs are needed for cross-validation.

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

Asset UUID and ECS instance selectors return an alarm list. SLEUTH uses the returned alarm set as a whole, continues pagination as needed for the requested scope, and looks up individual alarm details by their numeric `Id` only when they are needed to support the investigation. Multiple alarms do not require choosing a single primary alarm and still produce one incident report. List-scoped report filenames omit `event_id`.

### Free-form mode

When there is no alarm, asset, or instance selector, provide the Client ID plus a short description of the anomaly (e.g. "process X at 100% CPU", "suspicious file at /tmp/x.sh"). The skill starts from broad triage and narrows down from there.

### Multi-host and merge

Name several hosts / Client IDs (or point at an alarm affecting multiple assets) and the skill investigates them sequentially, writes one `*.findings.md` worksheet per host, and merges everything into a single report (`IR-{date}-{primary-host}-multiN-{type}.md`). Handing it several existing `IR-*.md` reports triggers merge-only mode: no investigation, just one consolidated report.

## Layout

```
.
├── manifest.json                           # Package metadata: owner, maturity, review cadence, budget tier
├── skills/
│   └── sleuth/
│       ├── SKILL.md                        # Skill definition and workflow
│       ├── agents/
│       │   ├── interface.yaml              # Canonical cross-target interface contract
│       │   └── openai.yaml                 # Codex app metadata and SIREN MCP dependency hint
│       ├── assets/
│       │   ├── report.md                   # Markdown report template copied from dossier/report.md
│       │   └── style/                      # Tracked, sanitized writing samples; curated-ir-excerpts.md is preferred
│       └── references/
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
│           ├── verification_checklist.md   # Adversarial verification gate run before the report
│           └── aspnet_webshell_upload_tracing.md # ASP.NET webshell upload tracing
├── scripts/
│   └── validate.py                         # Repo consistency checks (frontmatter, links, orphans; run in CI)
├── evals/                                  # Trigger evals plus synthetic findings and complete-report fixtures
└── reports/                                # Generated evidence: complete-report gate, scorecards, blind review, waivers
```

Files under `skills/sleuth/references/` are loaded on demand. The skill reads only the entries relevant to the current alarm or scenario, keeping the context window from being flooded on the first turn.

## Output examples

The skill writes a Markdown report into the cwd:

- `IR-20260417-web01-webshell-123456.md`: alarm-driven, alarm `Id` `123456`
- `IR-20260417-web01-webshell.md`: asset- or instance-scoped alarm set
- `IR-20260417-db-prod-rce.md`: free-form mode
- `IR-20260417-web01-multi3-miner-123456.md`: multi-host engagement (3 hosts, primary `web01`)

Each report file is copied from `skills/sleuth/assets/report.md` in this repo and from the same relative path inside the installed skill, then filled for the specific incident.

Event-type slugs (e.g. `webshell`, `rce`, `unknown`) are documented in `skills/sleuth/references/report_naming.md`, the single source of truth for the full table.

## Validation

Run the repository consistency check and complete-report regression from the repository root:

```bash
python3 scripts/validate.py
python3 evals/output/validate_full_reports.py
git diff --check
```

`scripts/validate.py` requires PyYAML. The complete-report fixtures are synthetic forward tests: they verify structure, severity, action status, IoC display, internal-language leakage, repetition, and broad length bands. They do not replace blind human review or prove improvement against a no-skill baseline.

## Contributing

Playbooks and tradecraft guides live in `skills/sleuth/references/`, and the report template lives in `skills/sleuth/assets/report.md`. Everything is plain Markdown. PRs adding new attack types or environment-specific tradecraft are welcome. Keep generic command recipes out of the references: the model already knows them, so the guides carry judgment rules, environment-specific gotchas, and concrete attacker indicators instead.

Report-writing rules are layered, one authoritative home per rule: block-local fill rules live in the template's HTML comments, cross-cutting constraints in `skills/sleuth/references/report_writing_rules.md`, and prose style in `skills/sleuth/references/report_style.md`. Put a new rule in its matching layer rather than restating it across files. Template changes (including its comments) should be made in the upstream `dossier` project and then synced into this skill.

After changing report rules, regenerate the affected fixtures under `evals/output/fixtures/full_reports/` through an isolated Step 8 writer, run the validation commands above, and review the Chinese prose manually against the style guide.
