# Maintaining the catalog

[← WhiteKiwi Skills](../README.md) · [Distribution](distribution.md)

## Distribution model

The install boundary is a plugin, not the entire repository. WhiteKiwi publishes an independent plugin for each standalone workflow. A plugin may contain more than one skill only when those skills form one coherent capability that users would normally install together.

| Client | Distribution | Generated metadata |
|---|---|---|
| Claude Code | Git-hosted plugin marketplace | `.claude-plugin/plugin.json` |
| Codex and ChatGPT | Git-backed plugin marketplace | `.codex-plugin/plugin.json` and `agents/openai.yaml` |
| OpenClaw | ClawHub Agent Skill | `metadata.openclaw.requires.bins` |

Each `skills/<name>/` directory is an authored workflow. Its generated `plugins/<name>/` package contains only that workflow. `scripts/build.sh` produces every adapter from those sources, injects only platform-specific metadata, preserves executable helpers, and rejects generated drift. Release archives are deterministic and include checksums.

Each skill has an independent semantic version in `catalog.json` at `skills.<name>.version`. Its Claude/Codex manifests, Claude marketplace entry, ZIP names, and ClawHub publication all use that version. Updating Locron leaves the other skills' versions and archives unchanged. Design Guidelines, Locron, and Pushman kept `0.6.0` when migrating to independent versions; Create Design Guideline and Loboot were each added at `0.1.0`. Create Design Guideline `0.2.0` consolidates the former Design Guidelines workflow; the old name is no longer a catalog entry. Future bumps apply only to the changed skill.

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
openclaw skills install ./platforms/openclaw/loboot --as loboot
openclaw skills install ./platforms/openclaw/locron --as locron
openclaw skills install ./platforms/openclaw/create-design-guideline --as create-design-guideline
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
skills.sh.json                         generated discovery categories
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

The optional **Run workflow** entry in GitHub Actions uses the same release job without requiring local GitHub CLI credentials. Select `main`, provide the exact per-skill tag and the reviewed full current-main commit SHA. The workflow validates first, rechecks the checkout and remote main, verifies or creates that exact tag without force, and publishes in the same run using its existing ephemeral GitHub token. A stale commit, version mismatch, dirty checkout, non-main dispatch, or conflicting tag fails closed. Token-created tags do not need to trigger a second workflow. The normal tag-push route remains supported.

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


Hermes uses the authored portable source directly. `skills.sh.json` is generated from catalog categories; it does not change skill payload versions or archives. See [distribution](distribution.md) for publication and discovery boundaries.

### Optional installed-CLI forward checks

When `loboot` is on `PATH`, `./scripts/validate.sh` also exercises its Linux and macOS offline renderers in temporary roots. The checks cover read-only previews, definition add/show/update/remove, read-only foreign discovery, and rejection of live actions offline. They never operate on real user services. Without the binary, these tests report a skip; catalog packaging validation is not native login-session acceptance.
