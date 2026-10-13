# Installation

[← WhiteKiwi Skills](README.md) · [Distribution](docs/distribution.md)

## Hermes Agent

```sh
hermes skills tap add WhiteKiwi/skills
hermes skills inspect WhiteKiwi/skills/skills/create-design-guideline
hermes skills install WhiteKiwi/skills/skills/create-design-guideline
```

Replace the last path segment with any skill in the catalog. No registry login is needed for this public source. Inspect scan results before installation.

```sh
hermes skills check
hermes skills update create-design-guideline
hermes skills uninstall create-design-guideline
```

## Portable CLI: Cursor, Gemini, Copilot, OpenCode, and more

Requires Node.js/npm and Git. List first, then select exactly what you need:

```sh
npx skills add WhiteKiwi/skills --list
npx skills add WhiteKiwi/skills --skill create-design-guideline -a cursor
# Other verified agent IDs: gemini-cli, github-copilot, opencode, hermes-agent
```

Omit `-a` for interactive client selection. The default is project scope; add `-g` only when you want global installation. Review existing same-name skill directories and back them up before installing or updating. Do not use blanket overwrite flags. Avoid installing both native-plugin and portable copies of the same workflow.

```sh
npx skills list
npx skills update create-design-guideline
npx skills remove create-design-guideline -a cursor
```

Without skill names, `skills update` can update multiple installed skills; keep the selection explicit. See [the upstream CLI](https://github.com/vercel-labs/skills) and [distribution requirements](docs/distribution.md).

## Native plugin and skill clients

### Claude Code

Register the catalog once:

```sh
claude plugin marketplace add WhiteKiwi/skills
```

Then choose a plugin:

```sh
claude plugin install loboot@whitekiwi-skills
# or
claude plugin install locron@whitekiwi-skills
# or
claude plugin install pushman@whitekiwi-skills
# or
claude plugin install design-guidelines@whitekiwi-skills
# or
claude plugin install create-design-guideline@whitekiwi-skills
```

### Codex and ChatGPT

Register the catalog once:

```sh
codex plugin marketplace add WhiteKiwi/skills
```

Then choose a plugin:

```sh
codex plugin add loboot@whitekiwi-skills
# or
codex plugin add locron@whitekiwi-skills
# or
codex plugin add pushman@whitekiwi-skills
# or
codex plugin add design-guidelines@whitekiwi-skills
# or
codex plugin add create-design-guideline@whitekiwi-skills
```

Codex CLI uses `plugin add` for installation. Use the plugin catalog UI in supported ChatGPT/Codex clients; availability depends on the client and account.

### OpenClaw

Install a skill directly by its owner-qualified ClawHub reference:

```sh
openclaw skills install @whitekiwi/locron
# or
openclaw skills install @whitekiwi/pushman
# or
openclaw skills install @whitekiwi/design-guidelines
# or
openclaw skills install @whitekiwi/create-design-guideline
```

The owner-qualified ClawHub reference is the supported registry path. Registry installs require a published ClawHub version; a repository push alone does not publish a new entry. Review the current registry scan before installing. Before publication or for local development, use the generated payload described below.

## Loboot

Install the agent workflow through a public-source route, independently of the Loboot executable:

```sh
npx skills add WhiteKiwi/skills --skill loboot
# or use the Hermes scan/install flow
hermes skills inspect WhiteKiwi/skills/skills/loboot
hermes skills install WhiteKiwi/skills/skills/loboot
```

Claude/Codex plugin commands are listed above. For OpenClaw before a verified registry publication, clone this repository and use the generated payload:

```sh
openclaw skills install ./platforms/openclaw/loboot --as loboot
```

The independently versioned [Loboot skill 0.1.0 release](https://github.com/WhiteKiwi/skills/releases/tag/loboot-v0.1.0) supplies `loboot-skill-0.1.0.zip` and Claude/Codex/OpenClaw variants with `loboot-SHA256SUMS`. Verify the release and checksums before unpacking. A portable skill ZIP is not a documented ChatGPT plugin installer.

The workflow requires the separate [Loboot CLI](https://github.com/WhiteKiwi/loboot/blob/main/docs/INSTALL.md) on `PATH`. Check the current official binary/Homebrew/source installation options there; this catalog does not install it, enable a service, or create a ClawHub listing. The skill targets CLI 0.1.0, with offline Linux/macOS coverage; real login-session acceptance must be evaluated separately.

## Update or remove

### Claude Code

```sh
claude plugin marketplace update whitekiwi-skills
claude plugin update design-guidelines@whitekiwi-skills
claude plugin update create-design-guideline@whitekiwi-skills
claude plugin update loboot@whitekiwi-skills
claude plugin update locron@whitekiwi-skills
claude plugin update pushman@whitekiwi-skills
claude plugin uninstall loboot@whitekiwi-skills
claude plugin uninstall locron@whitekiwi-skills
claude plugin uninstall pushman@whitekiwi-skills
claude plugin uninstall design-guidelines@whitekiwi-skills
claude plugin uninstall create-design-guideline@whitekiwi-skills
```

### Codex and ChatGPT

```sh
codex plugin marketplace upgrade whitekiwi-skills
codex plugin remove design-guidelines@whitekiwi-skills
codex plugin remove create-design-guideline@whitekiwi-skills
codex plugin remove loboot@whitekiwi-skills
codex plugin remove locron@whitekiwi-skills
codex plugin remove pushman@whitekiwi-skills
codex plugin add loboot@whitekiwi-skills
codex plugin add locron@whitekiwi-skills
codex plugin add pushman@whitekiwi-skills
codex plugin add design-guidelines@whitekiwi-skills
codex plugin add create-design-guideline@whitekiwi-skills
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
openclaw skills update @whitekiwi/create-design-guideline
```

The current native OpenClaw CLI does not expose `skills uninstall`. The standalone `clawhub uninstall` command applies to installations tracked by the standalone ClawHub CLI, not automatically to native OpenClaw-managed installations.


## Local OpenClaw payload

From a clone of this repository, after `./scripts/build.sh`:

```sh
openclaw skills install ./platforms/openclaw/create-design-guideline --as create-design-guideline
```

Choose the matching directory/name for another skill. See [maintenance](docs/maintaining.md) for builds and tagged registry releases.
