# SLEUTH

English | [中文](README.zh-CN.md)

An agent skill for security incident response in Claude Code and Codex. It runs read-only forensic commands on compromised hosts through the SIREN MCP server, reconstructs attack chains, and delivers verified findings mapped to MITRE ATT&CK. Formal incident reports are written from the verified findings by the companion `dossier` skill, only when the user explicitly asks for one.

Investigation outputs are generated in Simplified Chinese by design (the skill targets Chinese-speaking SOC teams); this README is in English for discoverability.

## Features

- **Investigation modes**: alarm-, asset-, or instance-scoped investigation, free-form host triage, and cloud-side investigation (AccessKey/STS abuse, anomalous ActionTrail calls, WAF attack entry, SAS alarm triage) that needs no SIREN client; a verification mode checks the conclusions of an existing report or findings
- **Capability preflight**: checks which host, cloud, sub-agent, and web evidence sources are available before investigation; missing coverage constrains the specific claims that depend on it
- **Per-alarm-type investigation playbooks** (webshell, miner, reverse shell, brute force, ransomware, RCE, SQL injection, abnormal login, data exfiltration, persistence, privilege escalation) + **cross-cutting tradecraft guides** (log analysis and reverse reasoning, cloud forensics, process/file analysis, attack countermeasures) + specialized guides (cloud-log routing, SAS/SLS host telemetry, OOB/DNSLog, SSH login attribution) + **MITRE ATT&CK mapping**. Playbooks, ASP.NET upload tracing, and the tradecraft routing table live in `skills/sleuth/references/playbooks.md`
- **Parallel command orchestration**: independent remote commands are dispatched in a single round to cut investigation time
- **Question-driven evidence loop**: after a bounded baseline, each follow-up must answer a named question that can change classification, scope, or response; branches stop when they add no decision-relevant evidence
- **Strictly read-only**: runs only commands that don't change system state (read files, list processes/network/services, inspect logs), never destructive or install commands; evidence integrity is preserved
- **Adversarial verification gate**: every load-bearing claim is independently refuted before delivery (sub-agent or inline) to guard against false attribution
- **Evidence-gated vulnerability attribution**: CVEs are investigated only when evidence points to vulnerability exploitation; credential abuse, exposed configuration, and other non-vulnerability entry paths are reported as such instead of being forced into a CVE
- **Continuous investigation**: the skill works a checklist and does not end its turn while an item is actionable; a blocked item is parked and the rest continue. SIREN AIR keeps the checklist and current verdict on the Case Board; other runtimes keep them in the findings worksheet, so progress can be read before the session ends
- **Report handoff**: investigations stop after verified findings; the formal `IR-....md` report is written by the companion `dossier` skill (`skills/dossier/` in the sibling `dossier` repository) from the findings worksheets, only when the user explicitly asks for it
- **Isolated conclusion writer**: when sub-agents are available, the Step 7 conclusion is drafted by a fresh writer that sees only the verified findings, and the orchestrator only passes or rejects it, sending a passed draft verbatim. The writer cannot access SIREN or the investigation transcript
- **Context-isolation sub-agents**: large outputs are narrowed by a sub-agent (or inline), returning decisive evidence with scope and truncation metadata, keeping the orchestrator's context lean
- **Multi-host engagements**: authorized hosts receive minimal volatile-evidence snapshots first, followed by per-host investigation; each worksheet is updated throughout and verified before delivery; the `dossier` skill merges them into one report on request (see *Multi-host and merge* below)
- **Console screenshots as evidence**: verified cloud-side facts can carry console screenshots captured read-only through `opencli-aliyun-ir`, recorded in the findings and referenced from the report

## Prerequisites

