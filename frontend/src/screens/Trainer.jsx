import React from "react";

import { Icon, ICONS } from "../components/Icon.jsx";
import {
  Badge,
  Button,
  Card,
  ConversationTurn,
  Dialog,
  IconButton,
  Input,
  Kbd,
  KeyValue,
  Select,
  StatCell,
  Tabs,
  Tag,
  Textarea,
  ToolInvocation,
  Toolbar,
  ToolbarSeparator,
  ToolbarSpacer,
  Tooltip,
} from "../ds/index.js";
import { formatDateTime, formatTime, shortId, toJsonText } from "../lib/format.js";
import { useKeyboard, useSubscription } from "../lib/hooks.js";

const PAGE_SIZE = 100;

const TABS = [
  { value: "all", label: "All", corrected: "all" },
  { value: "uncorrected", label: "Uncorrected", corrected: "uncorrected" },
  { value: "corrected", label: "Corrected", corrected: "corrected" },
];

const chatKey = (chat) => `${chat.conversation_id}::${chat.pipeline_run_id}`;

/** The design system renders four roles; everything else reads as a tool turn. */
const turnRole = (sender) => {
  if (sender === "user") return "user";
  if (sender === "system") return "system";
  if (sender === "assistant") return "assistant";
  return "tool";
};

const isToolCall = (message) => Boolean(message.data?.tool_calls);
const isToolResult = (message) =>
  message.sender === "tool_result" || message.data?.tool_result !== undefined;

/**
 * Seed the editable draft for a chat: an existing correction if the reviewer has
 * saved one, otherwise a copy of the original turns.
 */
function draftFromChat(chat) {
  if (chat.corrected?.messages?.length) {
    return chat.corrected.messages.map((message, index) => ({
      original_message_id: message.original_message_id ?? null,
      position: message.position ?? index,
      timestamp: message.timestamp,
      sender: message.sender,
      text: message.text ?? "",
      data: message.data ?? {},
    }));
  }
  return (chat.messages ?? []).map((message, index) => ({
    original_message_id: message.id ?? null,
    position: index,
    timestamp: message.timestamp,
    sender: message.sender,
    text: message.text ?? "",
    data: message.data ?? {},
  }));
}

function toolArgsText(message) {
  const calls = message.data?.tool_calls;
  if (!Array.isArray(calls)) return toJsonText(message.data);
  return toJsonText(
    calls.map((call) => ({
      name: call.tool_name ?? call.name,
      arguments: call.tool_args ?? call.arguments ?? {},
    })),
  );
}

