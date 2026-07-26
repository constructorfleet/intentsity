import React from "react";

import { Tooltip } from "../ds/index.js";
import { shortId } from "../lib/format.js";
import { Icon, ICONS } from "./Icon.jsx";

/**
 * Conversation and pipeline-run IDs are long enough that every place they are
 * shown has to shorten them, which used to leave no way to read one in full or
 * carry it to a log search. These render the truncated form but hand back the
 * whole value: hover to read it, click to copy it.
 */
async function writeToClipboard(value) {
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    // Clipboard API needs a secure context; HA is often served over plain HTTP
    // on a LAN, so fall back to the selection-based copy.
  }
  try {
    const field = document.createElement("textarea");
    field.value = value;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(field);
    return copied;
  } catch {
    return false;
  }
}

function useCopied(value) {
  const [copied, setCopied] = React.useState(false);
  const timer = React.useRef(null);

  React.useEffect(() => () => clearTimeout(timer.current), []);

  const copy = React.useCallback(async () => {
    if (!value) return;
    const ok = await writeToClipboard(String(value));
    if (!ok) return;
    setCopied(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), 1400);
  }, [value]);

  return [copied, copy];
}

/** Inline, truncated ID. Hover reveals the full value; click copies it. */
export function CopyId({ value, length = 12, size = 12, style }) {
  const [copied, copy] = useCopied(value);
  if (!value) return <span style={{ color: "var(--text-subtle)" }}>—</span>;

  return (
    <Tooltip content={copied ? "Copied" : value}>
      <button
        type="button"
        onClick={copy}
        aria-label={`Copy ${value}`}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 5,
          padding: "1px 5px",
          margin: "0 -5px",
          border: "none",
          borderRadius: "var(--r-sm)",
          background: copied ? "var(--accent-quiet)" : "transparent",
          color: copied ? "var(--accent-active)" : "inherit",
          fontFamily: "var(--font-mono)",
          fontSize: size,
          fontWeight: "inherit",
          cursor: "pointer",
          transition: "background var(--dur-fast) var(--ease-out)",
          ...style,
        }}
      >
        <span>{shortId(value, length)}</span>
        <Icon d={copied ? ICONS.check : ICONS.copy} size={Math.max(10, size - 1)} />
      </button>
    </Tooltip>
  );
}

/**
 * The untruncated ID, wrapped over as many lines as it needs. Used in the detail
 * panel, where there is room to show the value the short forms stand in for.
 */
export function FullId({ value }) {
  const [copied, copy] = useCopied(value);
  if (!value) return <span style={{ color: "var(--text-subtle)" }}>—</span>;

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy ${value}`}
      title={copied ? "Copied" : "Click to copy"}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 6,
        width: "100%",
        padding: "3px 5px",
        margin: "0 -5px",
        border: "none",
        borderRadius: "var(--r-sm)",
        background: copied ? "var(--accent-quiet)" : "transparent",
        color: copied ? "var(--accent-active)" : "var(--text-body)",
        fontFamily: "var(--font-mono)",
        fontSize: 12,
        lineHeight: "var(--lh-normal)",
        textAlign: "left",
        cursor: "pointer",
        transition: "background var(--dur-fast) var(--ease-out)",
      }}
    >
      <span style={{ flex: 1, minWidth: 0, wordBreak: "break-all" }}>{value}</span>
      <Icon
        d={copied ? ICONS.check : ICONS.copy}
        size={11}
        style={{ flexShrink: 0, marginTop: 2 }}
      />
    </button>
  );
}