- **Claude Code or Codex**: latest stable. The installable skill follows the open agent skills format under `skills/sleuth/` (`SKILL.md` with `references/` and `agents/` metadata).
- **dossier skill** (for formal reports): install the `dossier` skill from the sibling `dossier` repository in the same skills directory. It writes, merges, revises, and reviews `IR-….md` reports from sleuth's findings and reads `skills/sleuth/references/findings_spec.md` from the sleuth package installed beside it.
- **SIREN MCP server**: host investigation depends on SIREN list-client and remote-run tools (cloud-side investigation runs without them), usually exposed as `mcp__siren__ls` and `mcp__siren__run`. Configure SIREN as an MCP server in the client you use before running the skill.
- **`$sas` skill**: required for alarm-driven lookup.
- **Optional `sls` skill**: the first choice for WAF / SAS / ActionTrail cloud-log cross-validation.
- **Optional `aliyun` CLI**: used for single read-only control-plane lookups when a SIREN AIR Project has AccessKeys.
- **Optional `opencli-aliyun-ir` skill**: used after direct `sas` / `sls` for Alibaba Cloud control-plane state without AccessKeys, dedicated adapters, internal consoles, cross-product correlation, and explicit coverage gaps.

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

Asset UUID and ECS instance selectors return an alarm list. SLEUTH uses the returned alarm set as a whole, continues pagination as needed for the requested scope, and looks up individual alarm details by their numeric `Id` only when they are needed to support the investigation. Multiple alarms do not require choosing a single primary alarm. They still produce one findings set; list-scoped findings filenames omit `event_id`.

### Free-form mode

When there is no alarm, asset, or instance selector, provide the Client ID plus a short description of the anomaly (e.g. "process X at 100% CPU", "suspicious file at /tmp/x.sh"). The skill starts from broad triage and narrows down from there.

### Multi-host and merge

Name several hosts / Client IDs (or point at an alarm affecting multiple assets) and the skill captures a minimal snapshot on each authorized host before investigating in depth. It maintains one `*.findings.md` worksheet per Client, preserves separate reruns, and returns verified findings. Merging the worksheets into one report (`IR-{date}-{primary-host}-multiN-{type}.md`), and merging several existing `IR-*.md` reports, is the `dossier` skill's job. When a merge raises a new cross-report claim, sleuth's verification mode runs step 7 on it and writes the verdict back into the findings first.

### Reports

Report generation, merging, revision, and review live in the `dossier` skill (`skills/dossier/` in the sibling `dossier` repository, which also owns the report templates and writing rules). Install both skills in the same skills directory: `dossier` reads `skills/sleuth/references/findings_spec.md` from the sleuth package beside it to interpret the findings, and sleuth never reads `dossier`. New evidence or a changed conclusion always goes through sleuth's verification mode first, which writes the verdict into the findings; `dossier` then rewrites the affected chapters.

## Layout

```
.
├── AGENTS.md                               # Agent project instructions (Claude Code / Codex)
├── CHANGELOG.md                            # Visible workflow and safety-guardrail changes
├── manifest.json                           # Package metadata: owner, maturity, review cadence, budget tier
├── requirements.txt                        # Exact Python dependency pins for repository checks
├── docs/
│   ├── agent-guidance/                     # Task-specific guidance for AI agents working on this repo
│   └── sleuth-design-principles.*          # Design principles (HTML + PDF)
├── skills/
│   └── sleuth/
│       ├── SKILL.md                        # Resident layer: safety rails, mode routing, 8-step skeleton, stop rules, delegation and verdicts
│       ├── agents/
│       │   ├── interface.yaml              # Canonical cross-target interface contract
│       │   └── openai.yaml                 # Codex app metadata and SIREN MCP dependency hint
│       └── references/
│           ├── workflow_recon.md           # Step 1-2: capabilities, mode routing, client/host list, first sweep
│           ├── workflow_tracing.md         # Step 3-6 detail: playbook routing, cloud cross-validation, ATT&CK, residual risk
│           ├── workflow_delivery.md        # Step 7 detail: verification handoff and conclusion-writer isolation
│           ├── playbooks.md                # Step-3 alarm-type playbooks and tradecraft routing table
│           ├── tech_*.md                   # 4 cross-cutting tradecraft guides
│           ├── runtime_compat.md           # Cross-client tool mapping, sub-agents, context budget, SIREN failures
│           ├── findings_spec.md            # Per-host findings worksheet: naming, slugs, structure; read by dossier
│           ├── cloud_log_queries.md        # WAF / SAS / ActionTrail log routing
│           ├── sas_sls_host_telemetry.md   # SAS host telemetry: field gotchas, w3wp.exe, SSH attribution, OOB/DNSLog
│           ├── recon_residual.md           # Residual-risk follow-ups after the 6-axis sweep
│           └── verification_checklist.md   # Adversarial verification gate run before delivery
├── scripts/
│   ├── validate.py                         # Frontmatter, link, and orphan checks
│   ├── permission_probe.py                 # Runtime trust and read-only guardrail anchors
│   ├── permission_probe_anchors.yaml       # Expected trust anchors for permission_probe.py
│   ├── gen_trust_report.py                 # Secret, script-surface, dependency, and package-hash evidence
│   └── air_session_stats.py                # Round trips, context load, and exec output sizes in Codex AIR rollouts
├── evals/
│   ├── semantic_config.json                # Semantic eval configuration
│   ├── blind_holdout/                      # Blind holdout trigger cases for human review
│   ├── dev/                                # Development trigger cases
│   └── runtime/                            # Mock SIREN, scenarios, transcript compliance, and fault tests
└── reports/                                # Generated trust evidence, scorecards, blind review, and waivers
```

