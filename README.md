# Intentsity

A Home Assistant custom integration for building training data out of your own voice
assistant. One sidebar panel, two surfaces:

- **Wake word** — captures the audio around every wake-word detection from your ESPHome
  satellites, then lets you label each clip true positive, true negative, false positive,
  false negative, or background noise. Export the labeled set as a zip grouped by label,
  ready for a microWakeWord training run.
- **Intent training** — records every Assist pipeline conversation, lets you correct what
  the assistant *should* have said or called, and exports the corrections as JSONL for
  fine-tuning.

Both surfaces are observational. Chat logging reads the Assist pipeline's debug data and
never intercepts the pipeline; audio capture buffers what devices send and never talks back
to them. Nothing leaves your network.

## Requirements

- Home Assistant 2026.1.0 or newer
- For wake-word capture: one or more ESPHome devices running `micro_wake_word`
- Optionally an MQTT broker, if you use the MQTT transport rather than UDP

## Installation

### HACS

1. **HACS → Integrations → ⋮ → Custom repositories**, add
   `https://github.com/constructorfleet/intentsity` as an **Integration**.
2. Install **Intentsity** and restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → Intentsity**.

### Manual

Copy `custom_components/intentsity/` into your `config/custom_components/` directory,
restart, then add the integration from **Settings → Devices & Services**.

Only one instance is allowed — it owns both surfaces, one database, and one panel.

## Wiring up a device

Audio and wake events travel separately: Intentsity keeps a rolling PCM buffer per
assistant, and a wake event tells it which slice of that buffer to cut into a clip. Pick one
audio transport and one event transport.

### Audio: UDP (recommended)

