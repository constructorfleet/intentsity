import React from "react";

import { BrandMark } from "./components/Brand.jsx";
import { Icon, ICONS } from "./components/Icon.jsx";
import { IconButton, Sidebar, SidebarItem, SidebarSection, Toast, Tooltip } from "./ds/index.js";
import { IntentsityApi } from "./lib/api.js";
import { useToasts } from "./lib/hooks.js";
import { Annotator } from "./screens/Annotator.jsx";
import { Trainer } from "./screens/Trainer.jsx";

const VERSION = typeof __INTENTSITY_VERSION__ === "string" ? __INTENTSITY_VERSION__ : "dev";

const WORKSPACES = [
  { id: "wake", title: "Wake word", icon: ICONS.waveform, screen: Annotator },
  { id: "intent", title: "Intent training", icon: ICONS.list, screen: Trainer },
];

const THEME_STORAGE_KEY = "intentsity.theme";
const RAIL_STORAGE_KEY = "intentsity.sidebarCollapsed";

/** Two workspaces do not need 232px of chrome, so the rail is collapsible. */
function useCollapsedRail() {
  const [collapsed, setCollapsed] = React.useState(() => {
    try {
      return window.localStorage.getItem(RAIL_STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });

  const toggle = React.useCallback(() => {
    setCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(RAIL_STORAGE_KEY, next ? "1" : "0");
      } catch {
        // Private browsing: an unsaved preference is not worth failing over.
      }
      return next;
    });
  }, []);

  return [collapsed, toggle];
}

/** Follow Home Assistant's dark mode unless the reviewer has picked a theme. */
function useTheme(hass) {
  const [override, setOverride] = React.useState(() => {
    try {
      return window.localStorage.getItem(THEME_STORAGE_KEY);
    } catch {
      return null;
    }
  });

  const theme = override ?? (hass?.themes?.darkMode ? "dark" : "light");

  const toggle = React.useCallback(() => {
    setOverride(theme === "dark" ? "light" : "dark");
  }, [theme]);

  React.useEffect(() => {
    if (!override) return;
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, override);
    } catch {
      // Private browsing: an unsaved preference is not worth failing over.
    }
  }, [override]);

  return [theme, toggle];
}

/**
 * Read one of the integration's queue sensors out of the state machine. Matched
 * by substring because the entity ID picks up a prefix when the user renames it.
 */
const entityCount = (hass, slug) => {
  const entity = Object.values(hass?.states ?? {}).find(
    (state) => state.entity_id.startsWith("sensor.") && state.entity_id.includes(slug),
  );
  const value = Number(entity?.state);
  return Number.isFinite(value) ? value : undefined;
};

export function App({ hass, narrow }) {
  const [workspaceId, setWorkspaceId] = React.useState(WORKSPACES[0].id);
  const [theme, toggleTheme] = useTheme(hass);
  const [railCollapsed, toggleRail] = useCollapsedRail();
  const { toasts, push, dismiss } = useToasts();

  // The API wrapper reads hass lazily, so it only needs rebuilding when the
  // websocket connection itself is replaced.
  const api = React.useMemo(() => new IntentsityApi(hass), [hass?.connection]);
  React.useEffect(() => {
    api.hass = hass;
  }, [api, hass]);

  const onError = React.useCallback(
    (error) => {
      const message = error?.message ?? String(error);
      push("error", "Request failed", message);
      // Surfacing in the console too keeps stack traces available for bug reports.
      console.error("[intentsity]", error);
    },
    [push],
  );

  const workspace = WORKSPACES.find((entry) => entry.id === workspaceId) ?? WORKSPACES[0];
  const Screen = workspace.screen;

  const badges = {
    wake: entityCount(hass, "unlabeled_wake_clips"),
    intent: entityCount(hass, "uncorrected_assist_chats"),
  };

  return (
    <div
      data-theme={theme}
      style={{
        display: "flex",
        height: "100%",
        background: "var(--surface-app)",
        color: "var(--text-body)",
        fontFamily: "var(--font-sans)",
        fontSize: 13,
      }}
    >
      {!narrow && (
        <Sidebar width={196} collapsed={railCollapsed}>
          <div
            style={{
              padding: railCollapsed ? "12px 6px" : "14px 8px 14px 12px",
              display: "flex",
              alignItems: "center",
              justifyContent: railCollapsed ? "center" : "flex-start",
              gap: 8,
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <BrandMark />
            {/* The wordmark is live text, not `logo.svg`: the design system sets
                it in dark ink, which vanishes on the dark theme. */}
            {!railCollapsed && (
              <>
                <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: -0.02 }}>
                  Intent<span style={{ color: "var(--brand-500)" }}>s</span>ity
                </span>
                <div style={{ flex: 1 }} />
                <Tooltip content="Collapse sidebar">
                  <IconButton size="sm" aria-label="Collapse sidebar" onClick={toggleRail}>
                    <Icon d={ICONS.chevronLeft} size={12} />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </div>
          {railCollapsed && (
            <div style={{ display: "flex", justifyContent: "center", padding: "8px 0 0" }}>
              <Tooltip content="Expand sidebar" placement="right">
                <IconButton size="sm" aria-label="Expand sidebar" onClick={toggleRail}>
                  <Icon d={ICONS.chevronRight} size={12} />
                </IconButton>
              </Tooltip>
            </div>
          )}
          <SidebarSection title={railCollapsed ? undefined : "Workspaces"}>
            {WORKSPACES.map((entry) => (
              <SidebarItem
                key={entry.id}
                icon={<Icon d={entry.icon} />}
                active={entry.id === workspace.id}
                badge={badges[entry.id]}
                onClick={() => setWorkspaceId(entry.id)}
              >
                {entry.title}
              </SidebarItem>
            ))}
          </SidebarSection>
          <div
            style={{
              marginTop: "auto",
              padding: railCollapsed ? "10px 0" : "10px 12px",
              borderTop: "1px solid var(--border-subtle)",
              display: "flex",
              alignItems: "center",
              justifyContent: railCollapsed ? "center" : "flex-start",
              gap: 8,
              fontSize: 12,
              color: "var(--text-muted)",
            }}
          >
            {!railCollapsed && (
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    color: "var(--text-body)",
                    fontSize: 12,
                    fontWeight: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {hass?.user?.name ?? "Home Assistant"}
                </div>
                <div style={{ fontSize: 11, fontFamily: "var(--font-mono)" }}>v{VERSION}</div>
              </div>
            )}
            <Tooltip
              content={theme === "dark" ? "Switch to light" : "Switch to dark"}
              placement={railCollapsed ? "right" : "top"}
            >
              <IconButton size="sm" aria-label="Toggle theme" onClick={toggleTheme}>
                <Icon d={ICONS.theme} size={12} />
              </IconButton>
            </Tooltip>
          </div>
        </Sidebar>
      )}

      <Screen api={api} hass={hass} onError={onError} onNotify={push} />

      <div
        style={{
          position: "fixed",
          bottom: 16,
          right: 16,
          zIndex: 300,
          display: "flex",
          flexDirection: "column",
          gap: 8,
          alignItems: "flex-end",
        }}
      >
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            tone={toast.tone}
            title={toast.title}
            description={toast.description}
            onDismiss={() => dismiss(toast.id)}
          />
        ))}
      </div>
    </div>
  );
}