Loading is two-phase. `SKILL.md` is the only resident layer: safety rails, investigation-mode routing, the 8-step skeleton, the report handoff, and the rules each step must follow (the investigation loop and stop conditions, when to delegate, and verdict rules). A model that reads only `SKILL.md` can still run a full investigation. Everything else under `skills/sleuth/references/` holds detail and is loaded on demand. Each step names the `workflow_*.md` file to read when it starts. Playbooks and tradecraft guides load only when the current alarm or scenario needs them. This keeps the initial context small.

## Findings output

The skill returns a concise verified investigation result and keeps one findings worksheet per host in the cwd:

- `IR-20260417-web01-webshell-123456-client7.findings.md`: alarm-driven, alarm `Id` `123456`, SIREN client 7
- `IR-20260417-uid1234567890-akabuse-123456.findings.md`: cloud-side event with no SIREN client

Naming fields and event-type slugs (e.g. `webshell`, `rce`, `unknown`) are documented in `skills/sleuth/references/findings_spec.md`「文件命名」. The `dossier` skill derives the formal report name (`IR-….md`) from the findings name.

## Validation

Install the pinned repository-check dependency, then run the full baseline from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate.py
python3 scripts/permission_probe.py
python3 scripts/gen_trust_report.py --check
python3 evals/runtime/run_mock_siren_tests.py
git diff --check
```

`scripts/gen_trust_report.py --check` is read-only. If it reports stale evidence after a package, script, dependency, or tracked-file change, run `python3 scripts/gen_trust_report.py` once and commit the refreshed `reports/trust_report.json` and `reports/trust_report.md`.

The mock SIREN suite is a contract regression. It verifies runtime policy, scenario evidence, fault handling, transcript compliance, and concurrency, but it does not prove that an agent reaches the right conclusion. Use the [isolated model drill](evals/runtime/README.md) for real model outputs and costs, then apply the semantic review kept in the dossier repository (`evals/output/review.md`). The opt-in runner invokes the configured model service and writes a new explicit directory outside the repository; it is not part of offline CI. Blind human review remains separate.

## Contributing

Playbooks and tradecraft guides live in `skills/sleuth/references/`; everything is plain Markdown. PRs adding new attack types or environment-specific tradecraft are welcome. Keep generic command recipes out of the references: the model already knows them, so the guides carry judgment rules, environment-specific gotchas, and concrete attacker indicators instead.

Report templates, writing rules, and the complete-report fixtures live in the `dossier` repository. The sections of `skills/sleuth/references/findings_spec.md` that the `dossier` writer reads (file naming, content structure, conclusion-delivery rules) are a cross-repository contract: after changing them, run that repository's checks as well.
