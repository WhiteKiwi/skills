---
name: create-design-guideline
description: Create or substantially revise a reusable brand and product design guideline from product context, existing assets, and authoritative references. Use when the user asks to establish a visual system, brand guide, color and theme rules, design principles, or a canonical guideline page/document. Do not use for an audit-only review or a one-off cosmetic CSS change.
license: MIT-0
---

# Create Design Guideline

Create a decision system that another designer or engineer can apply without guessing. Deliver a canonical guideline with evidence, semantic tokens, interaction rules, and verification criteria.

## Read the relevant references

- Always read [references/research-and-color.md](references/research-and-color.md) before selecting colors or citing design systems.
- Read [references/deliverable-template.md](references/deliverable-template.md) before drafting the canonical guideline or implementing it.
- Use the bundled Node.js helper `scripts/contrast-check.mjs` for opaque sRGB foreground/background candidates. Measure pairs and inspect rendered layouts as separate checks.

## Establish the brief

Inspect existing product screens, code, tokens, brand assets, content, repository instructions, and prior research before proposing rules. Capture:

- product, audience, context, and desired impression
- brand signals worth preserving and visual problems to avoid
- supported surfaces, themes, viewport classes, languages, and exports
- whether the requested outcome is documentation only, a contained lab, or implementation

Ask only about choices that would materially change the direction and cannot be inferred safely. Record assumptions when proceeding without an answer.

Maintain an evidence ledger with four labels:

- `inherited`: already established by the product or brand
- `observed`: found in the current interface or assets
- `proposed`: a new or revised decision
- `verified`: measured or visually checked, with the intended surface, state, and date

Track approval and implementation separately using `candidate`, `approved`, or `implemented`. Preserve approval already granted for the requested scope; a passing measurement does not grant approval or prove deployment. Do not present a proposal as implemented reality.

## Research with purpose

Research current authoritative sources when the user requests references, trends, famous examples, or evidence. Prefer official design systems, brand guides, platform guidance, and standards. Use portfolio or editorial examples for composition and taste, not as normative accessibility evidence.

For every reference retained, write the decision it informs. Avoid a gallery of links with no effect on the guideline. Distinguish established requirements from aesthetic interpretation.

## Define the visual thesis first

Write one concise brand thesis and three to five operating principles. Each principle must resolve a recurring design choice. Good principles contain a preference and its reason, such as “quiet neutrals hold long-form evidence; the signature color marks decisive moments.”

Then define only the visual dimensions the product needs:

- layout grid, alignment, density, responsive behavior, and page rhythm
- typography roles, weights, line height, measure, and wrapping
- color roles, themes, and interactive states
- radius, border, elevation, blur, texture, and gradient policy
- imagery, diagrams, screenshots, and evidence treatment
- motion density, duration families, entry behavior, and reduced motion
- voice, labeling, and content hierarchy when they affect the interface

When an agent-facing implementation contract is part of the requested deliverable, update the repository's existing design contract; create `DESIGN.md` only if no canonical equivalent exists. Record atmosphere, semantic roles, component states, responsive art direction, anti-patterns, and release checks. Use taste dials such as design variance, motion intensity, and visual density when they clarify product decisions. Keep detailed rationale in the canonical human-facing guideline. A documentation-only request does not imply repository edits.

For responsive web products, preserve the established URL and content architecture while allowing distinct composition. Classify each mobile section as `preserve`, `recompose`, `collapse`, or `defer`; keep essential information and actions available in each supported viewport.

Component registries such as 21st.dev are discovery tools, not design authority. Check authorship, license, dependencies, accessibility behavior, reduced motion, and token fit before adoption, then translate the result into the product's semantic system.

Avoid turning a passing style preference into a universal rule. Explain why each rule serves this brand, audience, and content.

## Design color as role contracts

Define jobs before values:

1. canvas and raised surfaces
2. primary, secondary, and muted text
3. subtle and strong boundaries
4. interactive text and boundaries
5. focus indicators
6. brand field, brand boundary, and on-brand content
7. success, warning, error, and information

Build primitives only for jobs that exist. For new or revised palettes, author relationships in OKLCH or another suitable perceptual space and record stable sRGB hex fallbacks. Preserve an established palette or token format unless the requested change requires revising it. Do not generate a ramp by changing HSL lightness alone.

Bright brand colors often require separate tokens for a signal field, soft surface, focus/boundary, and accessible text. Never assume one brand hex can perform every job. Keep the brand hue separate from semantic success or warning roles.

Approve foreground/background pairs, not isolated swatches:

- ordinary text: WCAG 2.2 contrast at least `4.5:1`
- large text and essential non-text information: at least `3:1`, using the definitions and exceptions in the color reference
- translucent colors: check the composited result on every supported background
- essential meaning: add text, shape, or icon instead of relying on color alone

Map semantic roles independently in each supported theme, including fixed-theme scenes. Do not introduce a light or dark theme merely to fill a template. Preserve hierarchy rather than identical values. Define rest, hover, active/selected, focus-visible, and disabled states on every relevant background.

From this skill's directory, measure or gate opaque sRGB pairs:

```sh
node scripts/contrast-check.mjs '#171717:#C6FF4A'
node scripts/contrast-check.mjs --min 4.5 --json '#171717:#C6FF4A'
```

Report mode measures without failing on low contrast. `--min` accepts a threshold from 1 through 21 and gates the chosen use. Exit codes are `0` for a report or passing gate, `1` for a missed threshold, and `2` for invalid input. JSON retains the full ratio. The helper accepts `#RGB` and `#RRGGBB`; resolve alpha, CSS tokens, OKLCH, or P3 separately. Use an equivalent verified measurement if Node.js is unavailable and record that limitation. A color-pair result does not establish complete accessibility conformance.

## Build implementation-ready tokens

When code is in scope, use three layers:

1. `primitive`: visual values such as neutral and brand families
2. `semantic`: stable intent such as `text-primary`, `surface-raised`, or `brand-field`
3. `component`: a narrow exception only when semantic roles cannot express it

Components must not select primitive hex values directly. Name roles by purpose, not appearance. Keep token names stable when theme values change.

## Produce the canonical artifact

Use the structure and tables in [references/deliverable-template.md](references/deliverable-template.md). Mark the artifact `candidate`, `approved`, or `implemented`, with a version and date. Include allowed and forbidden combinations, not only preferred examples.

If the user asked only for a guideline, stop after delivering the canonical artifact and an adoption plan. Do not silently redesign or deploy the product.

If implementation is requested:

1. update the canonical guideline and core tokens together
2. migrate representative components before broad mechanical replacement
3. remove direct literals only where their semantic replacement is established
4. preserve intentional fixed-theme specimens and documented exceptions
5. keep rollout reversible and do not deploy without authorization

## Verify the system visibly

Inspect representative rendered pages rather than the guideline page alone:

- supported light, dark, or fixed themes
- the narrowest supported viewport and a typical wide viewport; for web products, check reflow at 320 CSS px where applicable
- rest, hover, active/selected, keyboard focus, disabled, error, and success states that exist
- longest realistic headings, paragraphs, URLs, and Korean or other non-Latin wrapping when relevant
- reduced motion
- print, PDF, social preview, or export surfaces when present

Check visual hierarchy, accent area, unwanted hue casts in neutrals, local contrast, and whether decoration competes with content. Run the product's build and static checks in proportion to risk. For documentation-only work, record these as adoption checks where no implementation exists. If rendering or measurement is unavailable, identify what remains unverified. Record unresolved choices explicitly instead of freezing them by accident.
