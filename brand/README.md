# Brand assets

Rasterized from `DesignSystem/assets/{icon,logo}.svg` for the
[home-assistant/brands](https://github.com/home-assistant/brands) repository,
which is what puts a logo on the integration's card and config entry. They are
**not** shipped inside `custom_components/intentsity/` — the panel inlines the
SVG instead, so a copy in the component would be dead weight in every install.

Brands expects `icon.png` at 256×256, `logo.png` no more than 512 px wide, and
`@2x` variants at exactly double, under `custom_integrations/intentsity/`.

Regenerate after any change to the SVGs. `logo.svg` sets its wordmark as live
text, so the renderer needs IBM Plex Sans available or the type falls back:

```bash
rsvg-convert -w  256 -h  256 DesignSystem/assets/icon.svg -o brand/icon.png
rsvg-convert -w  512 -h  512 DesignSystem/assets/icon.svg -o brand/icon@2x.png
rsvg-convert -w  512           DesignSystem/assets/logo.svg -o brand/logo.png
rsvg-convert -w 1024           DesignSystem/assets/logo.svg -o brand/logo@2x.png
```
