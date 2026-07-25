"""HTTP surfaces: clip audio, the training archive, and the wake webhook."""

from __future__ import annotations

import io
import json
from typing import Any
import zipfile

from aiohttp import web
from homeassistant.core import HomeAssistant
import numpy as np
import pytest

from custom_components.intentsity import db
from custom_components.intentsity.const import (
    AUDIO_KEY,
    DOMAIN,
    LABEL_BACKGROUND_NOISE,
    LABEL_TRUE_POSITIVE,
)
from custom_components.intentsity.http import (
    ClipArchiveView,
    ClipAudioView,
    _resolve_clip_path,
    async_handle_wake_webhook,
    async_register_views,
)
from custom_components.intentsity.models import AudioFormat, WakeEvent


class _Request:
    """Enough of `web.Request` for these views."""

    def __init__(
        self,
        hass: HomeAssistant,
        query: dict[str, str] | None = None,
        body: Any = None,
        can_read_body: bool = False,
    ) -> None:
        self.app = {"hass": hass}
        self.query = query or {}
        self.can_read_body = can_read_body
        self._body = body

    async def json(self) -> Any:
        if isinstance(self._body, str):
            return json.loads(self._body)
        return self._body


def _write_clip_file(hass: HomeAssistant, filename: str) -> None:
    from custom_components.intentsity.audio import write_wav

    write_wav(
        db.get_clips_dir(hass) / filename,
        np.arange(1600, dtype="<i2"),
        AudioFormat(sample_rate=16000, sample_width=2, channels=1),
    )


# --- Path resolution ------------------------------------------------------


def test_resolve_clip_path(hass: HomeAssistant, clean_db: None) -> None:
    _write_clip_file(hass, "clip.wav")
    resolved = _resolve_clip_path(hass, "clip.wav")
    assert resolved is not None
    assert resolved.name == "clip.wav"


def test_resolve_clip_path_rejects_escapes(hass: HomeAssistant, clean_db: None) -> None:
    """A poisoned database row must not read files outside the clips directory."""
    db.get_clips_dir(hass).mkdir(parents=True, exist_ok=True)
    outside = db.get_storage_dir(hass) / "intentsity.db"
    assert outside.is_file()

    assert _resolve_clip_path(hass, f"../{outside.name}") is None
    assert _resolve_clip_path(hass, "nested/clip.wav") is None
    assert _resolve_clip_path(hass, "missing.wav") is None


def test_resolve_clip_path_rejects_a_directory(hass: HomeAssistant, clean_db: None) -> None:
    (db.get_clips_dir(hass) / "a_directory").mkdir(parents=True)
    assert _resolve_clip_path(hass, "a_directory") is None


# --- Clip audio -----------------------------------------------------------


async def test_clip_audio_view(hass: HomeAssistant, add_clip) -> None:
    clip_id = add_clip(filename="clip.wav")
    _write_clip_file(hass, "clip.wav")

    response = await ClipAudioView().get(_Request(hass), str(clip_id))
    assert isinstance(response, web.FileResponse)
    assert response.headers["Content-Type"] == "audio/wav"
    assert response.headers["Cache-Control"] == "private, max-age=86400"


async def test_clip_audio_view_rejects_a_non_numeric_id(
    hass: HomeAssistant, clean_db: None
) -> None:
    response = await ClipAudioView().get(_Request(hass), "abc")
    assert response.status == 400


async def test_clip_audio_view_missing_row(hass: HomeAssistant, clean_db: None) -> None:
    response = await ClipAudioView().get(_Request(hass), "404")
    assert response.status == 404
    assert response.text == "Clip not found"


async def test_clip_audio_view_missing_file(hass: HomeAssistant, add_clip) -> None:
    clip_id = add_clip(filename="gone.wav")
    response = await ClipAudioView().get(_Request(hass), str(clip_id))
    assert response.status == 404
    assert response.text == "Clip audio missing"


# --- Clip archive ---------------------------------------------------------


async def test_clip_archive_view(hass: HomeAssistant, add_clip) -> None:
    add_clip(filename="tp.wav", label=LABEL_TRUE_POSITIVE)
    add_clip(filename="noise.wav", label=LABEL_BACKGROUND_NOISE)
    # A row whose file is gone is skipped rather than failing the download.
    add_clip(filename="missing.wav", label=LABEL_TRUE_POSITIVE)
    _write_clip_file(hass, "tp.wav")
    _write_clip_file(hass, "noise.wav")

    response = await ClipArchiveView().get(_Request(hass, query={"limit": "10"}))
    assert response.headers["Content-Type"] == "application/zip"
    assert "intentsity_clips.zip" in response.headers["Content-Disposition"]

    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        names = set(archive.namelist())
        assert names == {"tp/tp.wav", "bgnoise/noise.wav", "labels.jsonl"}
        manifest = [json.loads(line) for line in archive.read("labels.jsonl").decode().splitlines()]
    assert {entry["filename"] for entry in manifest} == {"tp.wav", "noise.wav"}
    # The manifest is metadata only; envelopes and blobs stay out.
    assert "peaks" not in manifest[0]
    assert "data" not in manifest[0]


