/**
 * The draggable divider between two panes. Pair it with `useResizableColumn`,
 * which supplies every prop this needs via `handleProps`.
 *
 * It is a real separator, not decoration: focusable, labelled, and reporting the
 * width it controls so a keyboard or screen-reader user can move it too.
 */
export function Resizer({ label, dragging = false, ...rest }) {
  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={label}
      tabIndex={0}
      className="ist-resizer"
      data-dragging={dragging ? "true" : "false"}
      title="Drag to resize · double-click to reset"
      {...rest}
    />
  );
}
