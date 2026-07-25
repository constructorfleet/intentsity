from __future__ import annotations

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
import voluptuous as vol

from .const import (
    ALL_CLIP_LABELS,
    AUDIO_KEY,
    CLIP_AUDIO_URL,
    DEFAULT_CLIP_LIMIT,
    DEFAULT_EVENT_LIMIT,
    DOMAIN,
    MAX_CLIP_LIMIT,
    MAX_EVENT_LIMIT,
    MIN_EVENT_LIMIT,
    SIGNAL_CLIP_RECORDED,
    SIGNAL_EVENT_RECORDED,
    WAKE_LABELS,
    WS_CMD_ASSISTANTS,
    WS_CMD_CAPTURE_NOISE,
    WS_CMD_EXPORT_CORRECTED_CHATS,
    WS_CMD_LABEL_CLIP,
    WS_CMD_LIST_CHATS,
    WS_CMD_LIST_CLIPS,
    WS_CMD_REPAIR_CLIP_RATE,
    WS_CMD_SAVE_CORRECTED_CHAT,
    WS_CMD_SUBSCRIBE_CHATS,
    WS_CMD_SUBSCRIBE_CLIPS,
    WS_CMD_TOMBSTONE,
    WS_CMD_TOMBSTONE_CLIPS,
)
from .db import (
    count_clips_by_assistant,
    fetch_chats,
    fetch_chats_page,
    fetch_clips_page,
    get_storage_dir,
    label_clips,
    tombstone_clips,
    tombstone_targets,
    upsert_corrected_chat,
)
from .export import generate_corrected_jsonl
from .maintenance import repair_misdeclared_clip_sample_rates
from .models import (
    AssistantListResponse,
    AssistantStatus,
    CaptureNoiseRequest,
    ChatListRequest,
    ChatListResponse,
    ClipLabelRequest,
    ClipListRequest,
    ClipRateRepairRequest,
    ClipTombstoneRequest,
    CorrectedChatExportRequest,
    CorrectedChatSaveRequest,
    TombstoneRequest,
)

_EVENT_LIMIT_SCHEMA = vol.All(
    vol.Coerce(int),
    vol.Range(min=MIN_EVENT_LIMIT, max=MAX_EVENT_LIMIT),
)
_CORRECTED_FILTER_SCHEMA = vol.In(["all", "corrected", "uncorrected"])
_DATE_FILTER_SCHEMA = vol.Any(None, vol.Coerce(str))


_CLIP_LIMIT_SCHEMA = vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_CLIP_LIMIT))
_CLIP_LABEL_SCHEMA = vol.In(list(ALL_CLIP_LABELS))


def async_register_commands(hass: HomeAssistant) -> None:
    """Register websocket commands for both Intentsity surfaces."""
    websocket_api.async_register_command(hass, websocket_list_chats)
    websocket_api.async_register_command(hass, websocket_subscribe_chats)
    websocket_api.async_register_command(hass, websocket_save_corrected_chat)
    websocket_api.async_register_command(hass, websocket_export_corrected_chats)
    websocket_api.async_register_command(hass, websocket_tombstone_targets)
    websocket_api.async_register_command(hass, websocket_list_clips)
    websocket_api.async_register_command(hass, websocket_subscribe_clips)
    websocket_api.async_register_command(hass, websocket_label_clips)
    websocket_api.async_register_command(hass, websocket_tombstone_clips)
    websocket_api.async_register_command(hass, websocket_repair_clip_rate)
    websocket_api.async_register_command(hass, websocket_capture_noise)
    websocket_api.async_register_command(hass, websocket_assistants)


def _normalize_corrected_filter(value: str) -> bool | None:
    if value == "corrected":
        return True
    if value == "uncorrected":
        return False
    return None


async def _async_fetch_chats_payload(
    hass: HomeAssistant,
    request: ChatListRequest,
) -> dict:
    corrected = _normalize_corrected_filter(request.corrected)
    chats, total = await hass.async_add_executor_job(
        fetch_chats_page,
        hass,
        request.limit,
        request.offset,
        corrected,
        request.start,
        request.end,
    )
    if isinstance(chats, ChatListResponse):
        return chats.model_dump(mode="json")
    return ChatListResponse(chats=chats, total=total).model_dump(mode="json")


