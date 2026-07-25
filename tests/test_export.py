"""JSONL export. The output feeds a fine-tuning run, so shapes matter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json

from homeassistant.core import HomeAssistant

from custom_components.intentsity import db
from custom_components.intentsity.export import (
    _normalize_corrected_messages,
    _parse_tool_arguments,
    _stringify_tool_result,
    generate_corrected_jsonl,
)
from custom_components.intentsity.models import (
    Chat,
    ChatMessage,
    CorrectedChatExportRequest,
    CorrectedChatMessage,
)

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def _message(sender: str, text: str, data: dict | None = None) -> CorrectedChatMessage:
    return CorrectedChatMessage(timestamp=NOW, sender=sender, text=text, data=data or {})


def test_stringify_tool_result_variants() -> None:
    assert _stringify_tool_result(None) == ""
    assert _stringify_tool_result("plain") == "plain"
    assert _stringify_tool_result(42) == "42"
    assert _stringify_tool_result([1, 2]) == "[1, 2]"
    assert json.loads(_stringify_tool_result({"ok": True})) == {"ok": True}
    # The Anthropic-style content block list is flattened to its text.
    assert (
        _stringify_tool_result({"content": [{"text": "one"}, {"text": "two"}, {"x": 1}]})
        == "one\ntwo"
    )
    # An empty content list has no text to extract, so the dict is dumped.
    assert json.loads(_stringify_tool_result({"content": []})) == {"content": []}


def test_parse_tool_arguments() -> None:
    assert _parse_tool_arguments('{"a": 1}') == {"a": 1}
    assert _parse_tool_arguments("not json") == "not json"
    assert _parse_tool_arguments({"a": 1}) == {"a": 1}
    assert _parse_tool_arguments(None) is None


def test_normalize_plain_turns() -> None:
    output = _normalize_corrected_messages(
        [
            _message("system", "You are helpful", {"role": "system"}),
            _message("user", "Turn on the light"),
            _message("assistant", "Done"),
        ]
    )
    assert [entry["role"] for entry in output] == ["system", "user", "assistant"]
    assert output[2]["content"] == "Done"


def test_normalize_promotes_turn_after_system_to_user() -> None:
    # A run whose second turn is mislabeled would train the model to answer itself.
    output = _normalize_corrected_messages(
        [
            _message("system", "You are helpful", {"role": "system"}),
            _message("assistant", "Turn on the light"),
        ]
    )
    assert [entry["role"] for entry in output] == ["system", "user"]


def test_normalize_deduplicates_tool_call_ids() -> None:
    output = _normalize_corrected_messages(
        [
            _message(
                "assistant",
                "",
                {
                    "tool_calls": [
                        {"name": "set_light", "tool_args": '{"room": "kitchen"}'},
                        {"name": "set_light", "tool_call_id": "dup"},
                        {"name": "set_light", "tool_call_id": "dup"},
                        "bare_tool_name",
                    ]
                },
            ),
        ]
    )
    calls = output[0]["tool_calls"]
    ids = [call["tool_call_id"] for call in calls]
    assert len(ids) == len(set(ids))
    assert calls[0]["arguments"] == {"room": "kitchen"}
    assert calls[1]["tool_call_id"] == "dup"
    assert calls[3]["name"] == "bare_tool_name"
    # A tool-call-only turn carries no content key.
    assert "content" not in output[0]


def test_normalize_repairs_mismatched_tool_result_id() -> None:
    output = _normalize_corrected_messages(
        [
            _message("assistant", "", {"tool_calls": [{"name": "set_light", "id": "call-1"}]}),
            _message(
                "tool_result",
                "",
                {
                    "role": "tool_result",
                    "tool_name": "set_light",
                    "tool_call_id": "stale",
                    "tool_result": {"success": True},
                },
            ),
        ]
    )
    assert output[1]["role"] == "tool"
    assert output[1]["tool_call_id"] == "call-1"
    assert output[1]["tool_name"] == "set_light"
    assert json.loads(output[1]["content"]) == {"success": True}


def test_normalize_tool_result_without_prior_call_keeps_its_id() -> None:
    output = _normalize_corrected_messages(
        [_message("tool", "raw", {"tool_result": "raw", "tool_call_id": "call-9"})]
    )
    assert output[0] == {"role": "tool", "content": "raw", "tool_call_id": "call-9"}


def test_normalize_forces_assistant_for_tool_call_text() -> None:
    output = _normalize_corrected_messages([_message("user", "tool_call: set_light")])
    assert output[0]["role"] == "assistant"


def test_normalize_prefers_data_content_over_text() -> None:
    output = _normalize_corrected_messages(
        [_message("user", "stale text", {"role": "user", "content": "fresh content"})]
    )
    assert output[0]["content"] == "fresh content"


def test_normalize_unsets_pending_calls_after_plain_turn() -> None:
    output = _normalize_corrected_messages(
        [
            _message("assistant", "", {"tool_calls": [{"name": "set_light", "id": "call-1"}]}),
            _message("assistant", "All set"),
            _message("tool", "late", {"tool_result": "late", "tool_call_id": "call-2"}),
        ]
    )
    # The plain assistant turn closed the call, so the stale id is left alone.
    assert output[2]["tool_call_id"] == "call-2"


def test_normalize_ignores_non_list_tool_calls() -> None:
    output = _normalize_corrected_messages([_message("assistant", "hi", {"tool_calls": "oops"})])
    assert "tool_calls" not in output[0]
    assert output[0]["content"] == "hi"


def test_generate_corrected_jsonl_groups_runs_by_conversation(
    hass: HomeAssistant, clean_db: None
) -> None:
    for index, run_id in enumerate(("run-1", "run-2")):
        db.upsert_chat(
            hass,
            Chat(
                conversation_id="conv-1",
                pipeline_run_id=run_id,
                created_at=NOW + timedelta(minutes=index),
                run_timestamp=NOW + timedelta(minutes=index),
                messages=[ChatMessage(timestamp=NOW, sender="user", text="Original")],
            ),
        )
        db.upsert_corrected_chat(hass, "conv-1", run_id, [_message("user", f"Turn {index}")])

    # A second conversation, and an uncorrected chat that must not appear.
    db.upsert_chat(
        hass,
        Chat(
            conversation_id="conv-2",
            pipeline_run_id="run-1",
            created_at=NOW,
            run_timestamp=NOW,
            messages=[ChatMessage(timestamp=NOW, sender="user", text="Original")],
        ),
    )
    db.upsert_corrected_chat(hass, "conv-2", "run-1", [_message("user", "Other")])
    db.upsert_chat(
        hass,
        Chat(
            conversation_id="conv-3",
            pipeline_run_id="run-1",
            created_at=NOW,
            run_timestamp=NOW,
            messages=[ChatMessage(timestamp=NOW, sender="user", text="Never corrected")],
        ),
    )

    payload = generate_corrected_jsonl(hass, CorrectedChatExportRequest(limit=100))
    assert payload["count"] == 2
    lines = [json.loads(line) for line in payload["jsonl"].splitlines()]
    # One line per conversation, runs concatenated in chronological order.
    assert [msg["content"] for msg in lines[0]["messages"]] == ["Turn 0", "Turn 1"]
    assert [msg["content"] for msg in lines[1]["messages"]] == ["Other"]


def test_generate_corrected_jsonl_skips_empty_corrections(
    hass: HomeAssistant, clean_db: None
) -> None:
    db.upsert_chat(
        hass,
        Chat(
            conversation_id="conv-1",
            pipeline_run_id="run-1",
            created_at=NOW,
            run_timestamp=NOW,
            messages=[ChatMessage(timestamp=NOW, sender="user", text="Original")],
        ),
    )
    db.upsert_corrected_chat(hass, "conv-1", "run-1", [])

    payload = generate_corrected_jsonl(hass, CorrectedChatExportRequest(limit=100))
    assert payload == {"jsonl": "", "count": 0}


def test_generate_corrected_jsonl_skips_a_chat_without_a_correction(
    hass: HomeAssistant, clean_db: None, monkeypatch
) -> None:
    """The query asks for corrected chats only, but the export never trusts that."""
    monkeypatch.setattr(
        db,
        "fetch_recent_chats",
        lambda *_args, **_kwargs: [
            Chat(
                conversation_id="conv-1",
                pipeline_run_id="run-1",
                created_at=NOW,
                run_timestamp=NOW,
                messages=[ChatMessage(timestamp=NOW, sender="user", text="Original")],
            )
        ],
    )

    assert generate_corrected_jsonl(hass, CorrectedChatExportRequest(limit=100)) == {
        "jsonl": "",
        "count": 0,
    }


def test_generate_corrected_jsonl_respects_date_window(hass: HomeAssistant, clean_db: None) -> None:
    for conversation_id, created_at in (
        ("conv-old", NOW - timedelta(days=10)),
        ("conv-new", NOW),
    ):
        db.upsert_chat(
            hass,
            Chat(
                conversation_id=conversation_id,
                pipeline_run_id="run-1",
                created_at=created_at,
                run_timestamp=created_at,
                messages=[ChatMessage(timestamp=created_at, sender="user", text="Original")],
            ),
        )
        db.upsert_corrected_chat(
            hass, conversation_id, "run-1", [_message("user", conversation_id)]
        )

    payload = generate_corrected_jsonl(
        hass, CorrectedChatExportRequest(limit=100, start=NOW - timedelta(days=1))
    )
    assert payload["count"] == 1
    assert "conv-new" in payload["jsonl"]
