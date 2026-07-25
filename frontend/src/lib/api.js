// Thin wrapper over the Home Assistant websocket connection the panel is
// handed by the frontend. Every command name here has a matching handler in
// custom_components/intentsity/websocket.py.

export const CMD = {
  listChats: "intentsity/chats/list",
  subscribeChats: "intentsity/chats/subscribe",
  saveCorrectedChat: "intentsity/chats/corrected/save",
  exportCorrectedChats: "intentsity/chats/corrected/export",
  tombstoneChats: "intentsity/chats/tombstone",
  listClips: "intentsity/clips/list",
  subscribeClips: "intentsity/clips/subscribe",
  labelClips: "intentsity/clips/label",
  tombstoneClips: "intentsity/clips/tombstone",
  captureNoise: "intentsity/clips/capture_noise",
  assistants: "intentsity/assistants",
};

export class IntentsityApi {
  constructor(hass) {
    this.hass = hass;
  }

  get connection() {
    return this.hass?.connection;
  }

  call(type, payload = {}) {
    const connection = this.connection;
    if (!connection) {
      return Promise.reject(new Error("Home Assistant connection unavailable"));
    }
    return connection.sendMessagePromise({ type, ...payload });
  }

  subscribe(type, payload, handler) {
    const connection = this.connection;
    if (!connection) {
      return Promise.reject(new Error("Home Assistant connection unavailable"));
    }
    return connection.subscribeMessage(handler, { type, ...payload });
  }

  // --- Wake word ---------------------------------------------------------

  listClips(filters) {
    return this.call(CMD.listClips, filters);
  }

  subscribeClips(filters, handler) {
    return this.subscribe(CMD.subscribeClips, filters, handler);
  }

  labelClips(clipIds, label) {
    return this.call(CMD.labelClips, { clip_ids: clipIds, label });
  }

  tombstoneClips(clipIds, restore = false) {
    return this.call(CMD.tombstoneClips, { clip_ids: clipIds, restore });
  }

  captureNoise(assistantId, seconds) {
    return this.call(CMD.captureNoise, { assistant_id: assistantId, seconds });
  }

  assistants() {
    return this.call(CMD.assistants);
  }

  // --- Intent training ---------------------------------------------------

  listChats(filters) {
    return this.call(CMD.listChats, filters);
  }

  subscribeChats(filters, handler) {
    return this.subscribe(CMD.subscribeChats, filters, handler);
  }

  saveCorrectedChat(conversationId, pipelineRunId, messages) {
    return this.call(CMD.saveCorrectedChat, {
      conversation_id: conversationId,
      pipeline_run_id: pipelineRunId,
      messages,
    });
  }

  exportCorrectedChats(filters) {
    return this.call(CMD.exportCorrectedChats, filters);
  }

  tombstoneChats(targets) {
    return this.call(CMD.tombstoneChats, { targets });
  }

  // --- Authenticated HTTP ------------------------------------------------

  /** Signed, short-lived URL usable by <audio> and download links. */
  async signPath(path, expires = 300) {
    const { path: signed } = await this.call("auth/sign_path", { path, expires });
    return signed;
  }
}
