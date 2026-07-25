# Intentsity Design System

Design system for **Intentsity** — internal tooling for training personal voice assistants. Two product surfaces:

- **Wake Word Annotator.** Reviewers cycle through candidate audio clips flagged by the on-device wake detector and label each as **True Positive · True Negative · False Positive · False Negative · Background noise**. Labels feed back into wake-model fine-tuning.
- **Intent Trainer.** Reviewers open real captured conversations, edit tool-call arguments and assistant responses, and mark sessions as golden examples for LLM fine-tuning.

Both are keyboard-first, dense, and read like professional engineering software (Linear, Splice, Audacity, DAWs), not consumer apps.

> **Source materials:** none were attached. The brand, name, and taxonomy above were derived from the user's product description alone. Wherever this design system commits to a specific value (color hex, font, iconography, layout), that value is an *interpretation* and is called out below so it can be corrected.

---

## Content fundamentals — voice & copy

- **Tone:** engineering-direct. "127 clips queued." "Precision rose 1.4%." Never marketing-inflected, never celebratory.
- **Person:** third-person or imperative. Not "you", not "we". "Save labels", not "Save your labels".
- **Casing:** **Sentence case for buttons and labels** ("Save labels", "Queue fine-tune"). Title Case reserved for section headers on marketing surfaces (none in the current product). UPPERCASE for eyebrow labels only (`SESSION`, `ARGUMENTS`) with `--tracking-caps`.
- **Emoji:** never in product UI. Not in toasts, not in empty states, not in comments. Tools like this are used all day; emoji become noise.
- **Numbers:** always in the mono family (Plex Mono). Fixed-precision — precision `0.982` not `98%`, duration `1.24s` not `about a second`. Deltas signed: `+0.014`, `−0.006`.
- **IDs and versions:** mono, prefixed. `c_9f2b04a1` (clip), `s_2a4b` (session), `wake-atlas-v3.2.1` (model).
- **Errors:** state the fact, then the recovery. "Model deploy failed — commit `a3f9` not signed. **Re-sign and retry.**"

Examples that fit / examples that break the brand are in `cards/brand-voice.html`.

---

## Visual foundations

**Colors.** Cool graphite neutrals with a **signal-cyan** brand (`--brand-500 #12a394`) and a **five-color annotation palette** that IS the semantic palette — TP emerald, TN blue, FP red, FN amber, BG violet. Same colors drive Toast tones and status dots. Full palette in `tokens/colors.css`.

**Typography.** `IBM Plex Sans` for UI, `IBM Plex Mono` for data, IDs, JSON, and keyboard hints. Mono is used *heavily* — it's how you tell at a glance that a value is machine-precise. **⚠︎ Substitution flag:** no source assets were provided; Plex was chosen for its engineering/tooling associations. If the real product uses another face (Söhne, Inter, SF Pro, GT America…) please send the font files and this pair will be swapped.

**Spacing.** 14-step ramp on a 2px baseline — 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96.

**Radii.** Small and functional: `sm 3`, `md 5`, `lg 8`, `xl 12`, `2xl 16`, `pill`. **No large radii on cards.** Panels stay square-ish; only avatars and badges get `--r-pill`.

**Elevation.** Mostly flat. Panels are separated by 1px borders (`--border-subtle`), not shadows. Shadows appear only on true overlays: dropdowns, tooltips, dialogs, toasts. No inner glows. No colored shadows.

**Borders.** `--border-subtle` for panel/row separation, `--border-default` for inputs, `--border-strong` for check/radio idle. Focus rings are a 3px `--brand-500`-at-28% halo, never a solid outline. No colored left-border-only cards.

**Backgrounds.** No gradients. No photo backdrops. No hand-drawn illustrations. No repeating patterns. The one gradient this system uses is the **transparent overlay for dialogs** (`--surface-overlay` at 55% + 4px backdrop blur). Full-bleed color appears only in `thumbnail.html`.

**Animation.** Fast and unfussy. `--dur-fast 140ms` for hovers, `--dur-med 220ms` for panel/state changes. Easing is `cubic-bezier(.2,.7,.2,1)`. **No bounces**, no springs (except a rare micro-detail via `--ease-spring` — never on layout). Buttons scale to `.98` on press. Intentsity playhead is a plain interval, not a tween.

**Hover / press.** Hover = one step warmer surface (`--surface-hover`), no color shift. Press = next step (`--surface-active`) *plus* `scale(.98)` on buttons. Ghost buttons rely entirely on background change; they never gain a border on hover.

