"""Pydantic models for both surfaces. Every external payload flows through here."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .const import (
    ALL_CLIP_LABELS,
    DEFAULT_CLIP_LIMIT,
    LABEL_UNLABELED,
    MAX_NOISE_CAPTURE_SECONDS,
    WAKE_LABELS,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _empty_to_none(value: object) -> object:
    if value == "":
        return None
    return value


# --- Intent trainer -------------------------------------------------------


class ChatMessage(BaseModel):
    id: int | None = None
    chat_id: str | None = None
    position: int | None = None
    timestamp: datetime = Field(default_factory=_utcnow)
    sender: str
    text: str
    data: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None


class CorrectedChatMessage(BaseModel):
    id: int | None = None
    corrected_chat_id: str | None = None
    original_message_id: int | None = None
    position: int = 0
    timestamp: datetime = Field(default_factory=_utcnow)
    sender: str
    text: str
    data: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None


class CorrectedChat(BaseModel):
    conversation_id: str
    pipeline_run_id: str
    original_conversation_id: str
    original_pipeline_run_id: str
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    messages: list[CorrectedChatMessage] = Field(default_factory=list)
    deleted_at: datetime | None = None


class Chat(BaseModel):
    conversation_id: str
    pipeline_run_id: str
    run_timestamp: datetime = Field(default_factory=_utcnow)
    created_at: datetime = Field(default_factory=_utcnow)
    messages: list[ChatMessage] = Field(default_factory=list)
    corrected: CorrectedChat | None = None
    deleted_at: datetime | None = None


class ChatListResponse(BaseModel):
    chats: list[Chat]
    total: int = 0


class ChatListRequest(BaseModel):
    limit: int
    offset: int = 0
    corrected: str = "all"
    start: datetime | None = None
    end: datetime | None = None

    @field_validator("corrected")
    @classmethod
    def _validate_corrected(cls, value: str) -> str:
        allowed = {"all", "corrected", "uncorrected"}
        if value not in allowed:
            raise ValueError("corrected must be one of: all, corrected, uncorrected")
        return value

    @field_validator("offset")
    @classmethod
    def _validate_offset(cls, value: int) -> int:
        if value < 0:
            raise ValueError("offset must be greater than or equal to zero")
        return value

    @field_validator("start", "end", mode="before")
    @classmethod
    def _coerce_empty(cls, value: object) -> object:
        return _empty_to_none(value)


class CorrectedChatSaveRequest(BaseModel):
    conversation_id: str
    pipeline_run_id: str
    messages: list[CorrectedChatMessage]


class TombstoneTarget(BaseModel):
    kind: str
    conversation_id: str | None = None
    pipeline_run_id: str | None = None
    message_id: int | None = None
    corrected_message_id: int | None = None

    @model_validator(mode="after")
    def _validate_kind(self) -> TombstoneTarget:
        if self.kind == "chat":
            if not self.conversation_id or not self.pipeline_run_id:
                raise ValueError("chat tombstone requires conversation_id and pipeline_run_id")
            return self
        if self.kind == "message":
            if self.message_id is None:
                raise ValueError("message tombstone requires message_id")
            return self
        if self.kind == "corrected_chat":
            if not self.conversation_id or not self.pipeline_run_id:
                raise ValueError(
                    "corrected_chat tombstone requires conversation_id and pipeline_run_id"
                )
            return self
        if self.kind == "corrected_message":
            if self.corrected_message_id is None:
                raise ValueError("corrected_message tombstone requires corrected_message_id")
            return self
        raise ValueError("invalid tombstone kind")


class TombstoneRequest(BaseModel):
    targets: list[TombstoneTarget]


class CorrectedChatExportRequest(BaseModel):
    limit: int
    start: datetime | None = None
    end: datetime | None = None

    @field_validator("start", "end", mode="before")
    @classmethod
    def _coerce_empty(cls, value: object) -> object:
        return _empty_to_none(value)


class CorrectedChatExportResponse(BaseModel):
    jsonl: str
    count: int = 0


# --- Wake word annotator --------------------------------------------------


class AudioFormat(BaseModel):
    """Frame format for one assistant's audio stream."""

    sample_rate: int = Field(gt=0, le=384_000)
    sample_width: int = Field(ge=1, le=4)
    channels: int = Field(ge=1, le=8)

    @property
    def bytes_per_frame(self) -> int:
        return self.sample_width * self.channels

    @property
    def frames_per_second(self) -> int:
        return self.sample_rate


