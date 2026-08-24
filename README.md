# WhiteKiwi Skills

[![Validate](https://github.com/WhiteKiwi/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/WhiteKiwi/skills/actions/workflows/validate.yml)
[![Latest release](https://img.shields.io/github/v/release/WhiteKiwi/skills)](https://github.com/WhiteKiwi/skills/releases/latest)
[![License: MIT-0](https://img.shields.io/badge/license-MIT--0-blue.svg)](LICENSE)

Portable [Agent Skills](https://agentskills.io) for Claude Code, Codex and ChatGPT, and OpenClaw. One authored workflow is validated and packaged for every supported client.

The first skill operates [Locron](https://github.com/WhiteKiwi/locron), the local-first scheduler that explains its durable decisions. It lets an agent create and change jobs safely, inspect scheduler state, and diagnose missed or failed runs through the installed Locron CLI.

## Quick start

Install [Locron](https://github.com/WhiteKiwi/locron#installation) first. The skill does not bundle the scheduler and requires `locron` on `PATH`:

```sh
locron --version --format json
```

Then install the skill for your client.

### Claude Code

```sh
claude plugin marketplace add WhiteKiwi/skills
claude plugin install locron@whitekiwi-skills
```

### Codex and ChatGPT

```sh
codex plugin marketplace add WhiteKiwi/skills
codex plugin add locron@whitekiwi-skills
```

Codex CLI uses `plugin add` for installation. The same generated plugin is available to the ChatGPT desktop Plugins browser after adding this catalog.

### OpenClaw

```sh
openclaw skills install @whitekiwi/locron
```

The owner-qualified ClawHub reference is the supported registry path. Review its current scan result on the [Locron ClawHub page](https://clawhub.ai/whitekiwi/skills/locron) before installing. For local development, use the generated payload described below.

## Use the Locron skill

Ask the agent to use Locron, or invoke the skill explicitly on clients that expose named skill invocation. For example:

```text
Use the locron skill to explain why the backup job did not run.
```

The workflow follows four operating rules:

- discover the installed Locron version and help surface before composing commands;
- prefer versioned `locron.cli/v1` JSON for observations and decisions;
- dry-run supported mutations, inspect the normalized result, then apply only when the request authorizes it;
- finish mutations with an exact-target read-back and diagnoses with durable evidence.

Locron 0.6.0's `explain` command is the preferred consolidated job report. The skill falls back to the installed 0.5.x diagnostic surface when `explain` is unavailable, and uses `why --run` for the full immutable attempt and event trace.

Read the authored workflow in [skills/locron/SKILL.md](skills/locron/SKILL.md) and its on-demand [safety reference](skills/locron/references/safety.md).

## Update or remove

### Claude Code

```sh
claude plugin marketplace update whitekiwi-skills
claude plugin update locron@whitekiwi-skills
claude plugin uninstall locron@whitekiwi-skills
```

### Codex and ChatGPT

```sh
codex plugin marketplace upgrade whitekiwi-skills
codex plugin remove locron@whitekiwi-skills
codex plugin add locron@whitekiwi-skills
```

Remove the catalog itself only when it is no longer needed:

```sh
codex plugin marketplace remove whitekiwi-skills
```

### OpenClaw

```sh
openclaw skills update @whitekiwi/locron
```

The current native OpenClaw CLI does not expose `skills uninstall`. The standalone `clawhub uninstall` command applies to installations tracked by the standalone ClawHub CLI, not automatically to native OpenClaw-managed installations.

## Portable by construction

| Client | Distribution | Generated metadata |
|---|---|---|
| Claude Code | Git-hosted plugin marketplace | `.claude-plugin/plugin.json` |
| Codex and ChatGPT | Git-backed plugin marketplace | `.codex-plugin/plugin.json` and `agents/openai.yaml` |
| OpenClaw | ClawHub Agent Skill | `metadata.openclaw.requires.bins` |

`skills/locron/` is the only authored workflow. `scripts/build.sh` produces every adapter from that source, injects only platform-specific metadata, and rejects generated drift. Release archives are deterministic and include checksums.

## Local development

Clone and validate the repository:

```sh
git clone https://github.com/WhiteKiwi/skills.git
cd skills
./scripts/validate.sh
```

Use a local package without publishing it:

```sh
claude plugin marketplace add .
codex plugin marketplace add .
openclaw skills install ./platforms/openclaw/locron --as locron
```

Build all generated payloads and reproducible release archives:

```sh
./scripts/build.sh
./scripts/validate.sh
```

```text
dist/
├── claude/locron/
├── openclaw/locron/
├── codex/locron/
├── skill/locron/
├── locron-claude-<version>.zip
├── locron-openclaw-<version>.zip
├── locron-codex-<version>.zip
├── locron-skill-<version>.zip
└── SHA256SUMS
```

`locron-skill-<version>.zip` contains only the portable skill. It is a release and API convenience artifact, not a documented ChatGPT installation ZIP.

## Repository layout

```text
skills/locron/                         authored source of truth
plugins/locron/                        generated Claude/Codex plugin
.claude-plugin/marketplace.json        generated Claude marketplace
.agents/plugins/marketplace.json       generated Codex marketplace
platforms/openclaw/locron/             generated OpenClaw skill
scripts/                               deterministic build, validation, release
tests/                                 trigger, packaging, and Locron behavior tests
.github/workflows/                     validation and tagged release
```

Do not edit generated files directly. Change `skills/locron/`, `catalog.json`, or `VERSION`, then run `./scripts/build.sh`.

## Release

Maintainers update `VERSION`, rebuild, validate, and create the matching tag:

```sh
./scripts/publish.sh --dry-run
git tag "v$(cat VERSION)"
git push origin main --tags
```

The `v*` workflow verifies that the tag matches `VERSION`, creates an idempotent GitHub Release, and attaches every ZIP plus `SHA256SUMS`. When `CLAWHUB_TOKEN` is configured, it also publishes the generated OpenClaw payload with the same explicit version.

For an authenticated manual ClawHub publication:

```sh
./scripts/publish.sh --clawhub
```

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills authoring best practices](https://agentskills.io/skill-creation/best-practices)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [OpenClaw skills and ClawHub](https://docs.openclaw.ai/clawhub)

## License

This catalog and its skill artifacts are licensed under [MIT-0](LICENSE). Locron retains its own licenses; no Locron implementation code is included here.
