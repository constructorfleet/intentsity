// The Intentsity mark, inlined from the design system's asset so the sidebar
// renders it crisply at any density and without a network request.
//
// Only the icon is used here: `logo.svg` sets its wordmark in dark ink on a
// transparent field, which disappears against the dark theme. The wordmark
// beside this glyph is live text instead, so it inherits `--text-body`.
import iconSvg from "../ds/assets/icon.svg";

// The source is a 512px square with hard-coded width/height. Strip those from
// the opening tag only — the artwork's own <rect> elements are sized in user
// units and must keep theirs — and let the wrapper size it, since an <svg> with
// neither dimension defaults to filling its container. The gradient id is
// namespaced because `bg` is too generic to leave in a shared document.
//
// The art carries its own 112/512 corner radius, so nothing here clips it.
const markup = iconSvg
  .replace(/<svg/, '<svg style="width:100%;height:100%;display:block"')
  .replace(/<svg[^>]*>/, (tag) => tag.replace(/\s(?:width|height)="\d+"/g, ""))
  .replace(/"bg"/g, '"intentsity-mark-bg"')
  .replace(/url\(#bg\)/g, "url(#intentsity-mark-bg)");

export function BrandMark({ size = 18 }) {
  return (
    <span
      style={{ display: "inline-flex", width: size, height: size, flex: "0 0 auto" }}
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: markup }}
    />
  );
}
