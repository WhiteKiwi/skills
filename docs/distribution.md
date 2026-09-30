# Distribution

[← WhiteKiwi Skills](../README.md) · [Install](../INSTALL.md) · [Maintain](maintaining.md)

Verified against upstream documentation on **2026-09-30**. Distinguish an installable source, a search-directory entry, and an authenticated registry publication. This repository does not claim official status or completed third-party listings.

## Supported routes

| Destination | Distribution mechanism | What this repository provides | Authentication / publication |
|---|---|---|---|
| Hermes Skills Hub | Public GitHub tap and direct repo/path installation | Standard `skills/<name>/SKILL.md`, companion files, discovery groupings | Pushing the public source is sufficient for direct installation; no Hermes publisher login. Private taps or GitHub rate limits may need a GitHub token |
| skills.sh / Vercel skills CLI | GitHub-hosted skills and install-driven directory | Portable sources plus generated `skills.sh.json` | No separate upload command for ordinary GitHub skills. Real CLI installs with telemetry contribute to discovery; indexing/cache timing is external |
| Claude Code | Git-hosted plugin marketplace | Generated marketplace and per-skill plugin | Register the public repository; this is not a claim of inclusion in Anthropic's curated marketplace |
| Codex / ChatGPT | Git-backed plugin marketplace | Generated marketplace, per-skill plugin, UI metadata | Register the catalog in a supported client; not an official OpenAI listing |
| OpenClaw / ClawHub | Registry publication or local skill payload | Generated payload and existing publish script | Actual registry upload requires ClawHub authentication; `CLAWHUB_TOKEN` for the optional existing CI path |
| GitHub Releases | Independently versioned archives | Four reproducible ZIP formats and checksums per skill | Existing tagged release workflow uses GitHub credentials |

### Hermes

The canonical `skills/` structure already meets the official custom-tap layout. Use the direct form to avoid confusing a tap slug with a repository path:

```sh
hermes skills tap add WhiteKiwi/skills
hermes skills inspect WhiteKiwi/skills/skills/locron
hermes skills install WhiteKiwi/skills/skills/locron
```

Hermes downloads companion directories such as `references/` and `scripts/`. Community skills are scanned. Read any findings; do not add `--force` as a default installation step. The public repository is an install source, not automatically a built-in or trusted Hermes tap.

### skills.sh and other agent clients

```sh
npx skills add WhiteKiwi/skills --list
npx skills add WhiteKiwi/skills --skill create-design-guideline -a cursor
npx skills add WhiteKiwi/skills --skill create-design-guideline -a gemini-cli
npx skills add WhiteKiwi/skills --skill create-design-guideline -a github-copilot
npx skills add WhiteKiwi/skills --skill create-design-guideline -a opencode
```

These are client adapters, not four separate stores. The CLI also has a `hermes-agent` adapter; prefer Hermes' native tap route when you want its provenance and scan workflow. Do not install both a native plugin and a portable copy of the same skill unless you intend duplicate discovery.

Review destinations and existing same-name directories before installing or updating. Do not use unattended blanket overwrite flags. Installation compatibility is verified from upstream documentation; full agent runtimes are not exercised by this repository's tests.

`skills.sh.json` is generated from `catalog.json` categories and skill names. It is display metadata, not a publishing credential or installation manifest. The same groupings can label Hermes tap entries. A source push does not guarantee the directory has refreshed; do not manufacture installs to inflate its ranking.

## Additional directories investigated

| Directory | Observed model | Current support / boundary |
|---|---|---|
| [SkillsMP](https://skillsmp.com/) | Index of public GitHub `SKILL.md` files | Sources are compatible with its documented discovery model. Inclusion is controlled by the index; no upload API is assumed or fabricated |
| [LobeHub Skills](https://lobehub.com/skills) | Third-party skills marketplace; Hermes also integrates LobeHub's agent catalog | No verified skill-publisher API or successful submission is claimed here. A marketplace download endpoint is not an upload API; agent JSON and Agent Skills are different artifacts |
| [browse.sh](https://browse.sh) | Browserbase's website-specific automation skill catalog, integrated by Hermes | Not an appropriate generic upload target for these design, scheduler, and notification workflows |

Do not add a token or publish workflow for a service until its official submission method, package contract, ownership, and terms are verified. A future account or persistent credential setup requires the maintainer's action; never commit credentials to this repository.

## Release checklist

1. Run `./scripts/validate.sh`; confirm generated metadata matches the catalog
2. Inspect authored skill files and dependencies; keep each workflow self-contained
3. Push the reviewed commit. Hermes and direct GitHub installations can then consume it
4. For a changed skill payload, follow the [per-skill release process](maintaining.md#release)
5. For ClawHub, authenticate using its supported login and run the existing skill-scoped publish command; verify the registry entry afterward
6. Report destinations individually: installable, indexed, published, or awaiting authentication/review. Never treat a GitHub push as proof of every marketplace publication

## Primary sources

- [Hermes skills, hub sources, and custom tap publishing](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)
- [Hermes source documentation](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md)
- [Vercel skills CLI and agent adapters](https://github.com/vercel-labs/skills)
- [skills.sh discovery FAQ](https://skills.sh/docs/faq)
- [skills.sh repository customization](https://skills.sh/docs/customize) and [configuration schema](https://skills.sh/schemas/skills.sh.schema.json)
- [Agent Skills specification](https://agentskills.io/specification)
- [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [OpenAI plugin packaging](https://developers.openai.com/codex/plugins/build)
- [OpenClaw / ClawHub](https://docs.openclaw.ai/clawhub)