**Transparency & blur.** Only for dialog overlays. Sidebars, popovers, tooltips are **fully opaque** — this is professional software; users need reliable contrast against arbitrary content.

**Iconography.** Currently uses **inline stroke SVG** at 1.5px, 14–16px viewbox, drawn in place — see the `Ico` helpers in the UI kit JSX. **No icon font is bundled yet.** The nearest CDN match if you need more coverage is **Lucide** (`https://unpkg.com/lucide-static`), same 1.5px stroke weight. Substitution flag — please supply the real icon set if one exists.

**Imagery.** None. This is a data tool. If a marketing surface is ever needed, imagery should be **cool-toned, high-contrast, subtly grainy** — waveform close-ups, oscilloscope shots, studio-monitor macros — not people or lifestyle photography.

**Cards.** 1px `--border-subtle`, `--r-lg (8px)`, `--surface-panel` fill, no shadow by default. Header strip has its own 1px bottom border; footer strip is `--surface-sunken`.

**Layout rules.** Fixed left sidebar (232px), fixed top toolbar (48px), everything else flexes. Content zones separated by 1px borders — never gaps. Right inspector panels are 280px. Content max-widths only exist inside long-form docs (none in the current product).

---

## Iconography

- Currently: inline stroke SVGs, 1.5px stroke, no fill, 14–16px canvas, rounded joins.
- No emoji anywhere in product UI.
- No unicode-as-icon (no ▶ ♫ ★). The one exception is the select chevron (`▾`) because a stroked SVG at 10px is illegible.
- **Substitution — please confirm:** if your product uses a specific icon set (Lucide, Phosphor, Radix, custom), send it and it'll be swapped in.

---

## Assets

- **No logo was supplied.** The wordmark used across the system is `Intentsity` set in Plex Sans 700 tight, paired with a five-bar waveform glyph rendered inline. Do **not** treat this as a real logo — see `cards/brand-wordmark.html`. Please supply real mark files.

---

## Components

Reusable primitives. All exported on `window.WaveformDesignSystem_606875` after `_ds_bundle.js` loads (the compiled namespace still reflects the initial project name).

**Forms** — Button, IconButton, Input, Textarea, Select, Checkbox, Radio, RadioGroup, Switch
**Feedback** — Badge, LabelChip, Tag, Tooltip, Toast, Dialog
**Data** — Card, Tabs, KeyValue
**Navigation** — Sidebar, SidebarSection, SidebarItem, Toolbar, ToolbarSeparator, ToolbarSpacer
**Domain (voice-training specific)** — Waveform, ConversationTurn, ToolInvocation, StatCell, Kbd

### Intentional additions
- **LabelChip** and `WAKE_LABELS` — no source was provided, but the five-label wake taxonomy IS the product; a dedicated chip primitive keeps consumers from re-implementing it with generic buttons.
- **Waveform** — same reasoning; audio review is the primary interaction.
- **ConversationTurn / ToolInvocation** — same for the intent-training surface.
- **StatCell**, **Kbd** — used in enough places (session dashboards, keyboard hints) to earn primitives.

Everything else is a standard baseline set (Button, Input, Select, …) because no source library was provided.

---

## Index

- `readme.md` — this file
- `SKILL.md` — agent-skill entry point (for Claude Code / other agents)
- `thumbnail.html` — homepage tile
- `styles.css` — one file to link; imports everything below
- `tokens/` — `colors.css`, `typography.css`, `spacing.css`, `radius.css`, `shadows.css`, `motion.css`, `semantic.css`, `reset.css`, `fonts.css`
- `cards/` — foundation specimen cards for the Design System tab
- `components/` — reusable primitives (`forms/`, `feedback/`, `data/`, `nav/`, `domain/`), each with `.jsx`, `.d.ts`, `.prompt.md`, and one `*.card.html`
- `ui_kits/wake_word/` — Wake Word Annotator recreation (index + Annotator.jsx)
- `ui_kits/intent_training/` — Intent Trainer recreation (index + Trainer.jsx)

---

## Caveats & things to confirm

1. **No source materials were attached** — this is designed from the product description alone. Names, taxonomy, fonts, colors, and layout are all interpretations.
2. **Fonts substituted** — IBM Plex Sans + Mono via Google Fonts. Replace with real product fonts when supplied.
3. **No logo** — wordmark is plain type + a generic 5-bar glyph.
4. **No icon set** — inline stroke SVGs only; connect Lucide or your own icons.
5. **Dark mode** shipped as opt-in via `[data-theme="dark"]` — both UI kits include a theme toggle in the sidebar footer for verification.
