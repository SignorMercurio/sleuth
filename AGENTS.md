# AGENTS.md

sleuth is a security-investigation agent skill repository for read-only remote incident response via SIREN and ATT&CK-chain analysis. Formal IR reports are written from its findings by the companion `dossier` skill in the sibling `dossier` repository.

## Task-specific guidance

Read only the guides relevant to the task:

- [Repository boundaries](docs/agent-guidance/repository-boundaries.md): package layout, source ownership, and distributable assets.
- [Investigation contracts](docs/agent-guidance/investigation-contracts.md): evidence handling and SAS, SLS, or OpenCLI routing.
- [Runtime governance](docs/agent-guidance/runtime-governance.md): permission anchors, mock SIREN tests, and generated trust evidence.
- [Verification](docs/agent-guidance/verification.md): baseline and change-specific checks.
- [Release operations](docs/agent-guidance/release-operations.md): remote deployment and dual-remote pushes.

Select checks by the changed surface using the verification guide.