Devices built with the satellite1 [`wake_audio_stream`](https://github.com/constructorfleet/satellite1-esphome)
component stream the exact audio microWakeWord processes — int16 mono 16 kHz — as raw
datagrams. No broker, minimal overhead, and it includes audio where *no* wake word fired,
which is exactly what false-negative training data needs.

Point the component at your Home Assistant host on the UDP port from the options flow
(default `6056`). Three packet shapes are accepted:

| Shape | Assistant ID from | Format from |
| --- | --- | --- |
| `WWD2` (preferred) | packet header | packet header |
| `WWD1` (legacy) | packet header | configured fallback |
| Raw PCM | sender IP address | configured fallback |

`WWD2` is the only shape that keeps both identity and format intact through a UDP proxy such
as Traefik. If you must use raw PCM, set **Assistant ID for unlabeled datagrams** in the
options flow — but then every device shares one buffer.

See [esphome/udp-satellite1.yaml](esphome/udp-satellite1.yaml).

### Audio: MQTT

Devices publish base64-encoded PCM to `assist/debug/+/pcm`. The segment matching `+` is the
assistant ID. A retained message on `assist/debug/+/audio_info` declares the device's format:

```json
{ "sample_rate": 48000, "bits_per_sample": 32, "channels": 1 }
```

Each assistant gets its own buffer, so devices at different sample rates coexist. This costs
noticeably more traffic than UDP. See [esphome/mqtt-i2s.yaml](esphome/mqtt-i2s.yaml).

### Wake events: webhook

Each install generates a random webhook ID on first setup. The panel's assistant list shows
the full URL; devices POST to it with no credentials — the random ID is the shared secret,
and it never leaves your network.

```
POST /api/webhook/<your-webhook-id>?assistant_id=kitchen&wake_word=okay_nabu
```

Fields may arrive as query parameters or a JSON body (query parameters win on conflict):
`assistant_id`, `wake_word`, `model`, `confidence`, `pre_duration`, `post_duration`, `label`.
The request returns `202` immediately rather than holding the connection open through the
post-roll window.

### Wake events: MQTT

Devices publish to `assist/debug/+/events`:

```json
{ "event": "wake", "wake_word": "okay_nabu", "rate": 16000, "bits": 16, "channels": 1 }
```

`rate`/`bits`/`channels` are optional; when all three are present they update the buffer
format before the clip is cut. Payloads with an `event` other than `wake` are ignored, so the
topic can carry other device chatter.

## Configuration

Everything is set from **Settings → Devices & Services → Intentsity → Configure**.

| Option | Default | Notes |
| --- | --- | --- |
| Listen for UDP audio | on | |
| UDP port | `6056` | Must match the device's `wake_audio_stream` port |
| Assistant ID for unlabeled datagrams | — | Only for legacy raw-PCM senders |
| Rolling buffer length | `60` s | Per assistant; bounds memory use |
| Audio kept before a detection | `2.0` s | Includes the wake word itself |
| Audio kept after a detection | `3.0` s | Capture waits this long before writing |
| Sample rate / width / channels | `16000` / `2` / `1` | Fallback only; `WWD2` and `audio_info` override |
| Subscribe to MQTT audio | on | Silently inactive with no broker configured |
| MQTT audio / event / format topics | `assist/debug/+/{pcm,events,audio_info}` | The `+` marks the assistant ID segment |
| Delete clips after | `0` days | `0` keeps clips forever; pruning runs twice a day |

## Reviewing in the panel

Both surfaces share one layout: a queue on the left, the item under review in the middle,
and — on Intent training — run details on the right. Every divider is draggable, and the
widths are remembered per browser. The panel measures itself rather than the window, so it
reflows as Home Assistant's own sidebar opens and closes: the side columns fold into
overlays you open from the toolbar when there is no room to dock them.

Conversations are grouped by conversation ID. An Assist dialogue that spans several pipeline
runs appears as one group of `run 1/N` rows rather than as unrelated chats. IDs are shown
shortened, but the full value is behind every one of them — hover to read it, click to copy.

| Key | Wake word | Intent training |
| --- | --- | --- |
| `J` / `K`, `↑` / `↓` | Previous / next clip | Previous / next run |
| `Space` | Play or pause | — |
| `1`–`5` | Apply a label | — |
| `⌘S` / `Ctrl+S` | — | Save the correction |

## Storage

Everything Intentsity owns lives under `config/intentsity/`, so a single directory covers
both surfaces and is included in Home Assistant backups:

```
config/intentsity/
├── intentsity.db          # chats, corrections, and clip metadata in one SQLite file
└── clips/
    ├── 20260724_141530_123456_kitchen.wav
    └── 20260724_141530_123456_kitchen.json   # sidecar metadata for the WAV
```

Clip rows carry a precomputed 96-point waveform envelope so the panel renders without
fetching audio. Deletes are tombstones — a deleted clip stays on disk and in the database
until retention pruning removes it, and the annotator has a queue for reviewing them.

If you previously ran the wake-word add-on, drop its `clips.db` at
`config/intentsity/clips.db` (or `config/intentsity/clips/clips.db`) alongside its WAV files.
Setup imports the rows once, mapping the add-on's label names onto the five-label taxonomy.
Re-running is harmless: existing filenames are skipped.

## Entities

| Entity | Meaning |
| --- | --- |
| `sensor.uncorrected_assist_chats` | Conversations recorded but not yet corrected |
| `sensor.unlabeled_wake_clips` | Captured clips with no label yet |

Both are measurement sensors, so they work as review-queue badges or automation triggers.

## HTTP API

Both views require Home Assistant authentication.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/intentsity/clips/{id}/audio` | One clip's WAV |
| `GET /api/intentsity/clips/archive` | Filtered clip set as a zip, grouped by label, with a `labels.jsonl` manifest |

The archive accepts `limit`, `label`, `assistant_id`, `start`, `end`, `include_deleted`, and
`labeled_only` as query parameters.

## WebSocket API

The panel talks to these; they are also usable from any authenticated websocket client.

| Command | Purpose |
| --- | --- |
| `intentsity/chats/list` | Page through recorded conversations |
| `intentsity/chats/subscribe` | Same, pushed on every new recording |
| `intentsity/chats/corrected/save` | Store a corrected conversation |
| `intentsity/chats/corrected/export` | JSONL of every correction |
| `intentsity/chats/tombstone` | Soft-delete chats or individual messages |
| `intentsity/clips/list` | Page through clips, filtered by label, assistant, or date |
| `intentsity/clips/subscribe` | Same, pushed on every new capture |
| `intentsity/clips/label` | Label one or more clips |
| `intentsity/clips/tombstone` | Soft-delete or restore clips |
| `intentsity/clips/capture_noise` | Save the trailing buffer as a background-noise clip |
| `intentsity/assistants` | Per-assistant capture status, transport health, webhook URL |

## Development

The Python package needs no build step; the panel does.

```bash
uv sync --locked --dev                   # Python 3.13; uv installs it if needed
uv run pytest --cov=custom_components.intentsity
uv run ruff check . && uv run ruff format --check .
```

```bash
cd frontend
npm install
npm run sync-ds      # re-vendor DesignSystem/ into src/ds/
npm run build        # emits custom_components/intentsity/panel.js
npm run dev          # same, watching
```

`DesignSystem/` is the source of truth for every component, token, and brand mark;
`frontend/src/ds/` is a build-time vendor copy so the bundle has no runtime dependency on that
tree. Edit the design system, then re-run `npm run sync-ds`. The PNGs in [brand/](brand/) are
rasterized from `DesignSystem/assets/` for the Home Assistant brands repository and are not
part of the shipped integration.

Contributor conventions, invariants, and the release checklist live in [AGENTS.md](AGENTS.md).

## License

MIT — see [LICENSE](LICENSE).
