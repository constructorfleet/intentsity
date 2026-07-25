import React from "react";

import { Icon, ICONS } from "../components/Icon.jsx";
import {
  Badge,
  Button,
  Card,
  IconButton,
  Input,
  Kbd,
  KeyValue,
  LabelChip,
  Select,
  StatCell,
  Switch,
  Tabs,
  Toolbar,
  ToolbarSeparator,
  ToolbarSpacer,
  Tooltip,
  WAKE_LABELS,
  Waveform,
} from "../ds/index.js";
import {
  formatConfidence,
  formatDateTime,
  formatRate,
  formatSeconds,
  formatTime,
} from "../lib/format.js";
import { useKeyboard, useSubscription } from "../lib/hooks.js";

const PAGE_SIZE = 50;
const NOISE_SECONDS = 5;

// Each queue maps to a server-side filter, so paging never has to be corrected
// on the client.
const TABS = [
  {
    value: "unlabeled",
    label: "Unlabeled",
    countKey: "unlabeled_total",
    filters: { label: "unlabeled" },
  },
  {
    value: "labeled",
    label: "Labeled",
    countKey: "labeled_total",
    filters: { labeled_only: true },
  },
  {
    value: "deleted",
    label: "Deleted",
    countKey: "deleted_total",
    filters: { deleted_only: true },
  },
];

const LABEL_BY_ID = new Map(WAKE_LABELS.map((label) => [label.id, label]));
const SHORTCUTS = new Map(WAKE_LABELS.map((label) => [label.key, label.id]));

const PlayIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
    <path d="M3 2l7 4-7 4V2z" />
  </svg>
);

const PauseIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
    <rect x="3" y="2" width="2" height="8" />
    <rect x="7" y="2" width="2" height="8" />
  </svg>
);

const labelTone = (label) => LABEL_BY_ID.get(label)?.tone ?? "neutral";