async def _async_send_chats_result(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    request_id: int,
    request: ChatListRequest,
) -> None:
    payload = await _async_fetch_chats_payload(hass, request)
    connection.send_result(request_id, payload)


async def _async_send_chats_event(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    request_id: int,
    request: ChatListRequest,
) -> None:
    corrected = _normalize_corrected_filter(request.corrected)
    chats = await hass.async_add_executor_job(
        fetch_chats,
        hass,
        request.limit,
        request.offset,
        corrected,
        request.start,
        request.end,
    )
    payload = ChatListResponse(chats=chats).model_dump(mode="json", exclude={"total"})
    connection.send_message(websocket_api.messages.event_message(request_id, payload))


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_LIST_CHATS,
        vol.Optional("limit", default=DEFAULT_EVENT_LIMIT): _EVENT_LIMIT_SCHEMA,
        vol.Optional("offset", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("corrected", default="all"): _CORRECTED_FILTER_SCHEMA,
        vol.Optional("start"): _DATE_FILTER_SCHEMA,
        vol.Optional("end"): _DATE_FILTER_SCHEMA,
    }
)
@callback
def websocket_list_chats(
    hass: HomeAssistant, connection: websocket_api.connection.ActiveConnection, msg: dict
) -> None:
    """Return a snapshot of recent chats."""
    request = ChatListRequest.model_validate(msg)
    hass.async_create_task(_async_send_chats_result(hass, connection, msg["id"], request))


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_SUBSCRIBE_CHATS,
        vol.Optional("limit", default=DEFAULT_EVENT_LIMIT): _EVENT_LIMIT_SCHEMA,
        vol.Optional("offset", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("corrected", default="all"): _CORRECTED_FILTER_SCHEMA,
        vol.Optional("start"): _DATE_FILTER_SCHEMA,
        vol.Optional("end"): _DATE_FILTER_SCHEMA,
    }
)
@callback
def websocket_subscribe_chats(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe to live chat event updates."""
    request_id: int = msg["id"]
    connection.send_result(request_id)
    request = ChatListRequest.model_validate(msg)

    async def _push_snapshot() -> None:
        await _async_send_chats_event(hass, connection, request_id, request)

    @callback
    def _handle_new_event(*_: object) -> None:
        hass.async_create_task(_push_snapshot())

    unsubscribe = async_dispatcher_connect(hass, SIGNAL_EVENT_RECORDED, _handle_new_event)
    connection.subscriptions[request_id] = unsubscribe
    hass.async_create_task(_push_snapshot())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_SAVE_CORRECTED_CHAT,
        vol.Required("conversation_id"): vol.Coerce(str),
        vol.Required("pipeline_run_id"): vol.Coerce(str),
        vol.Required("messages"): list,
    }
)
@callback
def websocket_save_corrected_chat(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Persist corrected chat messages for a given original chat."""
    request = CorrectedChatSaveRequest.model_validate(msg)

    async def _save() -> None:
        await hass.async_add_executor_job(
            upsert_corrected_chat,
            hass,
            request.conversation_id,
            request.pipeline_run_id,
            request.messages,
        )
        async_dispatcher_send(hass, SIGNAL_EVENT_RECORDED)
        connection.send_result(msg["id"])

    hass.async_create_task(_save())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_EXPORT_CORRECTED_CHATS,
        vol.Optional("limit", default=DEFAULT_EVENT_LIMIT): _EVENT_LIMIT_SCHEMA,
        vol.Optional("start"): _DATE_FILTER_SCHEMA,
        vol.Optional("end"): _DATE_FILTER_SCHEMA,
    }
)
@callback
def websocket_export_corrected_chats(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Export corrected chats as JSONL for fine-tuning."""
    request = CorrectedChatExportRequest.model_validate(msg)

    async def _export() -> None:
        payload = await hass.async_add_executor_job(
            generate_corrected_jsonl,
            hass,
            request,
        )
        connection.send_result(msg["id"], payload)

    hass.async_create_task(_export())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_TOMBSTONE,
        vol.Required("targets"): list,
    }
)
@callback
def websocket_tombstone_targets(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Tombstone chats or messages."""
    request = TombstoneRequest.model_validate(msg)

    async def _tombstone() -> None:
        await hass.async_add_executor_job(
            tombstone_targets,
            hass,
            request.targets,
        )
        async_dispatcher_send(hass, SIGNAL_EVENT_RECORDED)
        connection.send_result(msg["id"])

    hass.async_create_task(_tombstone())


# --- Wake word annotator --------------------------------------------------

_CLIP_FILTER_SCHEMA = {
    vol.Optional("limit", default=DEFAULT_CLIP_LIMIT): _CLIP_LIMIT_SCHEMA,
    vol.Optional("offset", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Optional("label"): vol.Any(None, _CLIP_LABEL_SCHEMA),
    vol.Optional("assistant_id"): vol.Any(None, vol.Coerce(str)),
    vol.Optional("include_deleted", default=False): bool,
    vol.Optional("labeled_only", default=False): bool,
    vol.Optional("deleted_only", default=False): bool,
    vol.Optional("start"): _DATE_FILTER_SCHEMA,
    vol.Optional("end"): _DATE_FILTER_SCHEMA,
}


def _clip_payload(response) -> dict:
    """Serialize clips, attaching the authenticated audio URL for each."""
    payload = response.model_dump(mode="json")
    for clip in payload["clips"]:
        clip["audio_url"] = f"{CLIP_AUDIO_URL}/{clip['id']}/audio"
    return payload


async def _async_send_clips(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    request_id: int,
    request: ClipListRequest,
    as_event: bool,
) -> None:
    response = await hass.async_add_executor_job(fetch_clips_page, hass, request)
    payload = _clip_payload(response)
    if as_event:
        connection.send_message(websocket_api.messages.event_message(request_id, payload))
    else:
        connection.send_result(request_id, payload)


@websocket_api.decorators.websocket_command(
    {vol.Required("type"): WS_CMD_LIST_CLIPS, **_CLIP_FILTER_SCHEMA}
)
@callback
def websocket_list_clips(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Return a page of captured clips, newest first."""
    request = ClipListRequest.model_validate(msg)
    hass.async_create_task(_async_send_clips(hass, connection, msg["id"], request, as_event=False))


@websocket_api.decorators.websocket_command(
    {vol.Required("type"): WS_CMD_SUBSCRIBE_CLIPS, **_CLIP_FILTER_SCHEMA}
)
@callback
def websocket_subscribe_clips(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Push a fresh clip page whenever a clip is captured or relabeled."""
    request_id: int = msg["id"]
    connection.send_result(request_id)
    request = ClipListRequest.model_validate(msg)

    async def _push() -> None:
        await _async_send_clips(hass, connection, request_id, request, as_event=True)

    @callback
    def _handle_clip(*_: object) -> None:
        hass.async_create_task(_push())

    connection.subscriptions[request_id] = async_dispatcher_connect(
        hass, SIGNAL_CLIP_RECORDED, _handle_clip
    )
    hass.async_create_task(_push())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_LABEL_CLIP,
        vol.Required("clip_ids"): [vol.Coerce(int)],
        vol.Required("label"): _CLIP_LABEL_SCHEMA,
    }
)
@callback
def websocket_label_clips(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Apply a wake label to one or more clips."""
    request = ClipLabelRequest.model_validate(msg)

    async def _label() -> None:
        updated = await hass.async_add_executor_job(
            label_clips, hass, request.clip_ids, request.label
        )
        async_dispatcher_send(hass, SIGNAL_CLIP_RECORDED)
        connection.send_result(msg["id"], {"updated": updated})

    hass.async_create_task(_label())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_TOMBSTONE_CLIPS,
        vol.Required("clip_ids"): [vol.Coerce(int)],
        vol.Optional("restore", default=False): bool,
    }
)
@callback
def websocket_tombstone_clips(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Soft-delete or restore clips."""
    request = ClipTombstoneRequest.model_validate(msg)

    async def _tombstone() -> None:
        updated = await hass.async_add_executor_job(
            tombstone_clips, hass, request.clip_ids, request.restore
        )
        async_dispatcher_send(hass, SIGNAL_CLIP_RECORDED)
        connection.send_result(msg["id"], {"updated": updated})

    hass.async_create_task(_tombstone())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_REPAIR_CLIP_RATE,
        vol.Required("clip_id"): vol.Coerce(int),
    }
)
@callback
def websocket_repair_clip_rate(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Repair one legacy clip whose 16 kHz PCM was declared as 48 kHz."""
    request = ClipRateRepairRequest.model_validate(msg)

    def _repair() -> dict:
        summary = repair_misdeclared_clip_sample_rates(
            get_storage_dir(hass),
            clip_id=request.clip_id,
            dry_run=False,
        )
        return {
            "scanned": summary.scanned,
            "repaired": summary.repaired,
            "missing_file": summary.missing_file,
            "skipped_header_rate": summary.skipped_header_rate,
            "skipped_unsupported_format": summary.skipped_unsupported_format,
        }

    async def _run() -> None:
        payload = await hass.async_add_executor_job(_repair)
        if payload["repaired"]:
            async_dispatcher_send(hass, SIGNAL_CLIP_RECORDED)
        connection.send_result(msg["id"], payload)

    hass.async_create_task(_run())


@websocket_api.decorators.websocket_command(
    {
        vol.Required("type"): WS_CMD_CAPTURE_NOISE,
        vol.Optional("assistant_id", default="default"): vol.Coerce(str),
        vol.Required("seconds"): vol.Coerce(float),
    }
)
@callback
def websocket_capture_noise(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Capture the trailing buffer as a background-noise clip."""
    try:
        request = CaptureNoiseRequest.model_validate(msg)
    except ValueError as exc:
        connection.send_error(msg["id"], websocket_api.const.ERR_INVALID_FORMAT, str(exc))
        return

    manager = hass.data.get(DOMAIN, {}).get(AUDIO_KEY)
    if manager is None:
        connection.send_error(
            msg["id"],
            websocket_api.const.ERR_NOT_SUPPORTED,
            "Intentsity capture is not running",
        )
        return

    async def _capture() -> None:
        clip = await manager.async_capture_noise(request.assistant_id, request.seconds)
        if clip is None:
            connection.send_error(
                msg["id"],
                websocket_api.const.ERR_NOT_FOUND,
                f"No buffered audio for assistant {request.assistant_id}",
            )
            return
        connection.send_result(msg["id"], {"clip_id": clip.id, "filename": clip.filename})

    hass.async_create_task(_capture())


@websocket_api.decorators.websocket_command({vol.Required("type"): WS_CMD_ASSISTANTS})
@callback
def websocket_assistants(
    hass: HomeAssistant,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Report capture status per assistant, plus transport health."""
    domain_data = hass.data.get(DOMAIN, {})
    manager = domain_data.get(AUDIO_KEY)

    async def _status() -> None:
        clip_counts = await hass.async_add_executor_job(count_clips_by_assistant, hass)
        assistants: list[AssistantStatus] = []
        if manager is not None:
            for assistant_id in manager.buffers.assistant_ids:
                buffer = manager.buffers.get(assistant_id)
                if buffer is None:
                    continue
                assistants.append(
                    AssistantStatus(
                        assistant_id=assistant_id,
                        buffered_seconds=round(buffer.duration, 2),
                        sample_rate=buffer.audio_format.sample_rate,
                        sample_width=buffer.audio_format.sample_width,
                        channels=buffer.audio_format.channels,
                        last_audio_at=buffer.last_audio_at,
                        clip_count=clip_counts.get(assistant_id, 0),
                    )
                )
        # Assistants with clips on disk but no live audio still belong in the list.
        seen = {status.assistant_id for status in assistants}
        for assistant_id, count in sorted(clip_counts.items()):
            if assistant_id not in seen:
                assistants.append(AssistantStatus(assistant_id=assistant_id, clip_count=count))

        response = AssistantListResponse(
            assistants=assistants,
            udp_running=bool(manager and manager.udp_running),
            udp_port=manager.udp_port if manager else None,
            mqtt_connected=bool(manager and manager.mqtt_connected),
            webhook_url=domain_data.get("webhook_url"),
            labels=list(WAKE_LABELS),
        )
        connection.send_result(msg["id"], response.model_dump(mode="json"))

    hass.async_create_task(_status())
