"""The websocket API both panel surfaces talk to.

Handlers are `@callback`s that spawn a task, so every test blocks on
`async_block_till_done()` before inspecting the fake connection.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
import pytest

from custom_components.intentsity import websocket
from custom_components.intentsity.const import (
    AUDIO_KEY,
    DEFAULT_CLIP_LIMIT,
    DEFAULT_EVENT_LIMIT,
    DOMAIN,
    LABEL_TRUE_POSITIVE,
    SIGNAL_CLIP_RECORDED,
    SIGNAL_EVENT_RECORDED,
    WAKE_LABELS,
    WS_CMD_ASSISTANTS,
    WS_CMD_CAPTURE_NOISE,
    WS_CMD_EXPORT_CORRECTED_CHATS,
    WS_CMD_LABEL_CLIP,
    WS_CMD_LIST_CHATS,
    WS_CMD_LIST_CLIPS,
    WS_CMD_SAVE_CORRECTED_CHAT,
    WS_CMD_SUBSCRIBE_CHATS,
    WS_CMD_SUBSCRIBE_CLIPS,
    WS_CMD_TOMBSTONE,
    WS_CMD_TOMBSTONE_CLIPS,
)
from custom_components.intentsity.models import (
    Chat,
    ChatMessage,
    Clip,
    ClipListResponse,
)
from custom_components.intentsity.utils import parse_timestamp

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


class _Connection:
    """Minimal stand-in for `ActiveConnection`."""

    def __init__(self) -> None:
        self.results: list[tuple[int, dict | None]] = []
        self.messages: list[dict] = []
        self.errors: list[tuple[int, str, str]] = []
        self.subscriptions: dict[int, Any] = {}

    def send_result(self, msg_id: int, payload: dict | None = None) -> None:
        self.results.append((msg_id, payload))

    def send_message(self, message: dict) -> None:
        self.messages.append(message)

    def send_error(self, msg_id: int, code: str, message: str) -> None:
        self.errors.append((msg_id, code, message))


@pytest.fixture
def connection() -> _Connection:
    return _Connection()


def _chat(conversation_id: str = "conv-1") -> Chat:
    return Chat(
        conversation_id=conversation_id,
        pipeline_run_id="run-1",
        created_at=NOW,
        run_timestamp=NOW,
        messages=[ChatMessage(timestamp=NOW, sender="user", text="Hi")],
    )


def _clip(clip_id: int = 7) -> Clip:
    return Clip(
        id=clip_id,
        filename=f"clip-{clip_id}.wav",
        timestamp=NOW,
        assistant_id="kitchen",
        duration=2.0,
        sample_rate=16000,
        sample_width=2,
        channels=1,
    )


# --- Registration ---------------------------------------------------------


async def test_async_register_commands(hass: HomeAssistant) -> None:
    websocket.async_register_commands(hass)
    handlers = hass.data[websocket_api.const.DOMAIN]
    for command in (
        WS_CMD_LIST_CHATS,
        WS_CMD_SUBSCRIBE_CHATS,
        WS_CMD_SAVE_CORRECTED_CHAT,
        WS_CMD_EXPORT_CORRECTED_CHATS,
        WS_CMD_TOMBSTONE,
        WS_CMD_LIST_CLIPS,
        WS_CMD_SUBSCRIBE_CLIPS,
        WS_CMD_LABEL_CLIP,
        WS_CMD_TOMBSTONE_CLIPS,
        WS_CMD_CAPTURE_NOISE,
        WS_CMD_ASSISTANTS,
    ):
        assert command in handlers


# --- Chats ----------------------------------------------------------------


async def test_list_chats(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    called: dict[str, Any] = {}

    def _fetch_chats_page(_hass, limit, offset, corrected, start, end):
        called.update(limit=limit, offset=offset, corrected=corrected, start=start, end=end)
        return [_chat()], 1

    monkeypatch.setattr(websocket, "fetch_chats_page", _fetch_chats_page)

    websocket.websocket_list_chats(
        hass,
        connection,
        {
            "id": 1,
            "type": WS_CMD_LIST_CHATS,
            "limit": DEFAULT_EVENT_LIMIT,
            "offset": 20,
            "corrected": "uncorrected",
            "start": "2026-01-01T12:00:00+00:00",
            "end": "2026-01-31T12:00:00+00:00",
        },
    )
    await hass.async_block_till_done()

    msg_id, payload = connection.results[0]
    assert msg_id == 1
    assert payload["chats"][0]["conversation_id"] == "conv-1"
    assert payload["total"] == 1
    assert parse_timestamp(payload["chats"][0]["run_timestamp"]) == NOW
    assert called["limit"] == DEFAULT_EVENT_LIMIT
    assert called["offset"] == 20
    assert called["corrected"] is False
    assert called["start"] == parse_timestamp("2026-01-01T12:00:00+00:00")


@pytest.mark.parametrize(
    ("filter_value", "expected"),
    [("all", None), ("corrected", True), ("uncorrected", False)],
)
async def test_list_chats_corrected_filter(
    hass: HomeAssistant,
    connection: _Connection,
    monkeypatch,
    filter_value: str,
    expected: bool | None,
) -> None:
    seen: dict[str, Any] = {}

    def _fetch_chats_page(_hass, limit, offset, corrected, start, end):
        seen["corrected"] = corrected
        return [], 0

    monkeypatch.setattr(websocket, "fetch_chats_page", _fetch_chats_page)
    websocket.websocket_list_chats(
        hass,
        connection,
        {
            "id": 1,
            "type": WS_CMD_LIST_CHATS,
            "limit": DEFAULT_EVENT_LIMIT,
            "corrected": filter_value,
        },
    )
    await hass.async_block_till_done()

    assert seen["corrected"] is expected


async def test_list_chats_accepts_a_response_object(
    hass: HomeAssistant, connection: _Connection, monkeypatch
) -> None:
    """`fetch_chats_page` may return a ready-made response instead of a tuple."""
    from custom_components.intentsity.models import ChatListResponse

    monkeypatch.setattr(
        websocket,
        "fetch_chats_page",
        lambda *_args: (ChatListResponse(chats=[_chat()], total=9), 0),
    )
    websocket.websocket_list_chats(
        hass, connection, {"id": 1, "type": WS_CMD_LIST_CHATS, "limit": DEFAULT_EVENT_LIMIT}
    )
    await hass.async_block_till_done()

    assert connection.results[0][1]["total"] == 9


async def test_subscribe_chats(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    monkeypatch.setattr(websocket, "fetch_chats", lambda *_args: [_chat()])

    websocket.websocket_subscribe_chats(
        hass, connection, {"id": 5, "type": WS_CMD_SUBSCRIBE_CHATS, "limit": DEFAULT_EVENT_LIMIT}
    )
    await hass.async_block_till_done()

    assert connection.results == [(5, None)]
    assert 5 in connection.subscriptions
    # The initial snapshot arrives as an event, with no `total`.
    assert connection.messages[0]["event"]["chats"][0]["conversation_id"] == "conv-1"
    assert "total" not in connection.messages[0]["event"]

    async_dispatcher_send(hass, SIGNAL_EVENT_RECORDED)
    await hass.async_block_till_done()
    assert len(connection.messages) == 2

    connection.subscriptions[5]()
    async_dispatcher_send(hass, SIGNAL_EVENT_RECORDED)
    await hass.async_block_till_done()
    assert len(connection.messages) == 2


async def test_save_corrected_chat(
    hass: HomeAssistant, connection: _Connection, monkeypatch
) -> None:
    saved: dict[str, Any] = {}
    signals: list[tuple] = []

    def _upsert(_hass, conversation_id, pipeline_run_id, messages):
        saved.update(
            conversation_id=conversation_id, pipeline_run_id=pipeline_run_id, messages=messages
        )
        return "corrected-1"

    monkeypatch.setattr(websocket, "upsert_corrected_chat", _upsert)
    from homeassistant.helpers.dispatcher import async_dispatcher_connect

    async_dispatcher_connect(hass, SIGNAL_EVENT_RECORDED, lambda *args: signals.append(args))

    websocket.websocket_save_corrected_chat(
        hass,
        connection,
        {
            "id": 3,
            "type": WS_CMD_SAVE_CORRECTED_CHAT,
            "conversation_id": "conv-1",
            "pipeline_run_id": "run-1",
            "messages": [
                {
                    "position": 0,
                    "timestamp": NOW.isoformat(),
                    "sender": "user",
                    "text": "Corrected",
                    "data": {},
                }
            ],
        },
    )
    await hass.async_block_till_done()

    assert connection.results == [(3, None)]
    assert saved["conversation_id"] == "conv-1"
    assert saved["messages"][0].text == "Corrected"
    assert signals


async def test_export_corrected_chats(
    hass: HomeAssistant, connection: _Connection, monkeypatch
) -> None:
    seen: dict[str, Any] = {}

    def _generate(_hass, request):
        seen["limit"] = request.limit
        seen["start"] = request.start
        return {"jsonl": '{"messages": []}', "count": 1}

    monkeypatch.setattr(websocket, "generate_corrected_jsonl", _generate)

    websocket.websocket_export_corrected_chats(
        hass,
        connection,
        {
            "id": 4,
            "type": WS_CMD_EXPORT_CORRECTED_CHATS,
            "limit": 10,
            "start": "2026-01-01T00:00:00+00:00",
            "end": "",
        },
    )
    await hass.async_block_till_done()

    assert connection.results[0][1]["count"] == 1
    assert seen["limit"] == 10
    assert seen["start"] == parse_timestamp("2026-01-01T00:00:00+00:00")


async def test_tombstone_targets(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        websocket,
        "tombstone_targets",
        lambda _hass, targets: captured.update(targets=targets),
    )

    websocket.websocket_tombstone_targets(
        hass,
        connection,
        {
            "id": 6,
            "type": WS_CMD_TOMBSTONE,
            "targets": [
                {"kind": "chat", "conversation_id": "conv-1", "pipeline_run_id": "run-1"},
                {"kind": "message", "message_id": 12},
            ],
        },
    )
    await hass.async_block_till_done()

    assert connection.results == [(6, None)]
    assert [target.kind for target in captured["targets"]] == ["chat", "message"]


# --- Clips ----------------------------------------------------------------


async def test_list_clips(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fetch(_hass, request):
        seen["request"] = request
        return ClipListResponse(
            clips=[_clip()],
            total=1,
            unlabeled_total=1,
            labeled_total=0,
            deleted_total=0,
            label_counts={"tp": 0},
        )

    monkeypatch.setattr(websocket, "fetch_clips_page", _fetch)

    websocket.websocket_list_clips(
        hass,
        connection,
        {
            "id": 1,
            "type": WS_CMD_LIST_CLIPS,
            "limit": DEFAULT_CLIP_LIMIT,
            "offset": 24,
            "label": LABEL_TRUE_POSITIVE,
            "assistant_id": "kitchen",
            "include_deleted": True,
            "labeled_only": True,
            "deleted_only": False,
            "start": "2026-01-01T00:00:00+00:00",
        },
    )
    await hass.async_block_till_done()

    msg_id, payload = connection.results[0]
    assert msg_id == 1
    # The panel plays audio through the authenticated view, not the raw filename.
    assert payload["clips"][0]["audio_url"] == "/api/intentsity/clips/7/audio"
    assert payload["unlabeled_total"] == 1
    assert payload["label_counts"] == {"tp": 0}

    request = seen["request"]
    assert request.limit == DEFAULT_CLIP_LIMIT
    assert request.offset == 24
    assert request.label == LABEL_TRUE_POSITIVE
    assert request.assistant_id == "kitchen"
    assert request.include_deleted is True
    assert request.labeled_only is True
    assert request.deleted_only is False
    assert request.start == parse_timestamp("2026-01-01T00:00:00+00:00")


async def test_list_clips_defaults(
    hass: HomeAssistant, connection: _Connection, monkeypatch
) -> None:
    seen: dict[str, Any] = {}

    def _fetch(_hass, request):
        seen["request"] = request
        return ClipListResponse()

    monkeypatch.setattr(websocket, "fetch_clips_page", _fetch)
    websocket.websocket_list_clips(hass, connection, {"id": 1, "type": WS_CMD_LIST_CLIPS})
    await hass.async_block_till_done()

    request = seen["request"]
    assert request.limit == DEFAULT_CLIP_LIMIT
    assert request.offset == 0
    assert request.label is None
    assert request.assistant_id is None
    assert request.include_deleted is False
    assert request.labeled_only is False
    assert request.deleted_only is False


async def test_subscribe_clips(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    monkeypatch.setattr(
        websocket, "fetch_clips_page", lambda *_args: ClipListResponse(clips=[_clip()], total=1)
    )

    websocket.websocket_subscribe_clips(
        hass, connection, {"id": 8, "type": WS_CMD_SUBSCRIBE_CLIPS, "deleted_only": True}
    )
    await hass.async_block_till_done()

    assert connection.results == [(8, None)]
    assert (
        connection.messages[0]["event"]["clips"][0]["audio_url"] == "/api/intentsity/clips/7/audio"
    )

    async_dispatcher_send(hass, SIGNAL_CLIP_RECORDED)
    await hass.async_block_till_done()
    assert len(connection.messages) == 2

    connection.subscriptions[8]()
    async_dispatcher_send(hass, SIGNAL_CLIP_RECORDED)
    await hass.async_block_till_done()
    assert len(connection.messages) == 2


async def test_label_clips(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    captured: dict[str, Any] = {}
    signals: list[tuple] = []
    from homeassistant.helpers.dispatcher import async_dispatcher_connect

    async_dispatcher_connect(hass, SIGNAL_CLIP_RECORDED, lambda *args: signals.append(args))

    def _label(_hass, clip_ids, label):
        captured.update(clip_ids=clip_ids, label=label)
        return len(clip_ids)

    monkeypatch.setattr(websocket, "label_clips", _label)

    websocket.websocket_label_clips(
        hass,
        connection,
        {
            "id": 9,
            "type": WS_CMD_LABEL_CLIP,
            "clip_ids": ["3", 4],
            "label": LABEL_TRUE_POSITIVE,
        },
    )
    await hass.async_block_till_done()

    assert connection.results == [(9, {"updated": 2})]
    assert captured == {"clip_ids": [3, 4], "label": LABEL_TRUE_POSITIVE}
    assert signals


async def test_tombstone_clips(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _tombstone(_hass, clip_ids, restore):
        captured.update(clip_ids=clip_ids, restore=restore)
        return 1

    monkeypatch.setattr(websocket, "tombstone_clips", _tombstone)

    websocket.websocket_tombstone_clips(
        hass,
        connection,
        {"id": 10, "type": WS_CMD_TOMBSTONE_CLIPS, "clip_ids": [3], "restore": True},
    )
    await hass.async_block_till_done()

    assert connection.results == [(10, {"updated": 1})]
    assert captured == {"clip_ids": [3], "restore": True}


# --- Noise capture --------------------------------------------------------


class _FakeManager:
    def __init__(self, clip: Clip | None) -> None:
        self._clip = clip
        self.calls: list[tuple] = []
        self.buffers = _FakeBuffers()
        self.udp_running = True
        self.udp_port = 6056
        self.mqtt_connected = False

    async def async_capture_noise(self, assistant_id: str, seconds: float) -> Clip | None:
        self.calls.append((assistant_id, seconds))
        return self._clip


class _FakeBuffer:
    def __init__(self) -> None:
        from custom_components.intentsity.models import AudioFormat

        self.audio_format = AudioFormat(sample_rate=16000, sample_width=2, channels=1)
        self.duration = 4.567
        self.last_audio_at = NOW


class _FakeBuffers:
    def __init__(self) -> None:
        self._buffers = {"kitchen": _FakeBuffer()}

    @property
    def assistant_ids(self) -> list[str]:
        return list(self._buffers)

    def get(self, assistant_id: str):
        return self._buffers.get(assistant_id)


async def test_capture_noise(hass: HomeAssistant, connection: _Connection) -> None:
    manager = _FakeManager(_clip(11))
    hass.data.setdefault(DOMAIN, {})[AUDIO_KEY] = manager

    websocket.websocket_capture_noise(
        hass,
        connection,
        {"id": 12, "type": WS_CMD_CAPTURE_NOISE, "assistant_id": "kitchen", "seconds": 5},
    )
    await hass.async_block_till_done()

    assert connection.results == [(12, {"clip_id": 11, "filename": "clip-11.wav"})]
    assert manager.calls == [("kitchen", 5.0)]


async def test_capture_noise_rejects_out_of_range_seconds(
    hass: HomeAssistant, connection: _Connection
) -> None:
    hass.data.setdefault(DOMAIN, {})[AUDIO_KEY] = _FakeManager(_clip())

    websocket.websocket_capture_noise(
        hass, connection, {"id": 13, "type": WS_CMD_CAPTURE_NOISE, "seconds": 500}
    )
    await hass.async_block_till_done()

    assert connection.results == []
    assert connection.errors[0][:2] == (13, websocket_api.const.ERR_INVALID_FORMAT)


async def test_capture_noise_without_capture_running(
    hass: HomeAssistant, connection: _Connection
) -> None:
    hass.data.pop(DOMAIN, None)

    websocket.websocket_capture_noise(
        hass, connection, {"id": 14, "type": WS_CMD_CAPTURE_NOISE, "seconds": 3}
    )
    await hass.async_block_till_done()

    assert connection.errors[0][:2] == (14, websocket_api.const.ERR_NOT_SUPPORTED)


async def test_capture_noise_without_buffered_audio(
    hass: HomeAssistant, connection: _Connection
) -> None:
    hass.data.setdefault(DOMAIN, {})[AUDIO_KEY] = _FakeManager(None)

    websocket.websocket_capture_noise(
        hass, connection, {"id": 15, "type": WS_CMD_CAPTURE_NOISE, "seconds": 3}
    )
    await hass.async_block_till_done()

    assert connection.errors[0][:2] == (15, websocket_api.const.ERR_NOT_FOUND)
    assert "default" in connection.errors[0][2]


# --- Assistants -----------------------------------------------------------


async def test_assistants(hass: HomeAssistant, connection: _Connection, monkeypatch) -> None:
    manager = _FakeManager(None)
    hass.data.setdefault(DOMAIN, {})[AUDIO_KEY] = manager
    hass.data[DOMAIN]["webhook_url"] = "https://ha.local/api/webhook/abc"
    monkeypatch.setattr(
        websocket, "count_clips_by_assistant", lambda _hass: {"kitchen": 3, "garage": 1}
    )

    websocket.websocket_assistants(hass, connection, {"id": 16, "type": WS_CMD_ASSISTANTS})
    await hass.async_block_till_done()

    _msg_id, payload = connection.results[0]
    assert payload["udp_running"] is True
    assert payload["udp_port"] == 6056
    assert payload["mqtt_connected"] is False
    assert payload["webhook_url"] == "https://ha.local/api/webhook/abc"
    assert payload["labels"] == list(WAKE_LABELS)

    kitchen, garage = payload["assistants"]
    assert kitchen["assistant_id"] == "kitchen"
    assert kitchen["buffered_seconds"] == 4.57
    assert kitchen["sample_rate"] == 16000
    assert kitchen["clip_count"] == 3
    # An assistant with clips but no live buffer still shows up.
    assert garage == {
        "assistant_id": "garage",
        "buffered_seconds": 0.0,
        "sample_rate": None,
        "sample_width": None,
        "channels": None,
        "last_audio_at": None,
        "clip_count": 1,
    }


async def test_assistants_without_capture_running(
    hass: HomeAssistant, connection: _Connection, monkeypatch
) -> None:
    hass.data.pop(DOMAIN, None)
    monkeypatch.setattr(websocket, "count_clips_by_assistant", lambda _hass: {})

    websocket.websocket_assistants(hass, connection, {"id": 17, "type": WS_CMD_ASSISTANTS})
    await hass.async_block_till_done()

    _msg_id, payload = connection.results[0]
    assert payload == {
        "assistants": [],
        "udp_running": False,
        "udp_port": None,
        "mqtt_connected": False,
        "webhook_url": None,
        "labels": list(WAKE_LABELS),
    }


async def test_assistants_skips_a_vanished_buffer(
    hass: HomeAssistant, connection: _Connection, monkeypatch
) -> None:
    manager = _FakeManager(None)
    # A buffer cleared between listing the IDs and reading it must not crash.
    manager.buffers._buffers["kitchen"] = None
    hass.data.setdefault(DOMAIN, {})[AUDIO_KEY] = manager
    monkeypatch.setattr(websocket, "count_clips_by_assistant", lambda _hass: {})

    websocket.websocket_assistants(hass, connection, {"id": 18, "type": WS_CMD_ASSISTANTS})
    await hass.async_block_till_done()

    assert connection.results[0][1]["assistants"] == []
