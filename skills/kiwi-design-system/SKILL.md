---
name: kiwi-design-system
description: Apply and improve PIP, the WhiteKiwi design system. Use when a task explicitly chooses PIP, works on WhiteKiwi/kiwi-design-system, or changes a product using @whitekiwi/ui or @whitekiwi/tokens. Covers integration, design contracts, shared improvement proposals, upstream contributions, and consumer verification; not a general-purpose brand creation skill.
license: MIT-0
---

# Kiwi Design System

Use PIP's existing visual language and components in the requested product. When
product work reveals a useful shared improvement, propose it to the user,
contribute the agreed change to the design system first, then adopt it in the app.
Do not require another consumer or a minimum usage count.

## Read the right source

The [design-system repository](https://github.com/WhiteKiwi/kiwi-design-system)
owns the implementation and design contracts. This skill owns the agent workflow.

- [Public catalog](https://design.whitekiwi.link/): visual specimens, system layers, and design standards.
- [Design contract](https://github.com/WhiteKiwi/kiwi-design-system/blob/main/DESIGN.md) and [guidelines](https://github.com/WhiteKiwi/kiwi-design-system/blob/main/docs/guidelines.md): visual roles, interaction states, and rationale.
- [UI package](https://github.com/WhiteKiwi/kiwi-design-system/tree/main/packages/ui) and [tokens package](https://github.com/WhiteKiwi/kiwi-design-system/tree/main/packages/tokens): exports, dependencies, themes, and API limits.

Inspect the consumer's dependencies, lockfile, source, and repository instructions.
Check installed package versions against the inspected source revision: `main`
and the website may contain changes not yet published. Use a local checkout or
available source-reading tools; an unavailable source is a limitation, not proof
that a component or capability is absent.

## Choose the work

- **Integrate or change a PIP product:** read [references/integration.md](references/integration.md). Prefer existing APIs and composition before adding parallel local UI.
- **A useful shared gap emerges:** describe the current need, shared benefit, and smallest change to the user. A short proposal is enough; do not require a separate design document or another product example.
- **Implement an agreed improvement:** read [references/contribution.md](references/contribution.md). Make the shared change in the design-system repository first, including documentation and verification, then verify its use in the consumer.
- **Explain or review the system:** read the relevant source and report what exists, its contracts, and demonstrated gaps. Do not turn a review into implementation or apply PIP to an unrelated brand.

For newly discovered scope, get the user's agreement before contributing. Reuse
an explicit request or earlier approval; do not repeatedly ask for the same work.
If the user chooses an app-only solution, respect that scope. If upstream access
is unavailable, preserve the reproduction and proposed change for handoff.

Keep product data, business logic, and product-only composition in the app.
Share only the agreed reusable parts. Start with the current need rather than
speculative options. Track temporary workarounds with their reason, related
issue/PR, and removal condition.

## Keep public material reader-focused

The public site explains what PIP contains, its design criteria, and how its
layers fit together. The repository README explains what the project is and
where its parts live. Keep agent approval, execution, and rollout procedures in
this skill and its references. Keep visual rules and API details in their source
repository instead of copying a second catalog into the skill.

## Verify and finish

Use the design repository's current checks and inspect changed screens in the
relevant themes, states, and viewport sizes. Static checks do not prove keyboard
behavior or a consumer application's complete accessibility. Node.js and the
repository's pinned package manager are needed for builds; do not claim runtime
verification when those tools or the app are unavailable.

Report the source revision, checks actually run, related PRs, and what remains.
Distinguish design-system merge, npm publication, and consumer adoption. A
contribution request does not itself authorize publishing packages or deploying
the app. Follow already authorized release scope without asking again.
