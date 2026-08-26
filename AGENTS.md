# AGENTS.md

sleuth is a security-investigation agent skill repository for read-only remote incident response via SIREN, ATT&CK-chain analysis, and Chinese IR reports.

## Task-specific guidance

Read only the guides relevant to the task:

- [Repository boundaries](docs/agent-guidance/repository-boundaries.md): package layout, source ownership, and distributable assets.
- [Investigation contracts](docs/agent-guidance/investigation-contracts.md): evidence handling and SAS, SLS, or OpenCLI routing.
- [Report writing](docs/agent-guidance/report-writing.md): writer isolation, fact boundaries, and rule ownership.
- [Runtime governance](docs/agent-guidance/runtime-governance.md): permission anchors, mock SIREN tests, and generated trust evidence.
- [Verification](docs/agent-guidance/verification.md): baseline and change-specific checks.
- [Release operations](docs/agent-guidance/release-operations.md): remote deployment and dual-remote pushes.

For every repository change, run the baseline checks in the verification guide.
