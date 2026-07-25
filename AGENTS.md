# Intentsity — Agent Playbook

This repository ships one Home Assistant custom integration with two surfaces: wake-word clip
annotation and Assist intent training. It replaces two earlier projects — a HACS integration
(`hacs-intentsity`) and a standalone FastAPI service / HA add-on (`esphome-wakeword-debug`) —
which now share a single database, a single panel, and a single config entry.

This document is the source of truth for how to work in this repo. Read it before planning a
change.

## Invariants

Violating any of these is a defect, not a tradeoff.

- **Never intercept the Assist pipeline.** Chat recording reads `pipeline_debug` from
  `KEY_ASSIST_PIPELINE` and the conversation chat logs. It does not monkey-patch Home
  Assistant internals, wrap pipeline methods, or sit in the request path. Logging is
  observational; a failure in Intentsity must never break a voice command.
- **Never block the event loop.** Every database read or write, WAV write, and filesystem walk
  goes through `hass.async_add_executor_job`. `ASYNC` lint rules are enabled and are not
  advisory.
- **Validate every external payload through Pydantic.** UDP packets, MQTT messages, webhook
  bodies, and websocket commands all parse into models in `models.py`. Bare dicts crossing a
  trust boundary are forbidden. Voluptuous schemas guard websocket command *shape*; Pydantic
  guards the values.
- **Audio capture is one-way.** Intentsity buffers what devices send. It never sends audio,
  commands, or configuration back to a device.
- **Deletes are tombstones.** Setting `deleted_at` is the delete. Rows and files disappear only
  through retention pruning, which is opt-in.
- **One instance, one database.** `config/intentsity/intentsity.db` holds chats, corrections,
  and clip metadata. The config flow enforces a single entry.
- **Keep the buffer in numpy.** `AudioBuffer` stores whole numpy chunks and trims by frame
  count. Do not reintroduce per-sample Python appends — at 48 kHz that was roughly a million
  interpreter operations per second per assistant.

## Repository map

| Path | Role |
| --- | --- |
| `custom_components/intentsity/__init__.py` | Setup, unload, reload, webhook and panel registration, legacy clip import |
| `custom_components/intentsity/const.py` | Domain constants, storage layout, label taxonomy, websocket command names |
| `custom_components/intentsity/models.py` | Every Pydantic model: requests, responses, wake events, audio formats |
| `custom_components/intentsity/db.py` | SQLAlchemy schema, the DB client, and in-place schema migrations |
| `custom_components/intentsity/coordinator.py` | Reads Assist pipeline debug runs into `Chat` rows |
| `custom_components/intentsity/capture.py` | `CaptureManager`: transports in, clips out, retention pruning |
| `custom_components/intentsity/audio.py` | Rolling PCM buffers, waveform envelopes, WAV writing |
| `custom_components/intentsity/udp.py` | asyncio UDP endpoint and the `WWD2`/`WWD1`/raw packet formats |
| `custom_components/intentsity/websocket.py` | All eleven websocket commands |
| `custom_components/intentsity/http.py` | Clip audio and archive views, plus the wake webhook handler |
| `custom_components/intentsity/export.py` | Corrected-conversation JSONL generation |
| `custom_components/intentsity/sensor.py` | The two review-queue sensors |
| `custom_components/intentsity/config_flow.py` | Single-instance config flow and the options flow |
| `custom_components/intentsity/utils.py` | Small shared helpers (option coercion, timestamps) |
| `custom_components/intentsity/panel.js` | **Build artifact.** Never edit by hand |
| `frontend/src/` | React panel sources |
| `frontend/src/ds/` | **Vendor copy** of `DesignSystem/`. Regenerate, never edit |
| `DesignSystem/` | Source of truth for all components, tokens, and brand marks |
| `brand/` | PNGs rasterized from `DesignSystem/assets/`, for the HA brands repo only |
| `esphome/` | Example device configs, one per transport |
| `tests/` | Pytest suite. Behavior without a test is broken by default |
| `.github/workflows/` | `validate.yaml` (HACS, hassfest, python, frontend) and `release.yaml` |

