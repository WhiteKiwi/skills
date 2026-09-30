# WhiteKiwi Skills

[![Validate](https://github.com/WhiteKiwi/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/WhiteKiwi/skills/actions/workflows/validate.yml)
[![Releases](https://img.shields.io/badge/releases-per--skill-blue)](https://github.com/WhiteKiwi/skills/releases)
[![License: MIT-0](https://img.shields.io/badge/license-MIT--0-blue.svg)](LICENSE)

Portable [Agent Skills](https://agentskills.io) for Claude Code, Codex and ChatGPT, and OpenClaw. Each workflow is published as a separately installable plugin or skill, so you can install only what you need.

## Available skills

| Skill | What it does | Requires | Install name |
|---|---|---|---|
| [Design Guidelines](skills/design-guidelines/SKILL.md) | Create, audit, and implement reusable brand and product guidelines | Node.js for the bundled contrast checker | `design-guidelines` |
| [Locron](skills/locron/SKILL.md) | Safely operate and diagnose local schedules | [`locron`](https://github.com/WhiteKiwi/locron#installation) on `PATH` | `locron` |
| [Pushman](skills/pushman/SKILL.md) | Safely send and inspect personal iPhone notifications | [`pushman`](https://github.com/pushmanhq/pushman-cli/blob/main/docs/INSTALL.md) on `PATH` | `pushman` |

The marketplace is the catalog, not an all-in-one bundle. Adding it makes the entries discoverable; it does **not** install every plugin. Install the individual entries you need.

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
# or
claude plugin install design-guidelines@whitekiwi-skills
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
# or
codex plugin add design-guidelines@whitekiwi-skills
```

Codex CLI uses `plugin add` for installation. The same catalog is available in the ChatGPT desktop Plugins directory after registration, where each workflow remains a separate install choice.

### OpenClaw

Install a skill directly by its owner-qualified ClawHub reference:

```sh
openclaw skills install @whitekiwi/locron
# or
openclaw skills install @whitekiwi/pushman
# or
openclaw skills install @whitekiwi/design-guidelines
```

The owner-qualified ClawHub reference is the supported registry path. Registry installs require a published ClawHub version; a repository push alone does not publish a new entry. Review the current registry scan before installing. Before publication or for local development, use the generated payload described below.

## Use the Design Guidelines skill

Ask for the outcome you need:

```text
Use the design-guidelines skill to create a brand and product guideline for this app.
Use the design-guidelines skill to audit this product's themes and interaction states.
Use the design-guidelines skill to implement the approved guideline in these components.
```

The workflow combines guideline creation, visual audits, and authorized implementation in one portable skill. It connects research to product decisions, separates proposed choices from verified implementation, and covers semantic tokens, typography, layout, themes, states, motion, and visual QA. Supporting references provide a canonical deliverable template, an audit format, accessibility requirements and exceptions, and guidance for agent-built interfaces.

The bundled checker needs Node.js and accepts opaque sRGB hex pairs. From the installed skill directory:

```sh
node scripts/contrast-check.mjs '#171717:#C6FF4A'
node scripts/contrast-check.mjs --min 4.5 --json '#171717:#C6FF4A'
```

Report mode measures without failing on low contrast. `--min` enables a gate for the chosen use; exit codes are 0 for a successful report or passing gate, 1 for a missed threshold, and 2 for invalid input. JSON preserves the full ratio. This checks color pairs, not complete WCAG conformance; alpha, CSS tokens, OKLCH, and P3 require separate resolution or measurement.

Read the authored workflow in [skills/design-guidelines/SKILL.md](skills/design-guidelines/SKILL.md). It consolidates the earlier local `create-design-guideline` and `design-guidelines` workflows under one public name.

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

The workflow is tested through Locron 0.9.2. It uses `explain` for the preferred consolidated job report, `why --run` for the full immutable attempt and event trace, and the installed `dashboard`, `mcp`, and `self-update` help surfaces for safe local operations. It falls back to the capabilities exposed by older installed versions instead of assuming newer commands exist.

Read the authored workflow in [skills/locron/SKILL.md](skills/locron/SKILL.md) and its on-demand [safety reference](skills/locron/references/safety.md).

## Use the Pushman skill

Install [Pushman CLI](https://github.com/pushmanhq/pushman-cli/blob/main/docs/INSTALL.md) 0.1.1 or newer, authorize it through a browser or the iPhone app, and optionally connect its local stdio MCP server:

```sh
pushman login
# or: pushman pair
codex mcp add pushman -- pushman mcp
```

Then ask the agent directly:

```text
Use the pushman skill to notify me when this task finishes.
```

The workflow is tested through Pushman 0.1.1. It prefers typed MCP tools, falls back to stable CLI JSON for sends, treats a direct exact-send request as authorization for one send, and never turns a draft or inspection request into a notification. It does not automatically retry ambiguous results because a retry can create a duplicate and consume quota, and it keeps Homebrew self-update separate from notification and credential operations.

Read the authored workflow in [skills/pushman/SKILL.md](skills/pushman/SKILL.md) and its on-demand [safety reference](skills/pushman/references/safety.md).

## Update or remove

### Claude Code

```sh
claude plugin marketplace update whitekiwi-skills
claude plugin update design-guidelines@whitekiwi-skills
claude plugin update locron@whitekiwi-skills
claude plugin update pushman@whitekiwi-skills
claude plugin uninstall locron@whitekiwi-skills
claude plugin uninstall pushman@whitekiwi-skills
claude plugin uninstall design-guidelines@whitekiwi-skills
```

### Codex and ChatGPT

```sh
codex plugin marketplace upgrade whitekiwi-skills
codex plugin remove design-guidelines@whitekiwi-skills
codex plugin remove locron@whitekiwi-skills
codex plugin remove pushman@whitekiwi-skills
codex plugin add locron@whitekiwi-skills
codex plugin add pushman@whitekiwi-skills
codex plugin add design-guidelines@whitekiwi-skills
```

Remove the catalog itself only when it is no longer needed:

```sh
codex plugin marketplace remove whitekiwi-skills
```

### OpenClaw

```sh
openclaw skills update @whitekiwi/locron
openclaw skills update @whitekiwi/pushman
openclaw skills update @whitekiwi/design-guidelines
```

The current native OpenClaw CLI does not expose `skills uninstall`. The standalone `clawhub uninstall` command applies to installations tracked by the standalone ClawHub CLI, not automatically to native OpenClaw-managed installations.

## Distribution model

The install boundary is a plugin, not the entire repository. WhiteKiwi publishes an independent plugin for each standalone workflow. A plugin may contain more than one skill only when those skills form one coherent capability that users would normally install together.

| Client | Distribution | Generated metadata |
|---|---|---|
| Claude Code | Git-hosted plugin marketplace | `.claude-plugin/plugin.json` |
| Codex and ChatGPT | Git-backed plugin marketplace | `.codex-plugin/plugin.json` and `agents/openai.yaml` |
| OpenClaw | ClawHub Agent Skill | `metadata.openclaw.requires.bins` |

Each `skills/<name>/` directory is an authored workflow. Its generated `plugins/<name>/` package contains only that workflow. `scripts/build.sh` produces every adapter from those sources, injects only platform-specific metadata, preserves executable helpers, and rejects generated drift. Release archives are deterministic and include checksums.

Each skill has an independent semantic version in `catalog.json` at `skills.<name>.version`. Its Claude/Codex manifests, Claude marketplace entry, ZIP names, and ClawHub publication all use that version. Updating Locron leaves the Design Guidelines and Pushman versions and archives unchanged. The migration preserves `0.6.0` as the starting version of all three skills; future bumps apply only to the changed skill.

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
openclaw skills install ./platforms/openclaw/design-guidelines --as design-guidelines
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
├── <skill>-SHA256SUMS
└── SHA256SUMS
```

Each `<skill>-skill-<version>.zip` contains only that portable skill. These archives are release and API convenience artifacts, not documented ChatGPT installation ZIPs.

`SHA256SUMS` covers the complete local build. Each `<skill>-SHA256SUMS` covers only that skill's four ZIPs and is attached to its release.

## Repository layout

```text
skills/<name>/                         authored sources of truth
plugins/<name>/                        generated, independently installable plugin
.claude-plugin/marketplace.json        generated catalog of Claude plugins
.agents/plugins/marketplace.json       generated catalog of Codex/ChatGPT plugins
platforms/openclaw/<name>/             generated OpenClaw skills
catalog.json                           per-skill versions and packaging metadata
scripts/                               deterministic build, validation, release
tests/                                 trigger, packaging, and behavior tests
.github/workflows/                     validation and tagged release
```

Do not edit generated files directly. Change `skills/<name>/` or `catalog.json`, then run `./scripts/build.sh`.

## Release

Update only the changed skill's `version` in `catalog.json`, rebuild, validate, and commit the source and generated metadata. For example, after bumping Locron to `0.6.1`:

```sh
./scripts/build.sh
./scripts/publish.sh --dry-run --skill locron
# Commit the source and generated metadata before tagging.
git push origin main
git tag locron-v0.6.1
git push origin locron-v0.6.1
```

The `*-v*` workflow requires an exact `<skill>-v<version>` match in the tagged catalog and verifies that the tag points to the checked-out commit. It creates an idempotent GitHub Release containing only that skill's four ZIPs and `<skill>-SHA256SUMS`. When `CLAWHUB_TOKEN` is configured, it also publishes only that skill's generated OpenClaw payload with its catalog version. Different skills can have release tags on the same commit.

Legacy repository-wide `v*` tags and releases remain available as historical snapshots. New releases use per-skill tags; there is no shared `VERSION` file.

To rerun a tagged release locally:

```sh
./scripts/publish.sh --release --tag locron-v0.6.1
```

For an authenticated manual ClawHub publication:

```sh
./scripts/publish.sh --clawhub --skill locron
```

Publication requires an explicit skill or release tag. `./scripts/publish.sh --dry-run` may still validate all entries, using each skill's own version, without publishing them.

Dry-runs can review uncommitted changes. Actual publication requires a clean committed working tree so the published payload corresponds to the repository state.

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills authoring best practices](https://agentskills.io/skill-creation/best-practices)
- [OpenAI plugin packaging](https://developers.openai.com/codex/plugins/build)
- [OpenAI plugin examples](https://github.com/openai/plugins)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [OpenClaw skills and ClawHub](https://docs.openclaw.ai/clawhub)

## License

This catalog and its skill artifacts are licensed under [MIT-0](LICENSE). Locron retains its own licenses; no Locron implementation code is included here.
