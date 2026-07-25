// Single-path-set icon primitive, matching the `Ico` helper the design system's
// ui_kits use: paths are separated by `|` in a 16x16 viewBox.
export function Icon({ d, size = 14, ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {d.split("|").map((path, index) => (
        <path key={index} d={path} />
      ))}
    </svg>
  );
}

export const ICONS = {
  waveform: "M2 8h12M8 2v12",
  list: "M2 4h12M2 8h12M2 12h8",
  search: "M7 2a5 5 0 100 10 5 5 0 000-10zM11.5 11.5L14 14",
  chevronLeft: "M10 3L5 8l5 5",
  chevronRight: "M6 3l5 5-5 5",
  chevronDown: "M3 6l5 5 5-5",
  refresh: "M13 8a5 5 0 11-1.6-3.7|M13 2v3h-3",
  download: "M8 2v8M5 7l3 3 3-3|M3 13h10",
  trash: "M3 5h10|M6.5 5V3.5h3V5|M5 5l.6 8h4.8L11 5",
  restore: "M3 8a5 5 0 105-5|M3 5v3h3",
  mic: "M8 2a2 2 0 012 2v3a2 2 0 11-4 0V4a2 2 0 012-2z|M4 8a4 4 0 008 0|M8 12v2",
  theme: "M8 2v2|M8 12v2|M2 8h2|M12 8h2|M8 5.5A2.5 2.5 0 108 10.5a2.5 2.5 0 000-5z",
  plug: "M6 2v4|M10 2v4|M4 6h8v2a4 4 0 01-8 0V6z|M8 12v2",
  check: "M3 8.5L6 11.5 13 4.5",
  pencil: "M11.5 2.5l2 2L6 12l-3 1 1-3 7.5-7.5z",
  save: "M3 3h8l2 2v8H3V3z|M5.5 3v3h5V3|M5.5 13v-4h5v4",
  plus: "M3 8h10M8 3v10",
};
