# Repository design

The repository presentation follows [PIP](https://design.whitekiwi.link/) and its [source of truth](https://github.com/WhiteKiwi/kiwi-design-system/blob/main/packages/tokens/src/theme.css).

## Adopted values

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | paper `#F4F5EF` | carbon `#0E100E` |
| Text | ink `#11140F` | chalk `#F1F4EB` |
| One accent headline | deep `#3C6000` | signal `#C6FF4A` |
| Supporting label | ash `#62685E` | fog `#A5AB9F` |

The cover is a static editorial illustration, not a fake UI. It uses no remote font, script, animation, or tracking image. Main text, installation commands, links, versions, and CI status remain accessible Markdown outside the image. GitHub owns the rest of the page's typography and background.

The SVG has an explicit viewBox, title, description, light/dark alternatives, and a light fallback. At 320px wide, the 104px source headline scales to 26px. Review both themes and actual rendered width before changing copy. These assets use semantic values from PIP; they do not impose the WhiteKiwi palette on the portable design skills.

Source reviewed: PIP v0.3, revision `99fa87c6631874084773ced3893e054dd9336081`, 2026-09-30. See the [repository surface contract](https://github.com/WhiteKiwi/kiwi-design-system/blob/main/docs/repository-surfaces.md) for future adaptations.