async def test_clip_archive_view_applies_filters(hass: HomeAssistant, add_clip) -> None:
    add_clip(filename="tp.wav", label=LABEL_TRUE_POSITIVE, assistant_id="kitchen")
    add_clip(filename="noise.wav", label=LABEL_BACKGROUND_NOISE, assistant_id="office")
    _write_clip_file(hass, "tp.wav")
    _write_clip_file(hass, "noise.wav")

    response = await ClipArchiveView().get(
        _Request(
            hass,
            query={
                "label": LABEL_TRUE_POSITIVE,
                "assistant_id": "kitchen",
                "labeled_only": "true",
                "include_deleted": "false",
            },
        )
    )
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        assert set(archive.namelist()) == {"tp/tp.wav", "labels.jsonl"}


async def test_clip_archive_view_with_no_matches(hass: HomeAssistant, clean_db: None) -> None:
    response = await ClipArchiveView().get(_Request(hass))
    assert response.status == 404
    assert response.text == "No clips match the filters"


@pytest.mark.parametrize(
    "query",
    [
        {"limit": "not-a-number"},
        {"label": "nonsense"},
        {"start": "not-a-date"},
    ],
)
async def test_clip_archive_view_rejects_bad_filters(
    hass: HomeAssistant, clean_db: None, query: dict[str, str]
) -> None:
    response = await ClipArchiveView().get(_Request(hass, query=query))
    assert response.status == 400
    assert response.text.startswith("Invalid filters")


# --- Wake webhook ---------------------------------------------------------


class _RecordingManager:
    def __init__(self) -> None:
        self.events: list[WakeEvent] = []

    async def async_capture_wake_event(self, event: WakeEvent) -> None:
        self.events.append(event)


@pytest.fixture
def manager(hass: HomeAssistant) -> _RecordingManager:
    manager = _RecordingManager()
    hass.data.setdefault(DOMAIN, {})[AUDIO_KEY] = manager
    return manager


async def test_wake_webhook_accepts_a_json_body(
    hass: HomeAssistant, manager: _RecordingManager
) -> None:
    response = await async_handle_wake_webhook(
        hass,
        "hook-1",
        _Request(
            hass,
            body={"assistant_id": "kitchen", "wake_word": "okay_nabu", "confidence": 0.9},
            can_read_body=True,
        ),
    )
    await hass.async_block_till_done()

    assert response.status == 202
    assert response.text == "accepted"
    assert manager.events[0].assistant_id == "kitchen"
    assert manager.events[0].wake_word == "okay_nabu"
    assert manager.events[0].confidence == 0.9


async def test_wake_webhook_accepts_query_params(
    hass: HomeAssistant, manager: _RecordingManager
) -> None:
    """ESPHome's http_request action is easiest to configure with query params."""
    response = await async_handle_wake_webhook(
        hass, "hook-1", _Request(hass, query={"assistant_id": "office", "label": "tp"})
    )
    await hass.async_block_till_done()

    assert response.status == 202
    assert manager.events[0].assistant_id == "office"
    assert manager.events[0].label == LABEL_TRUE_POSITIVE


async def test_wake_webhook_lets_query_params_win(
    hass: HomeAssistant, manager: _RecordingManager
) -> None:
    response = await async_handle_wake_webhook(
        hass,
        "hook-1",
        _Request(
            hass,
            query={"assistant_id": "query"},
            body={"assistant_id": "body"},
            can_read_body=True,
        ),
    )
    await hass.async_block_till_done()

    assert response.status == 202
    assert manager.events[0].assistant_id == "query"


async def test_wake_webhook_uses_defaults_for_an_empty_request(
    hass: HomeAssistant, manager: _RecordingManager
) -> None:
    response = await async_handle_wake_webhook(hass, "hook-1", _Request(hass))
    await hass.async_block_till_done()

    assert response.status == 202
    assert manager.events[0].assistant_id == "default"


@pytest.mark.parametrize("body", ["not json", ["a", "list"], None])
async def test_wake_webhook_ignores_a_non_dict_body(
    hass: HomeAssistant, manager: _RecordingManager, body: Any
) -> None:
    response = await async_handle_wake_webhook(
        hass, "hook-1", _Request(hass, body=body, can_read_body=True)
    )
    await hass.async_block_till_done()

    assert response.status == 202
    assert manager.events[0].assistant_id == "default"


async def test_wake_webhook_rejects_an_invalid_payload(
    hass: HomeAssistant, manager: _RecordingManager
) -> None:
    response = await async_handle_wake_webhook(
        hass, "hook-1", _Request(hass, query={"label": "nonsense"})
    )

    assert response.status == 400
    assert "label must be one of" in response.text
    assert manager.events == []


async def test_wake_webhook_without_capture_running(hass: HomeAssistant) -> None:
    hass.data.pop(DOMAIN, None)
    response = await async_handle_wake_webhook(hass, "hook-1", _Request(hass))

    assert response.status == 503
    assert response.text == "Intentsity capture is not running"


# --- Registration ---------------------------------------------------------


async def test_async_register_views(hass: HomeAssistant) -> None:
    registered: list[Any] = []
    hass.http = type("_Http", (), {"register_view": lambda _self, view: registered.append(view)})()

    async_register_views(hass)
    assert [type(view) for view in registered] == [ClipAudioView, ClipArchiveView]