## Workflow

1. **Plan before editing.** Name the files you will touch, any schema change, and the tests
   you will add.
2. **Match the surrounding code.** Comment density, naming, and idiom are already consistent;
   new code should be indistinguishable from what is there. Comments explain non-obvious
   *why*, never restate the code.
3. **Test edge cases, not happy paths.** The interesting failures live in malformed payloads,
   format changes mid-capture, empty buffers, missing files, and migration from old schemas.
4. **Run the full gate before opening a PR** (below). Paste the coverage summary into the PR
   description.
5. **Update the docs in the same commit.** If the API shape, schema, options, or panel behavior
   changes and `README.md` does not, the change is incomplete.
6. **Conventional commits, one per unit of work.** `feat(capture): adopt inline wake format`.

## Quality gate

```bash
uv run pytest --cov=custom_components.intentsity --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
cd frontend && npm run check
```

- **Coverage floor: 90%.** The suite currently sits at 100%; do not ratchet it down.
- Line length is 100. Target Python is 3.13.
- ASCII-only source unless a file already requires Unicode.
- Logs must be actionable and low-noise. `_LOGGER.exception` only where a stack trace
  genuinely helps; a malformed device payload is a `warning` with the payload's problem, not a
  traceback.

## Testing notes

The suite runs on `pytest-homeassistant-custom-component`, which has sharp edges worth knowing
before you spend an hour on them:

- The `hass` fixture reuses **one config directory across all tests**, so `config/intentsity/`
  must be wiped per test. The autouse `isolated_storage` fixture in `tests/conftest.py` does
  this; do not bypass it.
- Sockets are blocked by default. Tests that bind one need the `socket_enabled` fixture, and
  should bind port `0`.
- **Voluptuous defaults are applied by the websocket dispatcher, not by the handler.** A test
  that calls a `@websocket_command` handler directly must supply every field the Pydantic model
  requires, including ones with schema defaults such as `limit`.
- `assist_pipeline` depends on `conversation`, which needs `homeassistant.exposed_entities`.
  The bare harness does not set that up, so tests that load the integration take the
  `assist_pipeline` fixture, which sets up `homeassistant` first.
- Re-running `_async_initialize` on an already-loaded entry re-registers the webhook and raises
  `ValueError: Handler is already defined!`. Patch `_async_register_webhook` in those tests.
- `log_level = "WARNING"` in `pyproject.toml` keeps SQLAlchemy's echo out of failure output.
  `log_cli_level` does not have this effect.
- The dev group carries dependencies Intentsity never imports — `hassil`,
  `home-assistant-intents`, `mutagen`, `ha-ffmpeg`, `pymicro-vad`, `pyspeex-noise`,
  `paho-mqtt`. Production Home Assistant installs those on demand for the components the
  integration depends on; the test harness does not, so importing `assist_pipeline` fails
  without them. They are pinned to the versions the pinned core's manifests request.

## Dependencies and CI

`homeassistant` and `pytest-homeassistant-custom-component` are pinned exactly and must be
bumped as a pair: each p-h-c-c release targets one core version, and Python support moves with
them (0.13.316 is the last supporting 3.13, which is why `requires-python` has an upper bound).
Everything Home Assistant itself pins — `orjson`, `sqlalchemy`, `voluptuous` — gets a lower
bound only; a tighter floor just makes the resolver unsatisfiable.

`uv.lock` is committed and CI runs `uv sync --locked`, so a dependency change that does not
include a re-locked `uv.lock` fails the build. Run `uv lock` in the same commit.

`validate.yaml` also rebuilds the panel and fails if `panel.js` or `frontend/src/ds/` differ
from what is committed — HACS ships those artifacts, so a stale bundle reaches users.

