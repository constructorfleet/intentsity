"""Domain constants, storage layout, and API command names."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "intentsity"

# Storage. Everything Intentsity owns lives under config/intentsity/ so a single
# directory covers both surfaces and is picked up by Home Assistant backups.
STORAGE_DIR: Final = "intentsity"
DB_NAME: Final = "intentsity.db"
CLIPS_DIR: Final = "clips"
DB_SCHEMA_VERSION: Final = 7

COORDINATOR_KEY: Final = "coordinator"
AUDIO_KEY: Final = "audio"

DATA_UNSUBSCRIBE: Final = "intentsity_unsubscribe"
DATA_CHAT_LOG_UNSUBSCRIBE: Final = "intentsity_chat_log_unsubscribe"
DATA_DB_INITIALIZED: Final = "db_initialized"
DATA_API_REGISTERED: Final = "api_registered"
DATA_WEBHOOK_ID: Final = "webhook_id"

# --- Intent trainer -------------------------------------------------------

DEFAULT_EVENT_LIMIT: Final = 100
MAX_EVENT_LIMIT: Final = 500
MIN_EVENT_LIMIT: Final = 1

SIGNAL_EVENT_RECORDED: Final = "intentsity_event_recorded"

WS_CMD_LIST_CHATS: Final = "intentsity/chats/list"
WS_CMD_SUBSCRIBE_CHATS: Final = "intentsity/chats/subscribe"
WS_CMD_SAVE_CORRECTED_CHAT: Final = "intentsity/chats/corrected/save"
WS_CMD_EXPORT_CORRECTED_CHATS: Final = "intentsity/chats/corrected/export"
WS_CMD_TOMBSTONE: Final = "intentsity/chats/tombstone"

# --- Wake word annotator --------------------------------------------------

SIGNAL_CLIP_RECORDED: Final = "intentsity_clip_recorded"

WS_CMD_LIST_CLIPS: Final = "intentsity/clips/list"
WS_CMD_SUBSCRIBE_CLIPS: Final = "intentsity/clips/subscribe"
WS_CMD_LABEL_CLIP: Final = "intentsity/clips/label"
WS_CMD_TOMBSTONE_CLIPS: Final = "intentsity/clips/tombstone"
WS_CMD_REPAIR_CLIP_RATE: Final = "intentsity/clips/repair_rate"
WS_CMD_CAPTURE_NOISE: Final = "intentsity/clips/capture_noise"
WS_CMD_ASSISTANTS: Final = "intentsity/assistants"

DEFAULT_CLIP_LIMIT: Final = 24
MAX_CLIP_LIMIT: Final = 200

# The five-label wake taxonomy from the design system. `unlabeled` is the
# absence of a decision, not a label a reviewer can pick.
LABEL_UNLABELED: Final = "unlabeled"
LABEL_TRUE_POSITIVE: Final = "tp"
LABEL_TRUE_NEGATIVE: Final = "tn"
LABEL_FALSE_POSITIVE: Final = "fp"
LABEL_FALSE_NEGATIVE: Final = "fn"
LABEL_BACKGROUND_NOISE: Final = "bgnoise"

WAKE_LABELS: Final = (
    LABEL_TRUE_POSITIVE,
    LABEL_TRUE_NEGATIVE,
    LABEL_FALSE_POSITIVE,
    LABEL_FALSE_NEGATIVE,
    LABEL_BACKGROUND_NOISE,
)
ALL_CLIP_LABELS: Final = (LABEL_UNLABELED, *WAKE_LABELS)

# Legacy add-on label names, mapped on import from an existing clips.db.
LEGACY_LABEL_MAP: Final = {
    "Unknown": LABEL_UNLABELED,
    "Positive": LABEL_TRUE_POSITIVE,
    "False Positive": LABEL_FALSE_POSITIVE,
    "False Negative": LABEL_FALSE_NEGATIVE,
    "Background Noise": LABEL_BACKGROUND_NOISE,
}

# --- Audio capture configuration ------------------------------------------

CONF_UDP_ENABLED: Final = "udp_enabled"
CONF_UDP_PORT: Final = "udp_port"
CONF_UDP_ASSISTANT_ID: Final = "udp_assistant_id"
CONF_BUFFER_DURATION: Final = "buffer_duration_seconds"
CONF_PRE_WAKE_DURATION: Final = "pre_wake_duration_seconds"
CONF_POST_WAKE_DURATION: Final = "post_wake_duration_seconds"
CONF_MQTT_ENABLED: Final = "mqtt_enabled"
CONF_MQTT_AUDIO_TOPIC: Final = "mqtt_audio_topic"
CONF_MQTT_EVENT_TOPIC: Final = "mqtt_event_topic"
CONF_MQTT_AUDIO_INFO_TOPIC: Final = "mqtt_audio_info_topic"
CONF_SAMPLE_RATE: Final = "sample_rate"
CONF_SAMPLE_WIDTH: Final = "sample_width"
CONF_CHANNELS: Final = "channels"
CONF_RETENTION_DAYS: Final = "retention_days"

DEFAULT_UDP_PORT: Final = 6056
DEFAULT_BUFFER_DURATION: Final = 60.0
DEFAULT_PRE_WAKE_DURATION: Final = 2.0
DEFAULT_POST_WAKE_DURATION: Final = 3.0
# Fallbacks for legacy WWD1/raw datagrams. WWD2 packets carry their own format,
# and microWakeWord processes int16 mono 16 kHz.
DEFAULT_SAMPLE_RATE: Final = 16000
DEFAULT_SAMPLE_WIDTH: Final = 2
DEFAULT_CHANNELS: Final = 1
DEFAULT_MQTT_AUDIO_TOPIC: Final = "assist/debug/+/pcm"
DEFAULT_MQTT_EVENT_TOPIC: Final = "assist/debug/+/events"
DEFAULT_MQTT_AUDIO_INFO_TOPIC: Final = "assist/debug/+/audio_info"
DEFAULT_RETENTION_DAYS: Final = 0  # 0 disables automatic clip pruning.

MAX_NOISE_CAPTURE_SECONDS: Final = 30.0

PANEL_URL_PATH: Final = "intentsity"
CLIP_AUDIO_URL: Final = "/api/intentsity/clips"
