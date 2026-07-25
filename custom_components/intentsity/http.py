"""Authenticated HTTP views for clip audio, plus the ESPHome wake webhook."""

from __future__ import annotations

import io
import logging
from pathlib import Path
import zipfile

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from . import db
from .const import DOMAIN
from .models import ClipListRequest, WakeEvent

_LOGGER = logging.getLogger(__name__)


def _resolve_clip_path(hass: HomeAssistant, filename: str) -> Path | None:
    """Resolve a clip filename inside the clips directory, or None if it escapes.

    Filenames come from the database rather than the request, but resolving and
    re-checking the parent keeps a poisoned row from reading arbitrary files.
    """
    clips_dir = db.get_clips_dir(hass).resolve()
    candidate = (clips_dir / filename).resolve()
    if candidate.parent != clips_dir or not candidate.is_file():
        return None
    return candidate


class ClipAudioView(HomeAssistantView):
    """Serve one clip's WAV audio."""

    url = "/api/intentsity/clips/{clip_id}/audio"
    name = "api:intentsity:clip_audio"
    requires_auth = True

    async def get(self, request: web.Request, clip_id: str) -> web.StreamResponse:
        hass: HomeAssistant = request.app["hass"]
        try:
            numeric_id = int(clip_id)
        except ValueError:
            return web.Response(status=400, text="clip_id must be an integer")

        clip = await hass.async_add_executor_job(db.fetch_clip, hass, numeric_id)
        if clip is None:
            return web.Response(status=404, text="Clip not found")

        path = await hass.async_add_executor_job(_resolve_clip_path, hass, clip.filename)
        if path is None:
            return web.Response(status=404, text="Clip audio missing")

        return web.FileResponse(
            path,
            headers={
                "Content-Type": "audio/wav",
                # Clip files are immutable once written.
                "Cache-Control": "private, max-age=86400",
            },
        )


class ClipArchiveView(HomeAssistantView):
    """Download the filtered clip set as a zip with a labels manifest."""

    url = "/api/intentsity/clips/archive"
    name = "api:intentsity:clip_archive"
    requires_auth = True

    async def get(self, request: web.Request) -> web.StreamResponse:
        hass: HomeAssistant = request.app["hass"]
        query = dict(request.query)
        try:
            list_request = ClipListRequest(
                limit=int(query.pop("limit", 1000)),
                **{
                    key: value
                    for key, value in query.items()
                    if key in {"label", "assistant_id", "start", "end"}
                },
                include_deleted=query.get("include_deleted") == "true",
                labeled_only=query.get("labeled_only") == "true",
            )
        except (ValueError, TypeError) as exc:
            return web.Response(status=400, text=f"Invalid filters: {exc}")

        clips = await hass.async_add_executor_job(db.fetch_clips_for_export, hass, list_request)
        if not clips:
            return web.Response(status=404, text="No clips match the filters")

        def _build() -> bytes:
            clips_dir = db.get_clips_dir(hass)
            manifest_lines = []
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
                for clip in clips:
                    source = clips_dir / clip.filename
                    if not source.is_file():
                        continue
                    # Group by label so the archive is ready for model training.
                    archive.write(source, f"{clip.label}/{clip.filename}")
                    manifest_lines.append(clip.model_dump_json(exclude={"peaks", "data"}))
                archive.writestr("labels.jsonl", "\n".join(manifest_lines))
            return payload.getvalue()

        body = await hass.async_add_executor_job(_build)
        return web.Response(
            body=body,
            headers={
                "Content-Type": "application/zip",
                "Content-Disposition": 'attachment; filename="intentsity_clips.zip"',
            },
        )


async def async_handle_wake_webhook(
    hass: HomeAssistant, webhook_id: str, request: web.Request
) -> web.Response:
    """Capture a clip from an ESPHome wake-word detection.

    Registered as a webhook so devices need no credentials: the random webhook ID
    is the shared secret, and it never leaves the local network.
    """
    payload: dict = {}
    if request.can_read_body:
        try:
            body = await request.json()
        except ValueError:
            body = None
        if isinstance(body, dict):
            payload = body
    # ESPHome's http_request action is easiest to configure with query params.
    payload = {**payload, **dict(request.query)}

    try:
        event = WakeEvent.model_validate(payload)
    except ValueError as exc:
        _LOGGER.warning("Rejected wake webhook payload: %s", exc)
        return web.Response(status=400, text=str(exc))

    manager = hass.data.get(DOMAIN, {}).get("audio")
    if manager is None:
        return web.Response(status=503, text="Intentsity capture is not running")

    # Capture waits out the post-roll window, so let the device's request return
    # immediately rather than holding the connection open for seconds.
    hass.async_create_task(manager.async_capture_wake_event(event))
    return web.Response(status=202, text="accepted")


def async_register_views(hass: HomeAssistant) -> None:
    hass.http.register_view(ClipAudioView())
    hass.http.register_view(ClipArchiveView())