## Schema changes

The database is upgraded in place by `_ensure_schema`, which inspects `PRAGMA table_info` and
rebuilds tables when the shape is from an older release. Existing installs matter — someone is
running every schema version this project has shipped.

When you change the schema:

1. Bump `DB_SCHEMA_VERSION` in `const.py`.
2. Add the migration path to `_ensure_schema`, keeping the existing branches working.
3. Add a test that builds the *old* schema with raw `sqlite3`, runs `init_db`, and asserts the
   data survived. `tests/test_db.py` has three of these to copy from.
4. Bump the version in both `manifest.json` and `pyproject.toml` — they must match.

Never ship a schema change that loses data. In local development you can delete
`config/intentsity/intentsity.db` and re-run setup; in production that is not an option.

## Frontend

`DesignSystem/` is authoritative. `frontend/src/ds/` is a build-time copy so the shipped bundle
has no runtime dependency on that tree, and `custom_components/intentsity/panel.js` is the
esbuild output.

```bash
cd frontend
npm run sync-ds   # DesignSystem/ -> src/ds/
npm run build     # src/ -> custom_components/intentsity/panel.js
npm run dev       # build, watching
npm run check     # resolve and typecheck without writing panel.js
```

To change a component's appearance, edit it in `DesignSystem/` and re-sync. Editing
`frontend/src/ds/` directly means the next sync silently reverts your work. Commit the rebuilt
`panel.js` with the source change — HACS ships the artifact, not a build.

The brand marks live in `DesignSystem/assets/`. `sync-ds` vendors the SVGs and the panel inlines
`icon.svg` (see `components/Brand.jsx`), so no image is fetched at runtime. `logo.svg` is *not*
used in the panel: its wordmark is dark ink on transparent and disappears on the dark theme, so
the sidebar pairs the icon with the wordmark as live text. If a light-ink lockup is ever
supplied, that workaround can go. `brand/*.png` are for the Home Assistant brands repository;
regeneration steps are in `brand/README.md`.

The panel must render correctly on desktop and mobile, and must follow Home Assistant's dark
mode unless the reviewer has explicitly picked a theme.

## Release checklist

- [ ] `manifest.json` and `pyproject.toml` versions match and are bumped (release CI enforces this)
- [ ] `uv.lock` re-locked if any dependency moved
- [ ] `panel.js` rebuilt from current `frontend/src/`
- [ ] Dependencies pinned to compatible ranges — no bare `*`
- [ ] README options table, API tables, and storage layout reflect reality
- [ ] Full gate green on macOS and Linux; coverage ≥ 90%
- [ ] Schema migration tested from every prior shape, if the schema moved
- [ ] Commits ordered logically (docs → feat → fix → test → chore)

## Triage

**Panel does not load.** Check the browser console for CSP violations, confirm
`panel.js` exists in `custom_components/intentsity/`, and confirm the static path
`/intentsity_panel.js` is registered. The URL carries a random cache-buster per setup, so a
stale bundle usually means the file was not rebuilt.

**No clips are captured.** Check `intentsity/assistants` (the panel shows it) for
`udp_running`, `mqtt_connected`, and per-assistant `buffered_seconds`. Buffered audio but no
clips means wake events are not arriving; audio at 0 s means the transport is not delivering.
For MQTT, `mosquitto_sub -t 'assist/debug/#' -v` settles it quickly.

**Clips are silent or garbled.** The buffer format does not match what the device sends. `WWD2`
packets and retained `audio_info` messages both declare a format; the options-flow values are
only a fallback for senders that declare nothing.

**Chats are not recorded.** Assist pipeline debug data is what feeds the recorder. Confirm the
pipeline actually ran, and note that unfinished runs are deliberately skipped — recording one
mid-flight would truncate the conversation.

If something feels fragile, it is. Fix it properly rather than hoping nobody notices.
