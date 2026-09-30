# Workflow guide

[← WhiteKiwi Skills](../README.md)

## Use the Create Design Guideline skill

Choose this focused workflow to establish a new guideline or substantially revise the canonical document:

```text
Use the create-design-guideline skill to research and create a brand and product guideline for this app.
Use the create-design-guideline skill to substantially revise our canonical design guideline.
```

It turns product context, inherited brand choices, and authoritative references into a visual thesis, operating principles, foundations, semantic tokens, theme mappings, interaction states, and an adoption plan. Its canonical template records evidence and decision status; when implementation is authorized, it also maintains a concise `DESIGN.md` execution contract and verifies representative screens. Audit-only requests belong to the broader Design Guidelines workflow below.

Read [skills/create-design-guideline/SKILL.md](../skills/create-design-guideline/SKILL.md). The skill includes its own research reference, canonical deliverable template, and Node.js contrast checker with the same report and gate behavior described below. Each design workflow is self-contained and independently installable.

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

Read the authored workflow in [skills/design-guidelines/SKILL.md](../skills/design-guidelines/SKILL.md). Use Create Design Guideline for focused guideline creation or major revision, and Design Guidelines for broader research, audits, and authorized implementation. Install either workflow or both.

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

Read the authored workflow in [skills/locron/SKILL.md](../skills/locron/SKILL.md) and its on-demand [safety reference](../skills/locron/references/safety.md).

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

Read the authored workflow in [skills/pushman/SKILL.md](../skills/pushman/SKILL.md) and its on-demand [safety reference](../skills/pushman/references/safety.md).
