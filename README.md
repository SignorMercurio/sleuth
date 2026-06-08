# SLEUTH

An agent skill for security incident response in Claude Code and Codex. It runs read-only forensic commands on compromised hosts through the SIREN MCP server, reconstructs attack chains, and produces incident reports mapped to MITRE ATT&CK.

Part of a family of named security tools: **SIREN** (remote forensic runtime), **TALON** (threat hunting), **SLEUTH** (this skill — incident investigator), **DOSSIER** (report platform).

Reports and supporting materials are generated in Simplified Chinese by design (the skill targets Chinese-speaking SOC teams); this README is in English for discoverability.

## Features

- **Two investigation modes** — alarm-driven (UID + Event ID) or free-form (host anomaly only)
- **12 investigation playbooks** + **6 tradecraft guides** + specialized guides (cloud-log routing, OOB/DNSLog, IIS upload tracing) + **MITRE ATT&CK mapping**
- **Parallel command orchestration** — independent remote commands are dispatched in a single round to cut investigation time
- **Strictly read-only** — runs only commands that don't change system state (read files, list processes/network/services, inspect logs), never destructive or install commands; evidence integrity is preserved
- **Markdown incident report** — each incident writes a named `IR-....md` from the bundled Dossier-style template

## Prerequisites

- **Claude Code or Codex** — latest stable. The skill follows the open agent skills format (`SKILL.md` with optional `references/`, `assets/`, and `agents/openai.yaml` metadata).
- **SIREN MCP server** — the skill depends on SIREN list-client, remote-run, and alarm-detail tools, usually exposed as `mcp__siren__ls`, `mcp__siren__run`, and `mcp__siren__get_alarm_detail`. Configure SIREN as an MCP server in the client you use before running the skill.
- **Optional `sls` skill** — used only when cloud-side WAF / SAS / ActionTrail logs are needed for cross-validation.

## Install

### Codex — user-scope install

Codex discovers user skills from `$HOME/.agents/skills`. For local use:

```bash
git clone https://github.com/SignorMercurio/sleuth.git \
  ~/.agents/skills/sleuth
```

For active development, symlink this checkout instead of cloning a second copy:

```bash
mkdir -p ~/.agents/skills
ln -s /path/to/sleuth ~/.agents/skills/sleuth
```

Codex also scans repository-scoped skills under `.agents/skills` from the current working directory up to the repo root.

### Claude Code — `npx skills`

Uses the community CLI [vercel-labs/skills](https://github.com/vercel-labs/skills):

```bash
npx skills add SignorMercurio/sleuth
```

### Claude Code — `npx openskills`

Uses [openskills](https://github.com/numman-ali/openskills), installing at user scope:

```bash
npx openskills install SignorMercurio/sleuth --global
```

### Manual copy or rsync

For Claude Code, copy to `~/.claude/skills/sleuth`. For Codex, copy to `~/.agents/skills/sleuth` or a repo-scoped `.agents/skills/sleuth`.

```bash
# Codex
rsync -avz --exclude '.git' ./sleuth/ \
  <host>:~/.agents/skills/sleuth/

# Claude Code
rsync -avz --exclude '.git' ./sleuth/ \
  <host>:~/.claude/skills/sleuth/
```

After install, run `/skills` in Claude Code or mention `$sleuth` / use the skills selector in Codex to confirm the skill is loaded. It activates automatically when the context matches and can also be invoked explicitly.

## Usage

### Alarm-driven mode

Provide:
- Aliyun tenant **UID**
- Alarm **Event ID**
- SIREN **Client ID** (if omitted, the skill lists available clients for you to pick)

The skill pulls the alarm detail and runs the matching playbook end to end.

### Free-form mode

When there is no alarm ID, provide the Client ID plus a short description of the anomaly (e.g. "process X at 100% CPU", "suspicious file at /tmp/x.sh"). The skill starts from broad triage and narrows down from there.

## Layout

```
.
├── agents/
│   └── openai.yaml                         # Codex app metadata and SIREN MCP dependency hint
├── SKILL.md                                # Skill definition and workflow
├── assets/
│   └── report.md                           # Markdown report template copied from dossier/report.md
└── references/
    ├── invest_*.md                         # 12 investigation playbooks (one is general tradecraft)
    ├── tech_*.md                           # 6 tradecraft guides
    ├── attack_framework.md                 # ATT&CK tactic/technique reference
    ├── report_naming.md                    # IR-….md filename format and event_type slug table
    ├── cloud_log_queries.md                # WAF / SAS / ActionTrail log routing
    ├── sas_sls_host_telemetry.md           # SAS SLS host telemetry queries (env-specific gotchas)
    ├── oob_dnslog_investigation.md         # dnslog.cn / interact.sh / OOB callbacks
    ├── recon_residual.md                   # Residual-risk follow-ups after the 6-axis sweep
    └── aspnet_webshell_upload_tracing.md   # ASP.NET webshell upload tracing
```

Files under `references/` are loaded on demand — the skill reads only the entries relevant to the current alarm or scenario, keeping the context window from being flooded on the first turn.

## Output examples

The skill writes a Markdown report into the cwd:

- `IR-20260417-web01-webshell-123456.md` — alarm-driven, Event ID `123456`
- `IR-20260417-db-prod-rce.md` — free-form mode

Each report file is copied from `assets/report.md` and then filled for the specific incident.

The full event-type slug table (`webshell` / `miner` / `revshell` / `brute` / `abnlogin` / `privesc` / `exfil` / `ransom` / `sqli` / `rce` / `backdoor` / `unknown`) is documented in `references/report_naming.md`.

## Contributing

Playbooks and tradecraft guides live in `references/`, and the report template lives in `assets/report.md`. Playbooks, guides, and the report template are plain Markdown — PRs adding new attack types or refining command snippets are welcome. Template changes should be made in the upstream `dossier` project and then synced into this skill.
