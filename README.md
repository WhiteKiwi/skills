# WhiteKiwi Skills

[![Validate](https://github.com/WhiteKiwi/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/WhiteKiwi/skills/actions/workflows/validate.yml)
[![Latest release](https://img.shields.io/github/v/release/WhiteKiwi/skills)](https://github.com/WhiteKiwi/skills/releases/latest)
[![License: MIT-0](https://img.shields.io/badge/license-MIT--0-blue.svg)](LICENSE)

Portable [Agent Skills](https://agentskills.io) for Claude Code, Codex and ChatGPT, and OpenClaw. Each workflow is published as a separately installable plugin or skill, so you can install only what you need.

## Available skills

| Skill | What it does | Requires | Install name |
|---|---|---|---|
| [Locron](skills/locron/SKILL.md) | Safely operate and diagnose local schedules | [`locron`](https://github.com/WhiteKiwi/locron#installation) on `PATH` | `locron` |
| [Pushman](skills/pushman/SKILL.md) | Safely send and inspect personal iPhone notifications | [`pushman`](https://github.com/WhiteKiwi/pushman-cli/blob/main/docs/INSTALL.md) on `PATH` | `pushman` |

The marketplace is the catalog, not an all-in-one bundle. Adding it makes the entries discoverable; it does **not** install every plugin. Install one or both entries explicitly.

## Install only what you need

### Claude Code

Register the catalog once:

```sh
claude plugin marketplace add WhiteKiwi/skills
```

Then choose a plugin:

```sh
claude plugin install locron@whitekiwi-skills
# or
claude plugin install pushman@whitekiwi-skills
```

### Codex and ChatGPT

Register the catalog once:

```sh
codex plugin marketplace add WhiteKiwi/skills
```

Then choose a plugin:

```sh
codex plugin add locron@whitekiwi-skills
# or
codex plugin add pushman@whitekiwi-skills
```

Codex CLI uses `plugin add` for installation. The same catalog is available in the ChatGPT desktop Plugins directory after registration, where Locron and Pushman remain separate install choices.

### OpenClaw

Install a skill directly by its owner-qualified ClawHub reference:

```sh
openclaw skills install @whitekiwi/locron
# or
openclaw skills install @whitekiwi/pushman
```

The owner-qualified ClawHub reference is the supported registry path. Review the current registry scan before installing. For local development, use the generated payload described below.

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

The workflow is tested through Locron 0.8.0. It uses `explain` for the preferred consolidated job report, `why --run` for the full immutable attempt and event trace, and the installed `dashboard` help surface for safe local dashboard lifecycle operations. It falls back to the capabilities exposed by older installed versions instead of assuming newer commands exist.

Read the authored workflow in [skills/locron/SKILL.md](skills/locron/SKILL.md) and its on-demand [safety reference](skills/locron/references/safety.md).

## Use the Pushman skill

Install [Pushman CLI](https://github.com/WhiteKiwi/pushman-cli/blob/main/docs/INSTALL.md) 0.1.0-beta.4 or newer, pair it with the iPhone app, and optionally connect its local stdio MCP server:

```sh
pushman pair
codex mcp add pushman -- pushman mcp
```

Then ask the agent directly:

```text
Use the pushman skill to notify me when this task finishes.
```

The workflow prefers typed MCP tools, falls back to the installed CLI, treats a direct exact-send request as authorization for one send, and never turns a draft or inspection request into a notification. It does not automatically retry ambiguous results because a retry can create a duplicate and consume quota.

Read the authored workflow in [skills/pushman/SKILL.md](skills/pushman/SKILL.md) and its on-demand [safety reference](skills/pushman/references/safety.md).

## Update or remove

### Claude Code

```sh
claude plugin marketplace update whitekiwi-skills
claude plugin update locron@whitekiwi-skills
claude plugin update pushman@whitekiwi-skills
claude plugin uninstall locron@whitekiwi-skills
claude plugin uninstall pushman@whitekiwi-skills
```

### Codex and ChatGPT

```sh
codex plugin marketplace upgrade whitekiwi-skills
codex plugin remove locron@whitekiwi-skills
codex plugin remove pushman@whitekiwi-skills
codex plugin add locron@whitekiwi-skills
codex plugin add pushman@whitekiwi-skills
```

Remove the catalog itself only when it is no longer needed:

```sh
codex plugin marketplace remove whitekiwi-skills
```

### OpenClaw

```sh
openclaw skills update @whitekiwi/locron
openclaw skills update @whitekiwi/pushman
```

The current native OpenClaw CLI does not expose `skills uninstall`. The standalone `clawhub uninstall` command applies to installations tracked by the standalone ClawHub CLI, not automatically to native OpenClaw-managed installations.

## Distribution model

The install boundary is a plugin, not the entire repository. WhiteKiwi publishes an independent plugin for each standalone workflow. A plugin may contain more than one skill only when those skills form one coherent capability that users would normally install together.

| Client | Distribution | Generated metadata |
|---|---|---|
| Claude Code | Git-hosted plugin marketplace | `.claude-plugin/plugin.json` |
| Codex and ChatGPT | Git-backed plugin marketplace | `.codex-plugin/plugin.json` and `agents/openai.yaml` |
| OpenClaw | ClawHub Agent Skill | `metadata.openclaw.requires.bins` |

Each `skills/<name>/` directory is an authored workflow. Its generated `plugins/<name>/` package contains only that workflow, so installing `locron` does not install `pushman`, and vice versa. `scripts/build.sh` produces every adapter from those sources, injects only platform-specific metadata, and rejects generated drift. Release archives are deterministic and include checksums.

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
openclaw skills install ./platforms/openclaw/pushman --as pushman
```

Build all generated payloads and reproducible release archives:

```sh
./scripts/build.sh
./scripts/validate.sh
```

```text
dist/
├── claude/<skill>/
├── openclaw/<skill>/
├── codex/<skill>/
├── skill/<skill>/
├── <skill>-claude-<version>.zip
├── <skill>-openclaw-<version>.zip
├── <skill>-codex-<version>.zip
├── <skill>-skill-<version>.zip
└── SHA256SUMS
```

Each `<skill>-skill-<version>.zip` contains only that portable skill. These archives are release and API convenience artifacts, not documented ChatGPT installation ZIPs.

## Repository layout

```text
skills/<name>/                         authored sources of truth
plugins/<name>/                        generated, independently installable plugin
.claude-plugin/marketplace.json        generated catalog of Claude plugins
.agents/plugins/marketplace.json       generated catalog of Codex/ChatGPT plugins
platforms/openclaw/<name>/             generated OpenClaw skills
catalog.json                           catalog and packaging metadata
scripts/                               deterministic build, validation, release
tests/                                 trigger, packaging, and behavior tests
.github/workflows/                     validation and tagged release
```

Do not edit generated files directly. Change `skills/<name>/`, `catalog.json`, or `VERSION`, then run `./scripts/build.sh`.

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
- [OpenAI plugin packaging](https://developers.openai.com/codex/plugins/build)
- [OpenAI plugin examples](https://github.com/openai/plugins)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [OpenClaw skills and ClawHub](https://docs.openclaw.ai/clawhub)

## License

This catalog and its skill artifacts are licensed under [MIT-0](LICENSE). Locron retains its own licenses; no Locron implementation code is included here.
