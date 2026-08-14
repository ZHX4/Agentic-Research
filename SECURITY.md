# Security Policy

## Supported versions

The `main` branch is the actively maintained development and production branch.

## Reporting a vulnerability

Please do not disclose security vulnerabilities in public issues. Report them privately through GitHub's security advisory mechanism for this repository when available.

When reporting a vulnerability, include:

- a concise description of the issue;
- affected component(s) and version/commit;
- reproduction steps or a minimal proof of concept;
- the potential impact;
- any known mitigations.

Do not include secrets, private datasets, credentials, or personal data in a report.

## Security-sensitive areas

Particular care is required around:

- external literature provider credentials;
- model/provider API keys;
- Docker experiment execution;
- downloaded scientific artifacts;
- autonomous execution state and checkpoints;
- publication bundles and release artifacts.

Production deployments should use least-privilege credentials, isolated execution environments, controlled filesystem mounts, and explicit network policies.
