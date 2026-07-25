// Design-system stylesheet for the panel's shadow root, assembled in the order
// DesignSystem/styles.css imports the token files.
//
// Two deliberate departures from the browser-page version of the design system:
//
//  * tokens/fonts.css is omitted. An `@import url(...)` inside a shadow root is
//    inert, so the webfont is linked into document.head instead (loadFonts in
//    panel.jsx).
//  * `:root` is rewritten to `:host`. Custom properties declared on :root would
//    still inherit into the shadow tree, but declaring them there means editing
//    Home Assistant's global scope; :host keeps every token local to the panel.
import colors from "./tokens/colors.css";
import motion from "./tokens/motion.css";
import radius from "./tokens/radius.css";
import reset from "./tokens/reset.css";
import semantic from "./tokens/semantic.css";
import shadows from "./tokens/shadows.css";
import spacing from "./tokens/spacing.css";
import typography from "./tokens/typography.css";

export const FONT_HREF =
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700" +
  "&family=IBM+Plex+Mono:wght@400;500;600&display=swap";

const SHEETS = [reset, colors, typography, spacing, radius, shadows, motion, semantic];

export const tokensCss = SHEETS.join("\n").replace(/:root\b/g, ":host");