class AudioInfoMessage(BaseModel):
    """Retained MQTT payload describing a device's audio format."""

    sample_rate: int = Field(gt=0, le=384_000)
    bits_per_sample: int
    channels: int = Field(ge=1, le=8)

    @field_validator("bits_per_sample")
    @classmethod
    def _validate_bits(cls, value: int) -> int:
        if value not in (8, 16, 24, 32):
            raise ValueError("bits_per_sample must be 8, 16, 24, or 32")
        return value

    def to_format(self) -> AudioFormat:
        return AudioFormat(
            sample_rate=self.sample_rate,
            sample_width=self.bits_per_sample // 8,
            channels=self.channels,
        )


class WakeEvent(BaseModel):
    """A wake-word detection reported over MQTT, webhook, or the UI."""

    assistant_id: str = "default"
    wake_word: str | None = None
    model: str | None = None
    confidence: float | None = None
    pre_duration: float | None = Field(default=None, gt=0, le=30)
    post_duration: float | None = Field(default=None, ge=0, le=30)
    label: str = LABEL_UNLABELED
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("assistant_id")
    @classmethod
    def _validate_assistant(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("assistant_id must not be empty")
        return value

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        if value not in ALL_CLIP_LABELS:
            raise ValueError(f"label must be one of: {', '.join(ALL_CLIP_LABELS)}")
        return value


class Clip(BaseModel):
    id: int | None = None
    filename: str
    timestamp: datetime = Field(default_factory=_utcnow)
    label: str = LABEL_UNLABELED
    assistant_id: str | None = None
    wake_word: str | None = None
    confidence: float | None = None
    duration: float | None = None
    sample_rate: int | None = None
    sample_width: int | None = None
    channels: int | None = None
    peaks: list[float] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        if value not in ALL_CLIP_LABELS:
            raise ValueError(f"label must be one of: {', '.join(ALL_CLIP_LABELS)}")
        return value


class ClipListRequest(BaseModel):
    limit: int = DEFAULT_CLIP_LIMIT
    offset: int = 0
    label: str | None = None
    assistant_id: str | None = None
    include_deleted: bool = False
    # "Any of the five labels" and "tombstoned only" are the annotator's other two
    # queues; neither is expressible as a single `label` value.
    labeled_only: bool = False
    deleted_only: bool = False
    start: datetime | None = None
    end: datetime | None = None

    @field_validator("offset")
    @classmethod
    def _validate_offset(cls, value: int) -> int:
        if value < 0:
            raise ValueError("offset must be greater than or equal to zero")
        return value

    @field_validator("label", "assistant_id", mode="before")
    @classmethod
    def _coerce_blank(cls, value: object) -> object:
        return _empty_to_none(value)

    @field_validator("start", "end", mode="before")
    @classmethod
    def _coerce_empty(cls, value: object) -> object:
        return _empty_to_none(value)

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str | None) -> str | None:
        if value is not None and value not in ALL_CLIP_LABELS:
            raise ValueError(f"label must be one of: {', '.join(ALL_CLIP_LABELS)}")
        return value


class ClipListResponse(BaseModel):
    clips: list[Clip] = Field(default_factory=list)
    total: int = 0
    unlabeled_total: int = 0
    labeled_total: int = 0
    deleted_total: int = 0
    label_counts: dict[str, int] = Field(default_factory=dict)


class ClipLabelRequest(BaseModel):
    clip_ids: list[int]
    label: str

    @field_validator("clip_ids")
    @classmethod
    def _validate_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("clip_ids must not be empty")
        return value

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        if value not in ALL_CLIP_LABELS:
            raise ValueError(f"label must be one of: {', '.join(ALL_CLIP_LABELS)}")
        return value


class ClipTombstoneRequest(BaseModel):
    clip_ids: list[int]
    restore: bool = False

    @field_validator("clip_ids")
    @classmethod
    def _validate_ids(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("clip_ids must not be empty")
        return value


class CaptureNoiseRequest(BaseModel):
    """Capture the trailing buffer as a background-noise clip."""

    assistant_id: str = "default"
    seconds: float = Field(gt=0, le=MAX_NOISE_CAPTURE_SECONDS)


class AssistantStatus(BaseModel):
    assistant_id: str
    buffered_seconds: float = 0.0
    sample_rate: int | None = None
    sample_width: int | None = None
    channels: int | None = None
    last_audio_at: datetime | None = None
    clip_count: int = 0


class AssistantListResponse(BaseModel):
    assistants: list[AssistantStatus] = Field(default_factory=list)
    udp_running: bool = False
    udp_port: int | None = None
    mqtt_connected: bool = False
    webhook_url: str | None = None
    labels: list[str] = Field(default_factory=lambda: list(WAKE_LABELS))
