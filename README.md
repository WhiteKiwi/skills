# WhiteKiwi Skills

Portable Agent Skills published from one authored workflow per skill. The first catalog entry helps agents operate [Locron](https://github.com/whitekiwi/locron), the local-first scheduler that explains its durable decisions.

## Install Locron

The skill requires the `locron` executable on `PATH`. Install Locron before installing the skill and confirm it with:

```sh
locron --version --format json
```

The skill checks the installed version and help surface before it acts. It does not bundle or install the scheduler.

## Claude Code

```sh
claude plugin marketplace add whitekiwi/skills
claude plugin install locron@whitekiwi-skills
```

Invoke it explicitly by asking Claude to use the `locron` skill, or make a Locron scheduling or diagnosis request for automatic discovery.

Update or remove it with:

```sh
claude plugin marketplace update whitekiwi-skills
claude plugin update locron@whitekiwi-skills
claude plugin uninstall locron@whitekiwi-skills
```

## OpenClaw

After the first ClawHub publication:

```sh
openclaw skills install @whitekiwi/locron
```

Update a registry-tracked installation with:

```sh
openclaw skills update @whitekiwi/locron
```

OpenClaw 2026.7.1-2 exposes no `skills uninstall` command. Use the client's current managed-skill removal guidance rather than deleting an unknown path. Git and local installs can be used for development but must be reinstalled to update.

## Codex and ChatGPT

Add the GitHub catalog:

```sh
codex plugin marketplace add whitekiwi/skills
codex plugin add locron@whitekiwi-skills
```

The plugin is also available from the Plugins browser in the ChatGPT desktop app after adding the catalog. Codex CLI 0.149.1 calls its installation command `plugin add`, not `plugin install`.

Refresh or remove the catalog with:

```sh
codex plugin marketplace upgrade whitekiwi-skills
codex plugin remove locron@whitekiwi-skills
codex plugin marketplace remove whitekiwi-skills
```

For local experimentation with only the standalone skill, invoke `$skill-installer` and ask it to install `skills/locron` from `whitekiwi/skills`. This is not the supported marketplace update path.

## Manual and local development installs

Clone the repository, validate it, then use the platform's local source support:

```sh
git clone https://github.com/whitekiwi/skills.git
cd skills
./scripts/validate.sh

claude plugin marketplace add .
openclaw skills install ./platforms/openclaw/locron --as locron
codex plugin marketplace add .
```

Keep test configuration isolated and remove the temporary marketplace or installed skill using the client surface available in that version.

## What the skill does

The skill uses the installed CLI as the authority and follows these boundaries:

- machine-readable `locron.cli/v1` reads before prose parsing;
- dry-run-first creation, updates, manual runs, imports, pruning, and configuration changes;
- exact-target read-back and current-request authorization for mutations without dry-run;
- direct argv targets unless shell semantics are explicitly needed;
- explicit timezone and missed-run/overlap consequences;
- evidence-led diagnosis through service state, `doctor`, `why`, `history`, run explanations, and logs;
- no inference that the machine slept, and no inferred plaintext import/export acknowledgement.

The authored workflow is [skills/locron/SKILL.md](skills/locron/SKILL.md). Generated adapters are never edited directly.

## Build and validate

```sh
./scripts/build.sh
./scripts/validate.sh
```

`build.sh` validates the source, regenerates the committed marketplace payloads, and creates deterministic artifacts under `dist/`:

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

`locron-skill-<version>.zip` contains only the portable skill. It is a release/API convenience artifact and is not presented as a documented ChatGPT installation ZIP.

## Release

Update `VERSION`, rebuild the generated files, validate, and create the matching tag:

```sh
./scripts/publish.sh --dry-run
git tag v0.1.0
git push origin main --tags
```

The `v*` workflow runs `./scripts/publish.sh --release`. It requires the tag to equal `v$(cat VERSION)`, creates an idempotent GitHub Release, and attaches all ZIPs plus `SHA256SUMS`. When the repository secret `CLAWHUB_TOKEN` is configured, it also publishes the generated OpenClaw payload with an explicit version using `clawhub` 0.23.3. Without that secret, only the ClawHub step is skipped.

For a manual ClawHub publication after authentication:

```sh
./scripts/publish.sh --clawhub
```

Submission to Anthropic's official marketplace or OpenAI's universal Plugins Directory is not automated. Each requires a separate account, listing, review, and explicit publish action.

## Repository layout

```text
skills/locron/                         authored source of truth
plugins/locron/                        generated Claude/Codex plugin
.claude-plugin/marketplace.json        generated Claude catalog
.agents/plugins/marketplace.json       generated Codex catalog
platforms/openclaw/locron/             generated OpenClaw skill
scripts/                               deterministic build and validation
tests/                                 tooling and isolated Locron checks
.github/workflows/                     validation and tagged release
```

## Platform differences

| Item | Claude Code | OpenClaw / ClawHub | Codex / ChatGPT |
|---|---|---|---|
| Skill compatibility | Agent Skills | Agent Skills plus generated `metadata.openclaw` | Agent Skills |
| Marketplace | Git-hosted Claude marketplace | ClawHub registry | Git-backed Codex marketplace; optional reviewed Plugins Directory |
| GitHub installation | Marketplace shorthand | Direct Git is supported but not registry-updateable | Marketplace shorthand |
| Publish method | Push the GitHub catalog; official directory submission is separate | `clawhub skill publish` | Push the GitHub catalog; public directory submission is separate |
| Automatic/update path | Marketplace refresh plus plugin update | `skills update` for ClawHub-tracked installs | Marketplace snapshot upgrade; public directory changes require review |
| Additional manifest | `.claude-plugin/plugin.json` | Nested OpenClaw binary requirement only | `.codex-plugin/plugin.json` |

## License

This catalog and its skill artifacts are licensed under [MIT-0](LICENSE). Locron itself retains its own licenses; no Locron implementation code is included here.
