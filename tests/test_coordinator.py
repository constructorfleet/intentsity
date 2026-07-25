"""Chat-log recording from Assist pipeline debug data."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.components.assist_pipeline.pipeline import (
    KEY_ASSIST_PIPELINE,
    Pipeline,
    PipelineEvent,
    PipelineEventType,
    PipelineRunDebug,
)
from homeassistant.components.conversation.chat_log import DATA_CHAT_LOGS, SystemContent
from homeassistant.core import HomeAssistant
import pytest

from custom_components.intentsity import db
from custom_components.intentsity.coordinator import (
    IntentsityCoordinator,
    _process_intent_end,
    _process_intent_progress,
    _process_intent_start,
    _process_run_start,
)
from custom_components.intentsity.models import Chat
from custom_components.intentsity.utils import parse_timestamp

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def _make_pipeline() -> Pipeline:
    return Pipeline(
        conversation_engine="conversation.home_assistant",
        conversation_language="en",
        language="en",
        name="Default",
        stt_engine=None,
        stt_language=None,
        tts_engine=None,
        tts_language=None,
        tts_voice=None,
        wake_word_entity=None,
        wake_word_id=None,
    )


class _ChatLogStub:
    def __init__(self, content) -> None:
        self.content = content


class _SystemContent(SystemContent):
    def as_dict(self) -> dict[str, Any]:
        return {"role": "system", "content": self.content}


def _chat(conversation_id: str = "conv-1") -> Chat:
    return Chat(
        conversation_id=conversation_id,
        pipeline_run_id="run-1",
        run_timestamp=NOW,
        messages=[],
    )


def _run_debug(*events: PipelineEvent) -> PipelineRunDebug:
    run_debug = PipelineRunDebug()
    run_debug.events.extend(events)
    return run_debug


# --- RUN_START ------------------------------------------------------------


def test_process_run_start() -> None:
    event = PipelineEvent(PipelineEventType.RUN_START, {"conversation_id": "conv-1"})
    chat = _process_run_start(event, "run-1", NOW)

    assert chat is not None
    assert chat.conversation_id == "conv-1"
    assert chat.pipeline_run_id == "run-1"
    assert chat.run_timestamp == parse_timestamp(NOW)
    assert chat.messages == []


@pytest.mark.parametrize("data", [None, {}, {"conversation_id": ""}])
def test_process_run_start_without_a_conversation(data) -> None:
    assert (
        _process_run_start(PipelineEvent(PipelineEventType.RUN_START, data), "run-1", NOW) is None
    )


# --- INTENT_START ---------------------------------------------------------


def test_process_intent_start_appends_the_user_turn() -> None:
    chat = _chat("conv-2")
    event = PipelineEvent(
        PipelineEventType.INTENT_START,
        {"conversation_id": "conv-2", "intent_input": "Hello", "meta": "x"},
    )

    assert _process_intent_start(event, chat) is chat
    message = chat.messages[0]
    assert message.sender == "user"
    assert message.text == "Hello"
    # `intent_input` is promoted to text, so it must not be duplicated in data.
    assert message.data == {"conversation_id": "conv-2", "meta": "x"}
    assert message.timestamp == parse_timestamp(event.timestamp)


def test_process_intent_start_without_data() -> None:
    chat = _chat()
    assert _process_intent_start(PipelineEvent(PipelineEventType.INTENT_START, None), chat) is None
    assert chat.messages == []


def test_process_intent_start_without_input() -> None:
    chat = _chat()
    _process_intent_start(PipelineEvent(PipelineEventType.INTENT_START, {"other": 1}), chat)
    assert chat.messages[0].text == ""


# --- INTENT_PROGRESS ------------------------------------------------------


def test_process_intent_progress_records_each_delta_shape() -> None:
    chat = _chat("conv-3")

    for data, expected_sender, expected_text in (
        ({"tool_calls": [{"name": "foo"}], "role": "tool_calls"}, "tool_calls", ""),
        ({"tool_result": {"result": "ok"}, "role": "tool_result"}, "tool_result", "ok"),
        ({"content": "Hi", "role": "assistant"}, "assistant", "Hi"),
    ):
        event = PipelineEvent(PipelineEventType.INTENT_PROGRESS, {"chat_log_delta": data})
        assert _process_intent_progress(event, chat) is chat
        message = chat.messages[-1]
        assert (message.sender, message.text) == (expected_sender, expected_text)
        assert message.timestamp == parse_timestamp(event.timestamp)

    assert len(chat.messages) == 3


@pytest.mark.parametrize(
    ("tool_result", "expected"),
    [
        ({"result": "ok"}, "ok"),
        ({}, ""),
        (None, ""),
        ("plain", "plain"),
        (42, "42"),
    ],
)
def test_process_intent_progress_stringifies_tool_results(tool_result, expected: str) -> None:
    chat = _chat()
    _process_intent_progress(
        PipelineEvent(
            PipelineEventType.INTENT_PROGRESS, {"chat_log_delta": {"tool_result": tool_result}}
        ),
        chat,
    )
    assert chat.messages[0].text == expected
    assert chat.messages[0].sender == "tool_result"


def test_process_intent_progress_prefers_tool_calls_over_content() -> None:
    """A delta with both is a tool-call turn; its content is not the reply."""
    chat = _chat()
    event = PipelineEvent(
        PipelineEventType.INTENT_PROGRESS,
        {"chat_log_delta": {"tool_calls": [{"name": "foo"}], "content": "Ignored"}},
    )

    assert _process_intent_progress(event, chat) is chat
    assert len(chat.messages) == 1
    assert chat.messages[0].text == ""
    assert chat.messages[0].sender == "tool_calls"


@pytest.mark.parametrize("data", [None, {}, {"chat_log_delta": None}, {"chat_log_delta": {}}])
def test_process_intent_progress_without_a_delta(data) -> None:
    chat = _chat()
    assert (
        _process_intent_progress(PipelineEvent(PipelineEventType.INTENT_PROGRESS, data), chat)
        is None
    )
    assert chat.messages == []


def test_process_intent_progress_ignores_an_unknown_delta() -> None:
    chat = _chat()
    event = PipelineEvent(
        PipelineEventType.INTENT_PROGRESS, {"chat_log_delta": {"role": "assistant"}}
    )

    assert _process_intent_progress(event, chat) is chat
    assert chat.messages == []


# --- INTENT_END -----------------------------------------------------------


def test_process_intent_end_records_the_speech() -> None:
    chat = _chat()
    event = PipelineEvent(
        PipelineEventType.INTENT_END,
        {"response": {"speech": {"plain": {"speech": "Turning on the light"}}}},
    )

    assert _process_intent_end(event, chat) is chat
    assert chat.messages[0].sender == "assistant"
    assert chat.messages[0].text == "Turning on the light"
    assert chat.messages[0].data == {}


def test_process_intent_end_records_home_assistant_intent_output() -> None:
    chat = _chat()
    event = PipelineEvent(
        PipelineEventType.INTENT_END,
        {
            "processed_locally": False,
            "intent_output": {
                "response": {"speech": {"plain": {"speech": "Done"}}},
                "conversation_id": "conv-1",
                "continue_conversation": False,
            },
        },
    )

    assert _process_intent_end(event, chat) is chat
    assert chat.messages[0].sender == "assistant"
    assert chat.messages[0].text == "Done"


@pytest.mark.parametrize(
    "data",
    [
        None,
        {},
        {"response": {}},
        {"response": {"speech": {}}},
        {"response": {"speech": {"plain": {"speech": ""}}}},
        {"intent_output": {"response": {}}},
        {"intent_output": {"response": {"speech": {"plain": {"speech": ""}}}}},
    ],
)
def test_process_intent_end_without_speech(data) -> None:
    chat = _chat()
    assert _process_intent_end(PipelineEvent(PipelineEventType.INTENT_END, data), chat) is None
    assert chat.messages == []


# --- Whole-run assembly ---------------------------------------------------


def _full_run() -> PipelineRunDebug:
    return _run_debug(
        PipelineEvent(PipelineEventType.RUN_START, {"conversation_id": "conv-4"}),
        PipelineEvent(PipelineEventType.INTENT_START, {"intent_input": "Ping"}),
        PipelineEvent(
            PipelineEventType.INTENT_PROGRESS,
            {"chat_log_delta": {"content": "Pong", "role": "assistant"}},
        ),
        PipelineEvent(
            PipelineEventType.INTENT_END,
            {"intent_output": {"response": {"speech": {"plain": {"speech": "Pong"}}}}},
        ),
    )


def test_process_pipeline_run_prepends_system_content(hass: HomeAssistant) -> None:
    hass.data[DATA_CHAT_LOGS] = {
        "conv-4": _ChatLogStub([_SystemContent(content="A"), _SystemContent(content="B")])
    }
    coordinator = IntentsityCoordinator(hass)

    chat = coordinator._process_pipeline_run(_full_run(), "run-1")
    assert chat is not None
    assert chat.messages[0].sender == "system"
    # Multiple system blocks are joined, and their dicts merged into data.
    assert chat.messages[0].text == "A\n\nB"
    assert chat.messages[0].data["role"] == "system"
    assert [message.sender for message in chat.messages] == [
        "system",
        "user",
        "assistant",
        "assistant",
    ]


def test_process_pipeline_run_without_chat_logs(hass: HomeAssistant) -> None:
    coordinator = IntentsityCoordinator(hass)
    chat = coordinator._process_pipeline_run(_full_run(), "run-1")
    assert chat is not None
    assert [message.sender for message in chat.messages] == ["user", "assistant", "assistant"]


def test_process_pipeline_run_without_a_matching_log(hass: HomeAssistant) -> None:
    hass.data[DATA_CHAT_LOGS] = {"other": _ChatLogStub([])}
    coordinator = IntentsityCoordinator(hass)

    chat = coordinator._process_pipeline_run(_full_run(), "run-1")
    assert chat is not None
    assert chat.messages[0].sender == "user"


def test_process_pipeline_run_without_system_content(hass: HomeAssistant) -> None:
    hass.data[DATA_CHAT_LOGS] = {"conv-4": _ChatLogStub([])}
    coordinator = IntentsityCoordinator(hass)

    chat = coordinator._process_pipeline_run(_full_run(), "run-1")
    assert chat is not None
    assert chat.messages[0].sender == "user"


def test_process_pipeline_run_skips_an_unfinished_run(hass: HomeAssistant) -> None:
    """A run with no INTENT_END is still in flight; recording it would truncate it."""
    hass.data[DATA_CHAT_LOGS] = {"conv-4": _ChatLogStub([])}
    coordinator = IntentsityCoordinator(hass)
    run = _run_debug(
        PipelineEvent(PipelineEventType.RUN_START, {"conversation_id": "conv-4"}),
        PipelineEvent(PipelineEventType.INTENT_START, {"intent_input": "Ping"}),
    )

    assert coordinator._process_pipeline_run(run, "run-1") is None


def test_process_pipeline_run_without_a_run_start(hass: HomeAssistant) -> None:
    hass.data[DATA_CHAT_LOGS] = {"conv-4": _ChatLogStub([])}
    coordinator = IntentsityCoordinator(hass)
    run = _run_debug(PipelineEvent(PipelineEventType.INTENT_START, {"intent_input": "Ping"}))

    assert coordinator._process_pipeline_run(run, "run-1") is None


def test_process_pipeline_run_ignores_unhandled_events(hass: HomeAssistant) -> None:
    hass.data[DATA_CHAT_LOGS] = {"conv-4": _ChatLogStub([])}
    coordinator = IntentsityCoordinator(hass)
    run = _full_run()
    run.events.insert(1, PipelineEvent(PipelineEventType.STT_START, {"anything": 1}))

    chat = coordinator._process_pipeline_run(run, "run-1")
    assert chat is not None
    assert [message.sender for message in chat.messages] == ["user", "assistant", "assistant"]


# --- Update cycle ---------------------------------------------------------


class _PipelineData:
    def __init__(self, debug: dict) -> None:
        self.pipeline_debug = debug


@pytest.fixture
def pipeline_env(hass: HomeAssistant, monkeypatch):
    """Wire up one pipeline whose debug store the test controls."""
    pipeline = _make_pipeline()
    hass.data[DATA_CHAT_LOGS] = {"conv-4": _ChatLogStub([])}
    monkeypatch.setattr(
        "custom_components.intentsity.coordinator.async_get_pipelines",
        lambda _hass: [pipeline],
    )
    monkeypatch.setattr(
        "custom_components.intentsity.coordinator.async_get_pipeline",
        lambda _hass, _pid: pipeline,
    )
    monkeypatch.setattr(db, "count_uncorrected_chats", lambda _hass: 2)
    monkeypatch.setattr(db, "count_unlabeled_clips", lambda _hass: 5)
    monkeypatch.setattr(db, "fetch_recent_chats", lambda _hass: [])
    return pipeline


async def test_async_update_data_persists_a_chat(
    hass: HomeAssistant, monkeypatch, pipeline_env: Pipeline
) -> None:
    run_debug = _full_run()
    hass.data[KEY_ASSIST_PIPELINE] = _PipelineData({pipeline_env.id: {"run-1": run_debug}})

    persisted: dict[str, Any] = {}
    signals: list[str] = []

    def _upsert_chat(_hass, chat):
        persisted["chat"] = chat
        return chat.conversation_id, chat.pipeline_run_id

    monkeypatch.setattr(db, "upsert_chat", _upsert_chat)
    monkeypatch.setattr(
        "custom_components.intentsity.coordinator.async_dispatcher_send",
        lambda _hass, signal: signals.append(signal),
    )

    data = await IntentsityCoordinator(hass)._async_update_data()

    assert persisted["chat"].conversation_id == "conv-4"
    assert persisted["chat"].pipeline_run_id == "run-1"
    assert persisted["chat"].run_timestamp == parse_timestamp(run_debug.timestamp)
    assert signals == ["intentsity_event_recorded"]
    assert data == {"pipelines": {}, "uncorrected_count": 2, "unlabeled_clips": 5}


async def test_async_update_data_skips_already_recorded_runs(
    hass: HomeAssistant, monkeypatch, pipeline_env: Pipeline
) -> None:
    hass.data[KEY_ASSIST_PIPELINE] = _PipelineData({pipeline_env.id: {"run-1": _full_run()}})
    monkeypatch.setattr(db, "fetch_recent_chats", lambda _hass: [_chat("conv-4")])

    upserts: list[Chat] = []
    monkeypatch.setattr(db, "upsert_chat", lambda _hass, chat: upserts.append(chat))

    await IntentsityCoordinator(hass)._async_update_data()
    assert upserts == []


async def test_async_update_data_skips_runs_that_yield_no_chat(
    hass: HomeAssistant, monkeypatch, pipeline_env: Pipeline
) -> None:
    unfinished = _run_debug(
        PipelineEvent(PipelineEventType.RUN_START, {"conversation_id": "conv-4"})
    )
    hass.data[KEY_ASSIST_PIPELINE] = _PipelineData({pipeline_env.id: {"run-1": unfinished}})

    upserts: list[Chat] = []
    monkeypatch.setattr(db, "upsert_chat", lambda _hass, chat: upserts.append(chat))

    data = await IntentsityCoordinator(hass)._async_update_data()
    assert upserts == []
    assert data["uncorrected_count"] == 2


async def test_async_update_data_without_debug_runs(
    hass: HomeAssistant, monkeypatch, pipeline_env: Pipeline
) -> None:
    hass.data[KEY_ASSIST_PIPELINE] = _PipelineData({pipeline_env.id: {}})
    monkeypatch.setattr(db, "upsert_chat", lambda _hass, _chat: None)

    data = await IntentsityCoordinator(hass)._async_update_data()
    assert data["unlabeled_clips"] == 5


async def test_async_update_data_survives_an_unresolvable_pipeline(
    hass: HomeAssistant, monkeypatch, pipeline_env: Pipeline, caplog: pytest.LogCaptureFixture
) -> None:
    hass.data[KEY_ASSIST_PIPELINE] = _PipelineData({pipeline_env.id: {"run-1": _full_run()}})

    def _raise(_hass, _pipeline_id):
        raise RuntimeError("gone")

    monkeypatch.setattr("custom_components.intentsity.coordinator.async_get_pipeline", _raise)
    upserts: list[Chat] = []
    monkeypatch.setattr(db, "upsert_chat", lambda _hass, chat: upserts.append(chat))

    data = await IntentsityCoordinator(hass)._async_update_data()
    assert upserts == []
    assert data["uncorrected_count"] == 2


async def test_async_update_data_without_pipeline_data(hass: HomeAssistant) -> None:
    hass.data.pop(KEY_ASSIST_PIPELINE, None)
    assert await IntentsityCoordinator(hass)._async_update_data() == {}
