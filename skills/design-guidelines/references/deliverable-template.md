# Canonical guideline template

Use the sections relevant to the product. Keep status, decisions, tokens, states, validation, and adoption explicit; omit empty sections.

## Header and foundation

Record name, version, date, status (`candidate`, `approved`, or `implemented`), decision authority when known, and supported products, surfaces, themes, and languages. State one visual thesis, operating principles, intended impression, and anti-goals. Distinguish inherited and observed choices from proposals and verified checks.

## Research ledger

| Source | Observed method | Product decision | Authority |
| --- | --- | --- | --- |
| Direct link | Finding | Concrete rule and its scope | Standard / system / brand / inspiration |

## Foundations

Include `use`, `avoid`, and a representative example for the dimensions in scope:

| Dimension | Decisions to make | Validation |
| --- | --- | --- |
| Layout | grid, containers, spacing rhythm, alignment, density | real content at supported viewports |
| Typography | family, size, weight, line height, measure, wrapping | long headings, metadata, translated text, zoom |
| Material | radius, border, elevation, blur, texture, gradient | hierarchy and component states |
| Imagery | image, screenshot, diagram, evidence treatment | captions, crop, legibility, alternative text |
| Motion | durations, easing, entry and continuous motion | state feedback, reading access, reduced motion |
| Content | labels, voice, hierarchy, truncation | actual flows and error recovery |

Example decision form: “The evidence-heavy dashboard uses compact metadata and wider reading columns; long translated labels wrap instead of hiding their meaning.” Add measured values after testing this choice with the actual content.

## Color primitives and semantic themes

| Primitive | Authoring value | sRGB fallback | Purpose | Avoid |
| --- | --- | --- | --- | --- |
| `neutral-*` | OKLCH or other chosen space | hex | surface/text family | direct component selection |
| `brand-*` | value | hex | identity family | automatic status semantics |

Do not invent scale steps without a job. Include only supported themes:

| Semantic role | Light mapping | Dark mapping | Contract |
| --- | --- | --- | --- |
| `canvas` | token | token | page background |
| `surface-raised` | token | token | raised layer |
| `text-primary` | token | token | primary reading content |
| `text-secondary` | token | token | supporting text, still readable |
| `border-subtle` | token | token | nonessential separation |
| `brand-field` | token | token | identity field |
| `on-brand` | token | token | content on that field |
| `focus-ring` | token | token | keyboard focus indication |

Add interactive and status roles when used. Document intentional fixed-theme scenes and narrow component exceptions.

## Verified and forbidden pairs

| Foreground | Background | Ratio | Allowed use | Evidence |
| --- | --- | ---: | --- | --- |
| token and resolved value | token and resolved value | unrounded measurement | ordinary text / large text / essential UI | method, surface, state, date |

List forbidden pairs directly. For alpha, record the backing surface and composited result. A contrast measurement and a rendered visual review are different evidence.

## Interaction state matrix

| Family and theme | Rest | Hover | Active/selected | Focus-visible | Disabled |
| --- | --- | --- | --- | --- | --- |
| Primary / supported theme | foreground + background + border | pair | pair | indicator + adjacent surface | appearance + non-interactive behavior |

Repeat for existing links, controls, navigation, cards, and inputs. Include error and success feedback where present. “Uses the accent color” is incomplete.

## Responsive and motion behavior

Define what each supported viewport preserves, recomposes, collapses, or defers. Record wrapping, disclosure, target sizes, focus behavior, motion limits, and reduced-motion treatment. Keep essential information and actions available in every supported composition.

## Adoption and governance

Identify the canonical document and, when relevant, its concise `DESIGN.md` implementation contract. Record migration order, exception policy, change authority, unresolved choices, and the next validation step. Mark values implemented only after application and verification. Respect approval already granted for the requested scope.

## Release checks

Check representative rendered pages, supported themes and viewports, existing interaction states, longest realistic text and translations, keyboard use, reduced motion, and relevant export surfaces. Record contrast measurements and build/static checks, along with unavailable or incomplete validation.
