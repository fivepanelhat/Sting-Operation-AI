# Security Policy - Sting-Operation-AI

Edge vision / wasp detection workloads for Coastal Alpine Tech.

## Supported Versions

| Branch | Supported |
| ------ | --------- |
| `main` | Yes |

## Vulnerability Disclosure

Do not open public issues for security flaws. Use a private GitHub Security Advisory or contact the Chief Architect.

## Security Notifications

| Channel | Response |
| ------- | -------- |
| Dependabot | Weekly pip / Actions updates |
| Code scanning | Fix SAST findings on `main` |
| Core SDK | Consume `SecurityGuard` on text/prompt paths |
| Dataset tools | **Never** write API keys to disk from scripts |

## Active patches (2026-07)

| Finding | Severity | Fix |
| ------- | -------- | --- |
| CodeQL `py/clear-text-storage-sensitive-data` in `tools/download_dataset.py` | Error | Script no longer writes `ROBOFLOW_API_KEY` to `.env`; use environment variables only |
| Workflow token scope | Warning | `permissions: contents: read` on package CI |
| Prompt / label abuse | High | Core `SecurityGuard` on inference text inputs |

## Secrets handling

- `.env` and `.env.*` are gitignored.
- Set `ROBOFLOW_API_KEY` in the environment for dataset download and training.
- Rotate keys if they were ever committed or shared in chat logs.

## Quality gates

- CI (conda/python package), SecOps Bandit, red-team, release drafts on tags.

## Fleet security principles

- **No silent exfiltration** of personal or tenant operational data
- Prefer **local-first** processing; third-party AI only with explicit operator configuration and UI/docs disclosure
- Report vulnerabilities via GitHub Security Advisories or the maintainer contact on the org profile
- High-stakes production changes require human approval (HITL)

## Data sales and third parties

- **We do not sell personal information or customer operational data to third parties.**
- Optional AI or cloud services run only when configured by the operator; processing must be disclosed (in-product and/or docs).
- Prefer local-first paths so third-party transfer is unnecessary by default.

## NZ Privacy Act and Te Mana Raraunga

- Design in accordance with the **Privacy Act 2020**.
- Operate in accordance with **Te Mana Raraunga** principles for Māori data sovereignty interests.
- Align AI features with **NZ AI safety** / responsible AI expectations (HITL, transparency, no silent training on private content).