export function Trainer({ api, onError, onNotify }) {
  const [tab, setTab] = React.useState("uncorrected");
  const [query, setQuery] = React.useState("");
  const [senderFilter, setSenderFilter] = React.useState("");

  const [response, setResponse] = React.useState(null);
  const [selectedKey, setSelectedKey] = React.useState(null);
  const [draft, setDraft] = React.useState([]);
  // Draft indices whose editor is open. A turn is read-only until the reviewer
  // asks to correct it, so a fresh conversation reads as a transcript.
  const [editing, setEditing] = React.useState(() => new Set());
  const [dirty, setDirty] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [exported, setExported] = React.useState(null);

  const activeTab = TABS.find((entry) => entry.value === tab) ?? TABS[0];

  const filters = React.useMemo(
    () => ({ limit: PAGE_SIZE, corrected: activeTab.corrected }),
    [activeTab.corrected],
  );

  const subscribe = React.useCallback(
    (payload, handler) => api.subscribeChats(payload, handler),
    [api],
  );

  useSubscription(subscribe, filters, setResponse, onError);

  const chats = React.useMemo(() => {
    const all = (response?.chats ?? []).filter((chat) => !chat.deleted_at);
    if (!query) return all;
    const needle = query.toLowerCase();
    return all.filter((chat) =>
      [chat.conversation_id, ...(chat.messages ?? []).map((message) => message.text)]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [response, query]);

  const selectedIndex = React.useMemo(() => {
    const index = chats.findIndex((chat) => chatKey(chat) === selectedKey);
    return index === -1 ? 0 : index;
  }, [chats, selectedKey]);

  const chat = chats[selectedIndex] ?? null;

  React.useEffect(() => {
    if (!chats.length) {
      if (selectedKey !== null) setSelectedKey(null);
      return;
    }
    if (!chats.some((entry) => chatKey(entry) === selectedKey)) {
      setSelectedKey(chatKey(chats[Math.min(selectedIndex, chats.length - 1)]));
    }
  }, [chats, selectedKey, selectedIndex]);

  // Reseed the draft when the selection changes, but never clobber unsaved edits
  // just because a live push re-delivered the same chat.
  const activeKey = chat ? chatKey(chat) : null;
  const seededKey = React.useRef(null);
  React.useEffect(() => {
    if (!chat) {
      seededKey.current = null;
      setDraft([]);
      setEditing(new Set());
      setDirty(false);
      return;
    }
    if (seededKey.current === activeKey) return;
    seededKey.current = activeKey;
    setDraft(draftFromChat(chat));
    setEditing(new Set());
    setDirty(false);
  }, [chat, activeKey]);

  const toggleEditing = React.useCallback((index) => {
    setEditing((current) => {
      const next = new Set(current);
      if (!next.delete(index)) next.add(index);
      return next;
    });
  }, []);

  const select = React.useCallback((key) => setSelectedKey(key), []);

  const step = React.useCallback(
    (delta) => {
      if (!chats.length) return;
      const next = Math.min(chats.length - 1, Math.max(0, selectedIndex + delta));
      select(chatKey(chats[next]));
    },
    [chats, select, selectedIndex],
  );

  const updateDraft = React.useCallback((index, patch) => {
    setDirty(true);
    setDraft((current) =>
      current.map((message, position) =>
        position === index ? { ...message, ...patch } : message,
      ),
    );
  }, []);

  const save = React.useCallback(
    async ({ advance } = {}) => {
      if (!chat) return;
      setBusy(true);
      try {
        await api.saveCorrectedChat(
          chat.conversation_id,
          chat.pipeline_run_id,
          draft.map((message, index) => ({
            original_message_id: message.original_message_id,
            position: index,
            timestamp: message.timestamp,
            sender: message.sender,
            text: message.text,
            data: message.data,
          })),
        );
        setDirty(false);
        onNotify("success", "Correction saved", shortId(chat.conversation_id, 18));
        if (advance) step(1);
      } catch (error) {
        onError(error);
      } finally {
        setBusy(false);
      }
    },
    [api, chat, draft, onError, onNotify, step],
  );

  const discard = React.useCallback(() => {
    if (!chat) return;
    setDraft(draftFromChat(chat));
    setEditing(new Set());
    setDirty(false);
  }, [chat]);

  const deleteChat = React.useCallback(async () => {
    if (!chat) return;
    setBusy(true);
    try {
      await api.tombstoneChats([
        {
          kind: "chat",
          conversation_id: chat.conversation_id,
          pipeline_run_id: chat.pipeline_run_id,
        },
      ]);
      onNotify("info", "Chat removed from the dataset");
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }, [api, chat, onError, onNotify]);

  const exportJsonl = React.useCallback(async () => {
    setBusy(true);
    try {
      const result = await api.exportCorrectedChats({ limit: 500 });
      setExported(result);
    } catch (error) {
      onError(error);
    } finally {
      setBusy(false);
    }
  }, [api, onError]);

  const downloadJsonl = React.useCallback(() => {
    if (!exported?.jsonl) return;
    const blob = new Blob([exported.jsonl], { type: "application/jsonl" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "intentsity_corrected.jsonl";
    link.click();
    URL.revokeObjectURL(url);
  }, [exported]);

  useKeyboard(
    React.useCallback(
      (event) => {
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
          event.preventDefault();
          save();
          return;
        }
        if (event.metaKey || event.ctrlKey || event.altKey) return;
        if (event.key === "j" || event.key === "ArrowDown") {
          event.preventDefault();
          step(1);
        } else if (event.key === "k" || event.key === "ArrowUp") {
          event.preventDefault();
          step(-1);
        }
      },
      [save, step],
    ),
  );

  const counts = React.useMemo(() => {
    const all = response?.chats ?? [];
    const corrected = all.filter((entry) => entry.corrected).length;
    return { all: all.length, corrected, uncorrected: all.length - corrected };
  }, [response]);

  const visibleDraft = React.useMemo(
    () =>
      draft
        .map((message, index) => ({ message, index }))
        .filter(({ message }) => !senderFilter || turnRole(message.sender) === senderFilter),
    [draft, senderFilter],
  );

  const systemMessage = chat?.messages?.find((message) => message.sender === "system");

  // Which draft turns no longer match the recorded transcript, by message ID
  // where the correction carries one and by position otherwise.
  const originalText = React.useMemo(() => {
    const byId = new Map((chat?.messages ?? []).map((message) => [message.id, message.text ?? ""]));
    const byPosition = (chat?.messages ?? []).map((message) => message.text ?? "");
    return (message, index) =>
      message.original_message_id != null && byId.has(message.original_message_id)
        ? byId.get(message.original_message_id)
        : (byPosition[index] ?? "");
  }, [chat]);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
      <Toolbar>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Intent training</span>
        <span style={{ fontSize: 12, color: "var(--text-subtle)" }}>/</span>
        <span style={{ fontWeight: 600, fontSize: 14 }}>Conversations</span>
        <Badge tone="brand">{response?.total ?? counts.all} recorded</Badge>
        <ToolbarSeparator />
        <Input
          size="sm"
          placeholder="Search transcripts…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          style={{ width: 240 }}
          prefix={<Icon d={ICONS.search} size={12} />}
        />
        <Select
          size="sm"
          options={[
            { value: "", label: "All turns" },
            { value: "system", label: "System" },
            { value: "user", label: "User" },
            { value: "assistant", label: "Assistant" },
            { value: "tool", label: "Tool" },
          ]}
          value={senderFilter}
          onChange={(event) => setSenderFilter(event.target.value)}
          style={{ width: 140 }}
        />
        <ToolbarSpacer />
        <Button
          size="sm"
          variant="ghost"
          disabled={busy}
          onClick={exportJsonl}
          iconLeft={<Icon d={ICONS.download} size={12} />}
        >
          Export JSONL
        </Button>
        <Button size="sm" variant="primary" disabled={!chat || busy} onClick={() => save()}>
          {dirty ? "Save correction" : "Saved"}
        </Button>
      </Toolbar>

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <div
          style={{
            width: 280,
            minWidth: 280,
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
                count: counts[entry.value],
              }))}
            />
          </div>
          <div style={{ flex: 1, overflow: "auto" }}>
            {chats.length === 0 && (
              <div style={{ padding: 20, fontSize: 13, color: "var(--text-muted)" }}>
                {response ? "No conversations match these filters." : "Loading conversations…"}
              </div>
            )}
            {chats.map((entry) => {
              const key = chatKey(entry);
              const active = key === activeKey;
              const firstUserTurn = (entry.messages ?? []).find(
                (message) => message.sender === "user",
              );
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => select(key)}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "12px 14px",
                    border: "none",
                    textAlign: "left",
                    background: active ? "var(--accent-quiet)" : "transparent",
                    borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                    borderBottom: "1px solid var(--border-subtle)",
                    cursor: "pointer",
                    color: "var(--text-body)",
                  }}
                >
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}
                  >
                    <span
                      style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500 }}
                    >
                      {shortId(entry.conversation_id, 12)}
                    </span>
                    {entry.corrected && (
                      <Badge tone="tp" dot style={{ height: 16, fontSize: 9 }}>
                        fixed
                      </Badge>
                    )}
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--text-body)",
                      marginBottom: 2,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {firstUserTurn?.text || "(no user turn)"}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {(entry.messages ?? []).length} turns · {formatTime(entry.run_timestamp)}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ flex: 1, display: "flex", minWidth: 0 }}>
          <div
            style={{
              flex: 1,
              padding: 24,
              overflow: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 14,
              minWidth: 0,
            }}
          >
            {!chat && (
              <Card title="Nothing selected">
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  Conversations appear here after an Assist pipeline run completes.
                </div>
              </Card>
            )}

            {chat && (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>
                    {shortId(chat.conversation_id, 20)}
                  </h2>
                  <Badge mono>{shortId(chat.pipeline_run_id, 10)}</Badge>
                  {dirty && <Badge tone="fn">unsaved</Badge>}
                  <ToolbarSpacer />
                  <Tooltip content="Remove this chat from the dataset">
                    <IconButton aria-label="Delete chat" disabled={busy} onClick={deleteChat}>
                      <Icon d={ICONS.trash} />
                    </IconButton>
                  </Tooltip>
                  <Button size="sm" variant="ghost" disabled={!dirty} onClick={discard}>
                    Discard edits
                  </Button>
                </div>

                {visibleDraft.map(({ message, index }) => {
                  const role = turnRole(message.sender);
                  const changed = (message.text ?? "") !== originalText(message, index);
                  if (isToolCall(message)) {
                    return (
                      <EditableTurn
                        key={index}
                        label="Tool call"
                        editing={editing.has(index)}
                        changed={changed}
                        onToggle={() => toggleEditing(index)}
                        // The arguments payload stays on screen while editing:
                        // the text box holds notes about the call, not the args.
                        keepPreview
                        preview={
                          <ToolInvocation
                            name={
                              message.data?.tool_calls?.[0]?.tool_name ??
                              message.data?.tool_calls?.[0]?.name ??
                              "tool_call"
                            }
                            status="ok"
                            args={toolArgsText(message)}
                          />
                        }
                      >
                        <Textarea
                          style={{ marginTop: 8, fontFamily: "var(--font-mono)", fontSize: 12 }}
                          minRows={4}
                          value={message.text}
                          placeholder="Notes on this tool call (the arguments live in the payload above)"
                          onChange={(event) => updateDraft(index, { text: event.target.value })}
                        />
                      </EditableTurn>
                    );
                  }
                  if (isToolResult(message)) {
                    return (
                      <EditableTurn
                        key={index}
                        label="Tool result"
                        editing={editing.has(index)}
                        changed={changed}
                        onToggle={() => toggleEditing(index)}
                        preview={
                          <ConversationTurn role="tool" timestamp={formatTime(message.timestamp)}>
                            {message.text || "(empty)"}
                          </ConversationTurn>
                        }
                      >
                        <Textarea
                          style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}
                          minRows={3}
                          value={message.text}
                          onChange={(event) => updateDraft(index, { text: event.target.value })}
                        />
                      </EditableTurn>
                    );
                  }
                  if (role === "system") {
                    // System prompts run to hundreds of lines; folded away they
                    // stop burying the turns the reviewer is here to correct.
                    return (
                      <Collapsible
                        key={index}
                        title="System prompt"
                        meta={promptMeta(message.text)}
                      >
                        <PromptText text={message.text || "(empty system prompt)"} />
                      </Collapsible>
                    );
                  }
                  return (
                    <EditableTurn
                      key={index}
                      label={role}
                      editing={editing.has(index)}
                      changed={changed}
                      onToggle={() => toggleEditing(index)}
                      preview={
                        <ConversationTurn role={role} timestamp={formatTime(message.timestamp)}>
                          {message.text || "(empty)"}
                        </ConversationTurn>
                      }
                    >
                      <Textarea
                        minRows={2}
                        value={message.text}
                        onChange={(event) => updateDraft(index, { text: event.target.value })}
                      />
                    </EditableTurn>
                  );
                })}

                <div style={{ display: "flex", gap: 8, paddingTop: 8 }}>
                  <Button variant="primary" disabled={busy} onClick={() => save({ advance: true })}>
                    Save &amp; next
                  </Button>
                  <Button variant="ghost" onClick={() => step(1)}>
                    Skip
                  </Button>
                  <ToolbarSpacer />
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--text-muted)",
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <Kbd>⌘S</Kbd> save<Kbd>J</Kbd>/<Kbd>K</Kbd> nav
                  </div>
                </div>
              </>
            )}
          </div>

          {chat && (
            <div
              style={{
                width: 280,
                minWidth: 280,
                borderLeft: "1px solid var(--border-subtle)",
                background: "var(--surface-panel)",
                padding: 16,
                overflow: "auto",
                display: "flex",
                flexDirection: "column",
                gap: 16,
              }}
            >
              <div>
                <FieldLabel>Run metadata</FieldLabel>
                <KeyValue
                  items={[
                    { k: "Conversation", v: shortId(chat.conversation_id, 16), mono: true },
                    { k: "Run", v: shortId(chat.pipeline_run_id, 16), mono: true },
                    { k: "Started", v: formatDateTime(chat.run_timestamp) },
                    { k: "Turns", v: (chat.messages ?? []).length, mono: true },
                    {
                      k: "Corrected",
                      v: chat.corrected ? formatDateTime(chat.corrected.updated_at) : "not yet",
                    },
                  ]}
                />
              </div>
              <div>
                <FieldLabel>Turn roles</FieldLabel>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {[...new Set(draft.map((message) => message.sender))].map((sender) => (
                    <Tag key={sender}>{sender}</Tag>
                  ))}
                </div>
              </div>
              <div>
                <FieldLabel>Dataset</FieldLabel>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <StatCell label="Corrected" value={counts.corrected} unit={`/ ${counts.all}`} />
                  <StatCell label="Remaining" value={counts.uncorrected} />
                </div>
              </div>
              {systemMessage && (
                <div>
                  <FieldLabel>System prompt (read-only)</FieldLabel>
                  <Collapsible title="Show prompt" meta={promptMeta(systemMessage.text)}>
                    <PromptText text={systemMessage.text} maxHeight={260} />
                  </Collapsible>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <Dialog
        open={Boolean(exported)}
        onClose={() => setExported(null)}
        title={`Corrected dataset — ${exported?.count ?? 0} conversations`}
        width={720}
        footer={
          <>
            <Button variant="ghost" onClick={() => setExported(null)}>
              Close
            </Button>
            <Button
              variant="primary"
              disabled={!exported?.count}
              onClick={downloadJsonl}
              iconLeft={<Icon d={ICONS.download} size={12} />}
            >
              Download .jsonl
            </Button>
          </>
        }
      >
        <pre
          style={{
            margin: 0,
            maxHeight: 360,
            overflow: "auto",
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            whiteSpace: "pre-wrap",
            color: "var(--text-muted)",
          }}
        >
          {exported?.jsonl || "No corrected conversations yet."}
        </pre>
      </Dialog>
    </div>
  );
}

/**
 * One transcript turn. The editor stays hidden behind the pencil so an
 * untouched conversation reads as a transcript rather than a wall of inputs.
 */
function EditableTurn({ label, editing, changed, onToggle, preview, keepPreview, children }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <FieldLabel style={{ marginBottom: 0 }}>{label}</FieldLabel>
        {/* With the editors hidden, this is the only cue that a turn was rewritten. */}
        {changed && (
          <Badge tone="fn" style={{ height: 16, fontSize: 9 }}>
            edited
          </Badge>
        )}
        <Tooltip content={editing ? "Done editing" : "Edit this turn"}>
          <IconButton
            size="sm"
            active={editing}
            aria-label={editing ? `Stop editing ${label}` : `Edit ${label}`}
            aria-pressed={editing}
            onClick={onToggle}
          >
            <Icon d={editing ? ICONS.check : ICONS.pencil} size={12} />
          </IconButton>
        </Tooltip>
      </div>
      {(!editing || keepPreview) && preview}
      {editing && children}
    </div>
  );
}

const promptMeta = (text) => {
  const value = text ?? "";
  const lines = value ? value.split("\n").length : 0;
  return `${lines} lines · ${value.length.toLocaleString()} chars`;
};

/** Disclosure wrapper, collapsed until the reviewer asks for the detail. */
function Collapsible({ title, meta, defaultOpen = false, children }) {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div
      style={{
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--r-md)",
        background: "var(--surface-panel)",
        minWidth: 0,
      }}
    >
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          width: "100%",
          padding: "8px 10px",
          background: "none",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
          color: "var(--text-body)",
          fontFamily: "var(--font-sans)",
          fontSize: 12,
          fontWeight: 500,
        }}
      >
        <Icon d={open ? ICONS.chevronDown : ICONS.chevronRight} size={12} />
        <span>{title}</span>
        {meta && (
          <span
            style={{
              marginLeft: "auto",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              color: "var(--text-subtle)",
            }}
          >
            {meta}
          </span>
        )}
      </button>
      {open && <div style={{ padding: "0 10px 10px" }}>{children}</div>}
    </div>
  );
}

function PromptText({ text, maxHeight = 360 }) {
  return (
    <pre
      style={{
        margin: 0,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        lineHeight: "var(--lh-normal)",
        color: "var(--text-muted)",
        maxHeight,
        overflow: "auto",
      }}
    >
      {text}
    </pre>
  );
}

function FieldLabel({ children, style }) {
  return (
    <div
      style={{
        fontSize: 11,
        color: "var(--text-subtle)",
        textTransform: "uppercase",
        letterSpacing: "var(--tracking-caps)",
        fontWeight: 600,
        marginBottom: 6,
        fontFamily: "var(--font-mono)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
