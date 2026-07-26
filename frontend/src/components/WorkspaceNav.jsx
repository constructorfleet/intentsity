import { BrandMark } from "./Brand.jsx";
import { Icon } from "./Icon.jsx";

/**
 * Workspace switcher for the screen toolbars.
 *
 * Two workspaces do not justify a full-height rail down the side of the page —
 * that column cost every screen ~200px of width to show two links — so the
 * switcher rides in the toolbar as a segmented control instead.
 */
export function WorkspaceNav({ workspaces, activeId, badges = {}, compact = false, onSelect }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
      <BrandMark />
      <div
        role="tablist"
        aria-label="Workspaces"
        style={{
          display: "inline-flex",
          gap: 2,
          padding: 2,
          background: "var(--surface-sunken)",
          borderRadius: "var(--r-md)",
        }}
      >
        {workspaces.map((entry) => {
          const active = entry.id === activeId;
          const badge = badges[entry.id];
          return (
            <button
              key={entry.id}
              type="button"
              role="tab"
              aria-selected={active}
              title={compact ? entry.title : undefined}
              onClick={() => onSelect(entry.id)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                padding: compact ? "5px 8px" : "5px 10px",
                border: "none",
                borderRadius: "var(--r-sm)",
                background: active ? "var(--surface-panel)" : "transparent",
                boxShadow: active ? "var(--shadow-sm)" : "none",
                color: active ? "var(--accent-active)" : "var(--text-muted)",
                fontFamily: "var(--font-sans)",
                fontSize: 12,
                fontWeight: active ? "var(--fw-semibold)" : "var(--fw-regular)",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition:
                  "background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out)",
              }}
            >
              <Icon d={entry.icon} size={13} />
              {!compact && <span>{entry.title}</span>}
              {/* A count only earns its space when there is work waiting. */}
              {Number(badge) > 0 && (
                <span
                  style={{
                    minWidth: 16,
                    padding: "0 4px",
                    borderRadius: "var(--r-pill)",
                    background: active ? "var(--accent)" : "var(--surface-hover)",
                    color: active ? "var(--text-inverse)" : "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                    fontSize: 10,
                    lineHeight: "16px",
                    textAlign: "center",
                  }}
                >
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
