"""Payload validation. Every external input is parsed through these models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.intentsity import models
from custom_components.intentsity.const import (
    LABEL_BACKGROUND_NOISE,
    LABEL_TRUE_POSITIVE,
    LABEL_UNLABELED,
)

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def test_chat_defaults() -> None:
    chat = models.Chat(conversation_id="conv-1", pipeline_run_id="run-1")
    assert chat.messages == []
    assert chat.corrected is None
    assert chat.deleted_at is None
    assert chat.run_timestamp.tzinfo is not None


def test_chat_message_carries_data() -> None:
    message = models.ChatMessage(timestamp=NOW, sender="user", text="Hello", data={"meta": 1})
    assert message.data == {"meta": 1}
    assert message.position is None


def test_chat_list_request_normalizes_blank_dates() -> None:
    request = models.ChatListRequest(limit=10, start="", end="")
    assert request.start is None
    assert request.end is None
    assert request.corrected == "all"


@pytest.mark.parametrize("value", ["all", "corrected", "uncorrected"])
def test_chat_list_request_accepts_corrected_filters(value: str) -> None:
    assert models.ChatListRequest(limit=1, corrected=value).corrected == value


def test_chat_list_request_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="corrected must be one of"):
        models.ChatListRequest(limit=1, corrected="maybe")
    with pytest.raises(ValueError, match="offset must be greater than"):
        models.ChatListRequest(limit=1, offset=-1)


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "chat", "conversation_id": "c", "pipeline_run_id": "r"},
        {"kind": "message", "message_id": 4},
        {"kind": "corrected_chat", "conversation_id": "c", "pipeline_run_id": "r"},
        {"kind": "corrected_message", "corrected_message_id": 9},
    ],
)
def test_tombstone_target_valid_kinds(payload: dict) -> None:
    assert models.TombstoneTarget.model_validate(payload).kind == payload["kind"]


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        ({"kind": "chat", "conversation_id": "c"}, "chat tombstone requires"),
        ({"kind": "message"}, "message tombstone requires"),
        ({"kind": "corrected_chat", "pipeline_run_id": "r"}, "corrected_chat tombstone"),
        ({"kind": "corrected_message"}, "corrected_message tombstone"),
        ({"kind": "clip"}, "invalid tombstone kind"),
    ],
)
def test_tombstone_target_invalid(payload: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        models.TombstoneTarget.model_validate(payload)


def test_audio_format_derived_properties() -> None:
    audio_format = models.AudioFormat(sample_rate=16000, sample_width=2, channels=2)
    assert audio_format.bytes_per_frame == 4
    assert audio_format.frames_per_second == 16000


@pytest.mark.parametrize(
    "payload",
    [
        {"sample_rate": 0, "sample_width": 2, "channels": 1},
        {"sample_rate": 16000, "sample_width": 5, "channels": 1},
        {"sample_rate": 16000, "sample_width": 2, "channels": 0},
        {"sample_rate": 500_000, "sample_width": 2, "channels": 1},
    ],
)
def test_audio_format_rejects_out_of_range(payload: dict) -> None:
    with pytest.raises(ValueError):
        models.AudioFormat.model_validate(payload)


@pytest.mark.parametrize(("bits", "width"), [(8, 1), (16, 2), (24, 3), (32, 4)])
def test_audio_info_to_format(bits: int, width: int) -> None:
    info = models.AudioInfoMessage(sample_rate=16000, bits_per_sample=bits, channels=1)
    assert info.to_format().sample_width == width


def test_audio_info_rejects_odd_bit_depth() -> None:
    with pytest.raises(ValueError, match="bits_per_sample must be"):
        models.AudioInfoMessage(sample_rate=16000, bits_per_sample=12, channels=1)


def test_wake_event_defaults() -> None:
    event = models.WakeEvent()
    assert event.assistant_id == "default"
    assert event.label == LABEL_UNLABELED
    assert event.pre_duration is None
    assert event.post_duration is None


def test_wake_event_trims_assistant_id() -> None:
    assert models.WakeEvent(assistant_id="  kitchen  ").assistant_id == "kitchen"


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        ({"assistant_id": "   "}, "must not be empty"),
        ({"label": "maybe"}, "label must be one of"),
        ({"pre_duration": 0}, "greater than 0"),
        ({"pre_duration": 31}, "less than or equal to 30"),
        ({"post_duration": -1}, "greater than or equal to 0"),
    ],
)
def test_wake_event_rejects_bad_input(payload: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        models.WakeEvent.model_validate(payload)


def test_clip_defaults_to_unlabeled() -> None:
    clip = models.Clip(filename="clip.wav")
    assert clip.label == LABEL_UNLABELED
    assert clip.peaks == []
    assert clip.data == {}


def test_clip_rejects_unknown_label() -> None:
    with pytest.raises(ValueError, match="label must be one of"):
        models.Clip(filename="clip.wav", label="great")


def test_clip_list_request_blank_strings_become_none() -> None:
    request = models.ClipListRequest(limit=10, label="", assistant_id="", start="", end="")
    assert request.label is None
    assert request.assistant_id is None
    assert request.start is None
    assert request.end is None
    assert request.labeled_only is False
    assert request.deleted_only is False


def test_clip_list_request_validates() -> None:
    with pytest.raises(ValueError, match="offset must be greater than"):
        models.ClipListRequest(limit=10, offset=-1)
    with pytest.raises(ValueError, match="label must be one of"):
        models.ClipListRequest(limit=10, label="great")
    assert models.ClipListRequest(limit=10, label=LABEL_TRUE_POSITIVE).label == "tp"


def test_clip_label_request_requires_ids() -> None:
    with pytest.raises(ValueError, match="clip_ids must not be empty"):
        models.ClipLabelRequest(clip_ids=[], label=LABEL_TRUE_POSITIVE)
    with pytest.raises(ValueError, match="label must be one of"):
        models.ClipLabelRequest(clip_ids=[1], label="great")
    assert models.ClipLabelRequest(clip_ids=[1, 2], label=LABEL_BACKGROUND_NOISE).clip_ids == [1, 2]


def test_clip_tombstone_request_requires_ids() -> None:
    with pytest.raises(ValueError, match="clip_ids must not be empty"):
        models.ClipTombstoneRequest(clip_ids=[])
    assert models.ClipTombstoneRequest(clip_ids=[3]).restore is False


def test_capture_noise_request_bounds() -> None:
    assert models.CaptureNoiseRequest(seconds=5).assistant_id == "default"
    with pytest.raises(ValueError):
        models.CaptureNoiseRequest(seconds=0)
    with pytest.raises(ValueError):
        models.CaptureNoiseRequest(seconds=31)


def test_assistant_list_response_defaults_labels() -> None:
    response = models.AssistantListResponse()
    assert response.labels == ["tp", "tn", "fp", "fn", "bgnoise"]
    assert response.udp_running is False
    assert response.webhook_url is None