/** Client-side text filter over the fields shown in the clip row. */
function matchesQuery(clip, query) {
  if (!query) return true;
  const haystack = [
    clip.filename,
    clip.assistant_id,
    clip.wake_word,
    clip.label,
    formatTime(clip.timestamp),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

export function Annotator({ api, onError, onNotify }) {
  const [tab, setTab] = React.useState("unlabeled");
  const [assistantFilter, setAssistantFilter] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [autoAdvance, setAutoAdvance] = React.useState(true);

  const [response, setResponse] = React.useState(null);
  const [selectedId, setSelectedId] = React.useState(null);
  const [status, setStatus] = React.useState(null);
  const [busy, setBusy] = React.useState(false);

  const [audioUrl, setAudioUrl] = React.useState(null);
  const [audioVersion, setAudioVersion] = React.useState(0);
  const [playing, setPlaying] = React.useState(false);
  const [playhead, setPlayhead] = React.useState(0);
  const audioRef = React.useRef(null);

  const activeTab = TABS.find((entry) => entry.value === tab) ?? TABS[0];

  const filters = React.useMemo(
    () => ({
      limit: PAGE_SIZE,
      assistant_id: assistantFilter || null,
      ...activeTab.filters,
    }),
    [activeTab.filters, assistantFilter],
  );

  const subscribe = React.useCallback(
    (payload, handler) => api.subscribeClips(payload, handler),
    [api],
  );

  useSubscription(subscribe, filters, setResponse, onError);

  const refreshStatus = React.useCallback(() => {
    api.assistants().then(setStatus).catch(onError);
  }, [api, onError]);

  React.useEffect(refreshStatus, [refreshStatus]);

  const clips = React.useMemo(
    () => (response?.clips ?? []).filter((clip) => matchesQuery(clip, query)),
    [response, query],
  );

  const selectedIndex = React.useMemo(() => {
    const index = clips.findIndex((clip) => clip.id === selectedId);
    return index === -1 ? 0 : index;
  }, [clips, selectedId]);

  const clip = clips[selectedIndex] ?? null;

  // Keep a valid selection as the live subscription reshuffles the queue.
  React.useEffect(() => {
    if (!clips.length) {
      if (selectedId !== null) setSelectedId(null);
      return;
    }
    if (!clips.some((entry) => entry.id === selectedId)) {
      setSelectedId(clips[Math.min(selectedIndex, clips.length - 1)].id);
    }
  }, [clips, selectedId, selectedIndex]);

  const select = React.useCallback((clipId) => {
    setSelectedId(clipId);
    setPlayhead(0);
    setPlaying(false);
  }, []);

  const step = React.useCallback(
    (delta) => {
      if (!clips.length) return;
      const next = Math.min(clips.length - 1, Math.max(0, selectedIndex + delta));
      select(clips[next].id);
    },
    [clips, select, selectedIndex],
  );

  // Clip audio needs a signed URL: the view requires auth, and <audio> sends no
  // Authorization header.
  const clipId = clip?.id ?? null;
  const clipAudioPath = clip?.audio_url ?? null;
  React.useEffect(() => {
    if (!clipAudioPath) {
      setAudioUrl(null);
      return undefined;
    }
    let cancelled = false;
    setAudioUrl(null);
    api
      .signPath(`${clipAudioPath}?v=${audioVersion}`)
      .then((signed) => {
        if (!cancelled) setAudioUrl(signed);
      })
      .catch((error) => {
        if (!cancelled) onError(error);
      });
    return () => {
      cancelled = true;
    };
  }, [api, audioVersion, clipAudioPath, onError]);

  React.useEffect(() => {
    setPlayhead(0);
    setPlaying(false);
  }, [clipId]);

  React.useEffect(() => {
    const element = audioRef.current;
    if (!element) return;
    if (playing) {
      element.play().catch((error) => {
        setPlaying(false);
        onError(error);
      });
    } else {
      element.pause();
    }
  }, [playing, onError, audioUrl]);

  const applyLabel = React.useCallback(
    async (label) => {
      if (!clip) return;
      setBusy(true);
      try {
        await api.labelClips([clip.id], label);
        onNotify("success", `Labeled ${LABEL_BY_ID.get(label)?.short ?? label}`, clip.filename);
        if (autoAdvance) {
          // On the unlabeled queue the clip drops out of the list, so the row
          // that slides into this position is already the next one to review;
          // selecting it by ID now avoids a flash of the wrong clip.
          setSelectedId(clips[selectedIndex + 1]?.id ?? null);
        }
      } catch (error) {
        onError(error);
      } finally {
        setBusy(false);
      }
    },
    [api, autoAdvance, clip, clips, onError, onNotify, selectedIndex],
  );

  const toggleDeleted = React.useCallback(async () => {
    if (!clip) return;
    const restore = Boolean(clip.deleted_at);
    setBusy(true);
    try {
      await api.tombstoneClips([clip.id], restore);
      onNotify("info", restore ? "Clip restored" : "Clip deleted", clip.filename);
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }, [api, clip, onError, onNotify]);

  const repairClipRate = React.useCallback(async () => {
    if (!clip) return;
    setBusy(true);
    setPlaying(false);
    try {
      const result = await api.repairClipRate(clip.id);
      if (result.repaired > 0) {
        setAudioVersion((value) => value + 1);
        onNotify("success", "Repaired WAV header", clip.filename);
      } else {
        onNotify("warn", "Clip was not changed", clip.filename);
      }
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }, [api, clip, onError, onNotify]);

  const captureNoise = React.useCallback(async () => {
    const assistantId = assistantFilter || status?.assistants?.[0]?.assistant_id;
    if (!assistantId) {
      onNotify("warn", "No assistant is streaming audio", "Start a satellite, then try again.");
      return;
    }
    setBusy(true);
    try {
      const result = await api.captureNoise(assistantId, NOISE_SECONDS);
      onNotify("success", "Captured background noise", result.filename);
      refreshStatus();
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }, [api, assistantFilter, onError, onNotify, refreshStatus, status]);

  const downloadArchive = React.useCallback(async () => {
    // Export the labeled set regardless of the visible tab: unlabeled and deleted
    // clips are not training data.
    const params = new URLSearchParams({ limit: "1000", labeled_only: "true" });
    if (assistantFilter) params.set("assistant_id", assistantFilter);
    try {
      const signed = await api.signPath(`/api/intentsity/clips/archive?${params}`, 60);
      window.open(signed, "_blank");
    } catch (error) {
      onError(error);
    }
  }, [api, assistantFilter, onError]);

  useKeyboard(
    React.useCallback(
      (event) => {
        if (event.metaKey || event.ctrlKey || event.altKey) return;
        const label = SHORTCUTS.get(event.key);
        if (label) {
          event.preventDefault();
          applyLabel(label);
          return;
        }
        if (event.key === " ") {
          event.preventDefault();
          setPlaying((value) => !value);
          return;
        }
        if (event.key === "j" || event.key === "ArrowDown") {
          event.preventDefault();
          step(1);
        } else if (event.key === "k" || event.key === "ArrowUp") {
          event.preventDefault();
          step(-1);
        }
      },
      [applyLabel, step],
    ),
  );

  const unlabeledTotal = response?.unlabeled_total ?? 0;
  const labeledTotal = response?.labeled_total ?? 0;

  const assistantOptions = [
    { value: "", label: "All assistants" },
    ...(status?.assistants ?? []).map((assistant) => ({
      value: assistant.assistant_id,
      label: assistant.assistant_id,
    })),
  ];

  const duration = clip?.duration ?? 0;
  const transports = [
    status?.udp_running ? `UDP :${status.udp_port}` : null,
    status?.mqtt_connected ? "MQTT" : null,
  ].filter(Boolean);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <Toolbar>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Wake word</span>
        <span style={{ fontSize: 12, color: "var(--text-subtle)" }}>/</span>
        <span style={{ fontWeight: 600, fontSize: 14 }}>Clip review</span>
        <Badge tone="brand">{unlabeledTotal} unlabeled</Badge>
        <ToolbarSeparator />
        <Input
          size="sm"
          placeholder="Filter by device, label, time…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          style={{ width: 260 }}
          prefix={<Icon d={ICONS.search} size={12} />}
        />
        <Select
          size="sm"
          options={assistantOptions}
          value={assistantFilter}
          onChange={(event) => setAssistantFilter(event.target.value)}
          style={{ width: 170 }}
        />
        <ToolbarSpacer />
        <Switch checked={autoAdvance} onChange={setAutoAdvance} label="Auto-advance" />
        <ToolbarSeparator />
        <Tooltip content={`Save the last ${NOISE_SECONDS}s as background noise`}>
          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            onClick={captureNoise}
            iconLeft={<Icon d={ICONS.mic} size={12} />}
          >
            Capture noise
          </Button>
        </Tooltip>
        <Button
          size="sm"
          variant="primary"
          onClick={downloadArchive}
          iconLeft={<Icon d={ICONS.download} size={12} />}
        >
          Export clips
        </Button>
      </Toolbar>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <div
          style={{
            width: 320,
            minWidth: 320,
            borderRight: "1px solid var(--border-subtle)",
            background: "var(--surface-panel)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              padding: "8px 8px 0",
              minWidth: 0,
              overflow: "hidden",
            }}
          >
            <Tabs
              size="sm"
              value={tab}
              onChange={setTab}
              tabs={TABS.map((entry) => ({
                value: entry.value,
                label: entry.label,
                count: response?.[entry.countKey],
              }))}
            />
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {clips.length === 0 && (
              <div style={{ padding: 20, fontSize: 13, color: "var(--text-muted)" }}>
                {response ? "No clips match these filters." : "Loading clips…"}
              </div>
            )}
            {clips.map((entry) => {
              const active = entry.id === clip?.id;
              const tone = entry.label && entry.label !== "unlabeled" ? labelTone(entry.label) : null;
              const toneColor = tone
                ? `var(--${tone === "bgnoise" ? "bg" : tone}-500)`
                : "transparent";
              return (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => select(entry.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    width: "100%",
                    padding: "10px 12px",
                    border: "none",
                    textAlign: "left",
                    background: active ? "var(--accent-quiet)" : "transparent",
                    borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                    borderBottom: "1px solid var(--border-subtle)",
                    cursor: "pointer",
                    color: "var(--text-body)",
                    opacity: entry.deleted_at ? 0.55 : 1,
                  }}
                >
                  <div
                    style={{ width: 3, alignSelf: "stretch", background: toneColor, borderRadius: 2 }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: 12,
                          fontWeight: 500,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {entry.filename}
                      </span>
                      {tone && (
                        <Badge tone={tone} style={{ height: 16, padding: "0 6px", fontSize: 9 }}>
                          {LABEL_BY_ID.get(entry.label)?.short}
                        </Badge>
                      )}
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        fontSize: 11,
                        color: "var(--text-muted)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      <span>{formatSeconds(entry.duration)}</span>
                      <span>·</span>
                      <span>{entry.assistant_id ?? "unknown"}</span>
                      <span>·</span>
                      <span>{formatTime(entry.timestamp)}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div
          style={{
            flex: 1,
            padding: 20,
            overflow: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            minWidth: 0,
          }}
        >
          {!clip && (
            <Card title="Nothing selected">
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                Clips appear here as satellites report wake-word detections.
                {status && transports.length === 0 && (
                  <>
                    {" "}
                    No audio transport is active — enable UDP or MQTT in the integration options.
                  </>
                )}
              </div>
            </Card>
          )}

          {clip && (
            <>
              <Card padded={false}>
                <div
                  style={{
                    padding: "14px 18px",
                    borderBottom: "1px solid var(--border-subtle)",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}
                    >
                      <span
                        style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 600 }}
                      >
                        {clip.filename}
                      </span>
                      <Badge mono>{formatSeconds(clip.duration)}</Badge>
                      {clip.confidence != null && (
                        <Badge tone="brand">conf {formatConfidence(clip.confidence)}</Badge>
                      )}
                      {clip.deleted_at && <Badge tone="fp">deleted</Badge>}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {clip.assistant_id ?? "unknown"} · {formatDateTime(clip.timestamp)}
                    </div>
                  </div>
                  <Tooltip content="Rewrite legacy 48 kHz / 32-bit stereo metadata to 16 kHz / 16-bit mono without resampling">
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={busy}
                      onClick={repairClipRate}
                      iconLeft={<Icon d={ICONS.refresh} size={12} />}
                    >
                      Change sample rate
                    </Button>
                  </Tooltip>
                  <Tooltip content={clip.deleted_at ? "Restore clip" : "Delete clip"}>
                    <IconButton
                      aria-label={clip.deleted_at ? "Restore clip" : "Delete clip"}
                      disabled={busy}
                      onClick={toggleDeleted}
                    >
                      <Icon d={clip.deleted_at ? ICONS.restore : ICONS.trash} />
                    </IconButton>
                  </Tooltip>
                  <IconButton aria-label="Previous clip" onClick={() => step(-1)}>
                    <Icon d={ICONS.chevronLeft} />
                  </IconButton>
                  <IconButton aria-label="Next clip" onClick={() => step(1)}>
                    <Icon d={ICONS.chevronRight} />
                  </IconButton>
                </div>

                <div style={{ padding: "22px 22px 14px" }}>
                  <Waveform
                    bars={clip.peaks?.length ? clip.peaks : undefined}
                    seed={clip.id ?? 42}
                    samples={96}
                    playhead={playhead}
                    height={96}
                    onScrub={(position) => {
                      setPlayhead(position);
                      const element = audioRef.current;
                      if (element && Number.isFinite(element.duration)) {
                        element.currentTime = position * element.duration;
                      }
                    }}
                  />
                  {audioUrl && (
                    <audio
                      ref={audioRef}
                      src={audioUrl}
                      preload="metadata"
                      onTimeUpdate={(event) => {
                        const element = event.currentTarget;
                        if (element.duration > 0) {
                          setPlayhead(element.currentTime / element.duration);
                        }
                      }}
                      onEnded={() => {
                        setPlaying(false);
                        setPlayhead(0);
                      }}
                      style={{ display: "none" }}
                    />
                  )}
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 14 }}
                  >
                    <IconButton
                      variant="primary"
                      size="lg"
                      aria-label={playing ? "Pause" : "Play"}
                      disabled={!audioUrl}
                      onClick={() => setPlaying((value) => !value)}
                    >
                      {playing ? <PauseIcon /> : <PlayIcon />}
                    </IconButton>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 13,
                        color: "var(--text-muted)",
                      }}
                    >
                      {formatSeconds(playhead * duration)} / {formatSeconds(duration)}
                    </div>
                    <div
                      style={{
                        marginLeft: "auto",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: 12,
                        color: "var(--text-muted)",
                      }}
                    >
                      <Kbd>Space</Kbd> play<Kbd>J</Kbd>/<Kbd>K</Kbd> nav
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    padding: "16px 22px",
                    borderTop: "1px solid var(--border-subtle)",
                    background: "var(--surface-sunken)",
                  }}
                >
                  <div
                    style={{
                      fontSize: 11,
                      textTransform: "uppercase",
                      letterSpacing: "var(--tracking-caps)",
                      color: "var(--text-subtle)",
                      fontWeight: 600,
                      marginBottom: 10,
                    }}
                  >
                    Label this clip
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {WAKE_LABELS.map((entry) => (
                      <LabelChip
                        key={entry.id}
                        tone={entry.tone}
                        shortcut={entry.key}
                        selected={clip.label === entry.id}
                        onClick={() => applyLabel(entry.id)}
                      >
                        {entry.label}
                      </LabelChip>
                    ))}
                  </div>
                </div>
              </Card>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <Card title="Clip metadata" elevation="flat">
                  <KeyValue
                    items={[
                      { k: "File", v: clip.filename, mono: true },
                      { k: "Duration", v: formatSeconds(clip.duration), mono: true },
                      { k: "Sample rate", v: formatRate(clip.sample_rate), mono: true },
                      {
                        k: "Format",
                        v: `${(clip.sample_width ?? 0) * 8}-bit · ${clip.channels ?? "?"} ch`,
                        mono: true,
                      },
                      { k: "Assistant", v: clip.assistant_id ?? "—" },
                      { k: "Wake word", v: clip.wake_word ?? "—", mono: true },
                      { k: "Confidence", v: formatConfidence(clip.confidence), mono: true },
                    ]}
                  />
                </Card>
                <Card
                  title="Capture status"
                  actions={
                    <Tooltip content="Refresh">
                      <IconButton size="sm" aria-label="Refresh status" onClick={refreshStatus}>
                        <Icon d={ICONS.refresh} size={12} />
                      </IconButton>
                    </Tooltip>
                  }
                >
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                    <StatCell
                      label="Unlabeled"
                      value={unlabeledTotal}
                      unit={`/ ${unlabeledTotal + labeledTotal}`}
                    />
                    <StatCell label="Labeled" value={labeledTotal} />
                    <StatCell
                      label="Buffered"
                      value={formatSeconds(status?.assistants?.[0]?.buffered_seconds ?? 0)}
                      unit={status?.assistants?.[0]?.assistant_id}
                    />
                    <StatCell
                      label="Transport"
                      value={transports.length ? transports.join(" + ") : "none"}
                      delta={
                        status?.webhook_url ? `webhook ${status.webhook_url}` : "no webhook"
                      }
                      deltaTone="neutral"
                    />
                  </div>
                </Card>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
