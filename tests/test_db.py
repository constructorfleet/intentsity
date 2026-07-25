"""Unified SQLite schema: chats, corrections, and clips in one database."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

from homeassistant.core import HomeAssistant
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from custom_components.intentsity import db
from custom_components.intentsity.const import (
    CLIPS_DIR,
    DB_NAME,
    DOMAIN,
    LABEL_BACKGROUND_NOISE,
    LABEL_FALSE_POSITIVE,
    LABEL_TRUE_POSITIVE,
    LABEL_UNLABELED,
    STORAGE_DIR,
)
from custom_components.intentsity.models import (
    Chat,
    ChatMessage,
    Clip,
    ClipListRequest,
    CorrectedChatMessage,
    TombstoneTarget,
)

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def _chat(conversation_id: str, run_id: str, *, created_at: datetime = NOW) -> Chat:
    return Chat(
        conversation_id=conversation_id,
        pipeline_run_id=run_id,
        created_at=created_at,
        run_timestamp=created_at,
        messages=[
            ChatMessage(timestamp=created_at, sender="user", text="Turn on the light"),
            ChatMessage(timestamp=created_at, sender="assistant", text="Done"),
        ],
    )


# --- Paths ----------------------------------------------------------------


def test_storage_paths_live_under_config(hass: HomeAssistant) -> None:
    assert db.get_storage_dir(hass) == Path(hass.config.path(STORAGE_DIR))
    assert db.get_db_path(hass).name == DB_NAME
    assert db.get_clips_dir(hass).name == CLIPS_DIR


def test_init_db_creates_file(hass: HomeAssistant, clean_db: None) -> None:
    assert db.get_db_path(hass).is_file()
    # Re-initializing an existing database is a no-op.
    db.init_db(hass)


def test_dispose_client_is_tolerant(hass: HomeAssistant) -> None:
    hass.data.pop(DOMAIN, None)
    db.dispose_client(hass)  # no domain data at all
    hass.data[DOMAIN] = "not-a-dict"
    db.dispose_client(hass)
    hass.data.pop(DOMAIN, None)


# --- Chats ----------------------------------------------------------------


def test_upsert_and_fetch_chat(hass: HomeAssistant, clean_db: None) -> None:
    key = db.upsert_chat(hass, _chat("conv-1", "run-1"))
    assert key == ("conv-1", "run-1")

    chats = db.fetch_recent_chats(hass)
    assert len(chats) == 1
    assert [msg.text for msg in chats[0].messages] == ["Turn on the light", "Done"]
    assert [msg.position for msg in chats[0].messages] == [0, 1]


def test_upsert_chat_is_idempotent(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.upsert_chat(hass, _chat("conv-1", "run-1"))

    chats = db.fetch_recent_chats(hass)
    assert len(chats) == 1
    # Messages carry no ids, so a second write appends rather than replacing.
    assert len(chats[0].messages) == 4


def test_upsert_chat_message_assigns_next_position(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    message_id = db.upsert_chat_message(
        hass, "conv-1", "run-1", ChatMessage(sender="user", text="And the fan")
    )
    assert message_id > 0

    messages = db.fetch_recent_chats(hass)[0].messages
    assert messages[-1].text == "And the fan"
    assert messages[-1].position == 2


def test_replace_chat_messages(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.replace_chat_messages(
        hass,
        "conv-1",
        "run-1",
        [ChatMessage(sender="user", text="Only this", data={"k": "v"})],
    )

    messages = db.fetch_recent_chats(hass)[0].messages
    assert [msg.text for msg in messages] == ["Only this"]
    assert messages[0].data == {"k": "v"}


def test_fetch_chats_page_paginates_and_counts(hass: HomeAssistant, clean_db: None) -> None:
    for index in range(5):
        db.upsert_chat(
            hass, _chat(f"conv-{index}", "run-1", created_at=NOW + timedelta(minutes=index))
        )

    page, total = db.fetch_chats_page(hass, limit=2, offset=1)
    assert total == 5
    # Newest first, so offset 1 lands on the second-newest.
    assert [chat.conversation_id for chat in page] == ["conv-3", "conv-2"]

    assert len(db.fetch_chats(hass, limit=3)) == 3


def test_fetch_chats_filters_by_corrected_state(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-corrected", "run-1"))
    db.upsert_chat(hass, _chat("conv-plain", "run-1"))
    db.upsert_corrected_chat(
        hass,
        "conv-corrected",
        "run-1",
        [CorrectedChatMessage(sender="user", text="Fixed", position=0)],
    )

    corrected, corrected_total = db.fetch_chats_page(hass, limit=10, corrected=True)
    assert [chat.conversation_id for chat in corrected] == ["conv-corrected"]
    assert corrected_total == 1
    assert corrected[0].corrected is not None
    assert [msg.text for msg in corrected[0].corrected.messages] == ["Fixed"]

    uncorrected, uncorrected_total = db.fetch_chats_page(hass, limit=10, corrected=False)
    assert [chat.conversation_id for chat in uncorrected] == ["conv-plain"]
    assert uncorrected_total == 1

    assert db.count_uncorrected_chats(hass) == 1
    assert len(db.fetch_recent_chats(hass, corrected=True)) == 1
    assert len(db.fetch_recent_chats(hass, corrected=False)) == 1


def test_fetch_chats_filters_by_date_range(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-old", "run-1", created_at=NOW - timedelta(days=2)))
    db.upsert_chat(hass, _chat("conv-new", "run-1", created_at=NOW))

    page, total = db.fetch_chats_page(hass, limit=10, start=NOW - timedelta(hours=1))
    assert [chat.conversation_id for chat in page] == ["conv-new"]
    assert total == 1

    page, _ = db.fetch_chats_page(hass, limit=10, end=NOW - timedelta(days=1))
    assert [chat.conversation_id for chat in page] == ["conv-old"]

    recent = db.fetch_recent_chats(hass, limit=10, start=NOW - timedelta(hours=1), end=NOW)
    assert [chat.conversation_id for chat in recent] == ["conv-new"]


def test_fetch_latest_chat_by_conversation_id(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1", created_at=NOW))
    db.upsert_chat(hass, _chat("conv-1", "run-2", created_at=NOW + timedelta(minutes=1)))

    latest = db.fetch_latest_chat_by_conversation_id(hass, "conv-1")
    assert latest is not None
    assert latest.pipeline_run_id == "run-2"
    assert db.fetch_latest_chat_by_conversation_id(hass, "missing") is None


def test_upsert_corrected_chat_replaces_messages(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.upsert_corrected_chat(
        hass, "conv-1", "run-1", [CorrectedChatMessage(sender="user", text="First")]
    )
    db.upsert_corrected_chat(
        hass,
        "conv-1",
        "run-1",
        [
            CorrectedChatMessage(sender="user", text="Second"),
            CorrectedChatMessage(sender="assistant", text="Reply"),
        ],
    )

    corrected = db.fetch_recent_chats(hass)[0].corrected
    assert corrected is not None
    assert [msg.text for msg in corrected.messages] == ["Second", "Reply"]
    assert [msg.position for msg in corrected.messages] == [0, 1]


def test_upsert_corrected_chat_restores_tombstoned(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.upsert_corrected_chat(
        hass, "conv-1", "run-1", [CorrectedChatMessage(sender="user", text="First")]
    )
    db.tombstone_targets(
        hass,
        [TombstoneTarget(kind="corrected_chat", conversation_id="conv-1", pipeline_run_id="run-1")],
    )
    assert db.fetch_recent_chats(hass)[0].corrected is None

    db.upsert_corrected_chat(
        hass, "conv-1", "run-1", [CorrectedChatMessage(sender="user", text="Again")]
    )
    corrected = db.fetch_recent_chats(hass)[0].corrected
    assert corrected is not None
    assert [msg.text for msg in corrected.messages] == ["Again"]


def test_tombstone_chat_hides_everything_below_it(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.upsert_corrected_chat(
        hass, "conv-1", "run-1", [CorrectedChatMessage(sender="user", text="Fixed")]
    )
    db.tombstone_targets(
        hass,
        [TombstoneTarget(kind="chat", conversation_id="conv-1", pipeline_run_id="run-1")],
    )

    assert db.fetch_recent_chats(hass) == []
    assert db.count_uncorrected_chats(hass) == 0


def test_tombstone_individual_messages(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.upsert_corrected_chat(
        hass,
        "conv-1",
        "run-1",
        [
            CorrectedChatMessage(sender="user", text="Keep"),
            CorrectedChatMessage(sender="assistant", text="Drop"),
        ],
    )
    chat = db.fetch_recent_chats(hass)[0]
    assert chat.corrected is not None

    db.tombstone_targets(
        hass,
        [
            TombstoneTarget(kind="message", message_id=chat.messages[0].id),
            TombstoneTarget(
                kind="corrected_message", corrected_message_id=chat.corrected.messages[1].id
            ),
        ],
    )

    updated = db.fetch_recent_chats(hass)[0]
    assert [msg.text for msg in updated.messages] == ["Done"]
    assert updated.corrected is not None
    assert [msg.text for msg in updated.corrected.messages] == ["Keep"]


def test_tombstone_targets_empty_is_noop(hass: HomeAssistant, clean_db: None) -> None:
    db.tombstone_targets(hass, [])


def test_delete_chat_and_corrected_chat(hass: HomeAssistant, clean_db: None) -> None:
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db.upsert_corrected_chat(
        hass, "conv-1", "run-1", [CorrectedChatMessage(sender="user", text="Fixed")]
    )

    db.delete_corrected_chat(hass, "conv-1", "run-1")
    assert db.fetch_recent_chats(hass)[0].corrected is None

    db.delete_chat(hass, "conv-1", "run-1")
    assert db.fetch_recent_chats(hass) == []

    # Deleting what is already gone is a no-op.
    db.delete_chat(hass, "conv-1", "run-1")
    db.delete_corrected_chat(hass, "conv-1", "run-1")


# --- Clips ----------------------------------------------------------------


def test_insert_clip_dedupes_by_filename(hass: HomeAssistant, clean_db: None) -> None:
    clip = Clip(filename="clip.wav", timestamp=NOW, assistant_id="kitchen")
    first = db.insert_clip(hass, clip)
    assert db.insert_clip(hass, clip) == first


def test_fetch_clip_round_trips_json_columns(hass: HomeAssistant, clean_db: None) -> None:
    clip_id = db.insert_clip(
        hass,
        Clip(
            filename="clip.wav",
            timestamp=NOW,
            assistant_id="kitchen",
            wake_word="okay_nabu",
            confidence=0.91,
            duration=2.5,
            sample_rate=16000,
            sample_width=2,
            channels=1,
            peaks=[0.1, 0.9],
            data={"pre_duration": 2.0},
        ),
    )

    clip = db.fetch_clip(hass, clip_id)
    assert clip is not None
    assert clip.peaks == [0.1, 0.9]
    assert clip.data == {"pre_duration": 2.0}
    assert clip.timestamp == NOW
    assert db.fetch_clip(hass, clip_id + 999) is None


def test_fetch_clips_page_counts_every_queue(hass: HomeAssistant, add_clip) -> None:
    hass_instance = hass
    add_clip(label=LABEL_UNLABELED)
    add_clip(label=LABEL_UNLABELED)
    add_clip(label=LABEL_TRUE_POSITIVE)
    add_clip(label=LABEL_FALSE_POSITIVE)
    deleted_id = add_clip(label=LABEL_BACKGROUND_NOISE)
    db.tombstone_clips(hass_instance, [deleted_id])

    response = db.fetch_clips_page(hass_instance, ClipListRequest(limit=50))
    assert response.total == 4  # tombstoned clips are excluded by default
    assert response.unlabeled_total == 2
    assert response.labeled_total == 2
    assert response.deleted_total == 1
    assert response.label_counts[LABEL_TRUE_POSITIVE] == 1
    assert response.label_counts[LABEL_BACKGROUND_NOISE] == 0


def test_fetch_clips_page_labeled_only_queue(hass: HomeAssistant, add_clip) -> None:
    add_clip(label=LABEL_UNLABELED)
    add_clip(label=LABEL_TRUE_POSITIVE)
    add_clip(label=LABEL_FALSE_POSITIVE)

    response = db.fetch_clips_page(hass, ClipListRequest(limit=50, labeled_only=True))
    assert response.total == 2
    assert {clip.label for clip in response.clips} == {
        LABEL_TRUE_POSITIVE,
        LABEL_FALSE_POSITIVE,
    }
    # The tab counts stay scoped to the whole assistant, not the active queue.
    assert response.unlabeled_total == 1


def test_fetch_clips_page_deleted_only_queue(hass: HomeAssistant, add_clip) -> None:
    kept = add_clip(label=LABEL_TRUE_POSITIVE)
    removed = add_clip(label=LABEL_UNLABELED)
    db.tombstone_clips(hass, [removed])

    response = db.fetch_clips_page(hass, ClipListRequest(limit=50, deleted_only=True))
    assert [clip.id for clip in response.clips] == [removed]
    assert response.total == 1
    assert response.deleted_total == 1

    restored = db.tombstone_clips(hass, [removed], restore=True)
    assert restored == 1
    assert db.fetch_clips_page(hass, ClipListRequest(limit=50)).total == 2
    assert db.fetch_clip(hass, kept).deleted_at is None


def test_fetch_clips_page_include_deleted(hass: HomeAssistant, add_clip) -> None:
    add_clip()
    removed = add_clip()
    db.tombstone_clips(hass, [removed])

    response = db.fetch_clips_page(hass, ClipListRequest(limit=50, include_deleted=True))
    assert response.total == 2


def test_fetch_clips_page_unlabeled_covers_legacy_rows(hass: HomeAssistant, add_clip) -> None:
    add_clip(label=LABEL_UNLABELED)
    add_clip(label=LABEL_TRUE_POSITIVE)
    # The add-on wrote an empty label rather than a sentinel value.
    legacy_id = add_clip(filename="legacy.wav")
    with db.get_db_path(hass).open("rb"):
        pass
    db.dispose_client(hass)
    connection = sqlite3.connect(db.get_db_path(hass))
    connection.execute("UPDATE clips SET label = '' WHERE id = ?", (legacy_id,))
    connection.commit()
    connection.close()

    response = db.fetch_clips_page(hass, ClipListRequest(limit=50, label=LABEL_UNLABELED))
    assert {clip.id for clip in response.clips} == {legacy_id} | {
        clip.id for clip in response.clips if clip.label == LABEL_UNLABELED
    }
    assert response.total == 2
    assert response.unlabeled_total == 2
    # An empty label reads back as the sentinel.
    assert db.fetch_clip(hass, legacy_id).label == LABEL_UNLABELED


def test_fetch_clips_page_filters_and_orders(hass: HomeAssistant, add_clip) -> None:
    add_clip(assistant_id="kitchen", timestamp=NOW)
    newest = add_clip(assistant_id="kitchen", timestamp=NOW + timedelta(minutes=5))
    add_clip(assistant_id="office", timestamp=NOW + timedelta(minutes=10))

    response = db.fetch_clips_page(hass, ClipListRequest(limit=50, assistant_id="kitchen"))
    assert response.total == 2
    assert response.clips[0].id == newest  # newest first

    windowed = db.fetch_clips_page(
        hass,
        ClipListRequest(limit=50, start=NOW + timedelta(minutes=1), end=NOW + timedelta(minutes=6)),
    )
    assert [clip.id for clip in windowed.clips] == [newest]

    paged = db.fetch_clips_page(hass, ClipListRequest(limit=1, offset=1))
    assert len(paged.clips) == 1
    assert paged.total == 3


def test_fetch_clips_for_export_ignores_pagination(hass: HomeAssistant, add_clip) -> None:
    for _ in range(5):
        add_clip(label=LABEL_TRUE_POSITIVE)
    add_clip(label=LABEL_UNLABELED)

    clips = db.fetch_clips_for_export(hass, ClipListRequest(limit=1, labeled_only=True))
    assert len(clips) == 5


def test_label_clips_updates_rows(hass: HomeAssistant, add_clip) -> None:
    first = add_clip()
    second = add_clip()

    assert db.label_clips(hass, [first, second], LABEL_TRUE_POSITIVE) == 2
    assert db.fetch_clip(hass, first).label == LABEL_TRUE_POSITIVE
    assert db.label_clips(hass, [999], LABEL_TRUE_POSITIVE) == 0
    assert db.count_unlabeled_clips(hass) == 0


def test_count_unlabeled_clips_excludes_tombstoned(hass: HomeAssistant, add_clip) -> None:
    add_clip()
    removed = add_clip()
    db.tombstone_clips(hass, [removed])
    assert db.count_unlabeled_clips(hass) == 1


def test_count_clips_by_assistant(hass: HomeAssistant, add_clip) -> None:
    add_clip(assistant_id="kitchen")
    add_clip(assistant_id="kitchen")
    add_clip(assistant_id="office")
    add_clip(assistant_id=None)
    removed = add_clip(assistant_id="office")
    db.tombstone_clips(hass, [removed])

    assert db.count_clips_by_assistant(hass) == {"kitchen": 2, "office": 1}


def test_prune_clips_removes_rows_and_files(hass: HomeAssistant, add_clip) -> None:
    clips_dir = db.get_clips_dir(hass)
    clips_dir.mkdir(parents=True, exist_ok=True)
    old = add_clip(filename="old.wav", timestamp=NOW - timedelta(days=30))
    add_clip(filename="new.wav", timestamp=datetime.now(UTC))
    (clips_dir / "old.wav").write_bytes(b"RIFF")
    (clips_dir / "old.json").write_text("{}")

    assert db.prune_clips(hass, retention_days=0) == 0  # pruning disabled
    assert db.prune_clips(hass, retention_days=7) == 1
    assert db.fetch_clip(hass, old) is None
    assert not (clips_dir / "old.wav").exists()
    assert not (clips_dir / "old.json").exists()
    assert db.fetch_clips_page(hass, ClipListRequest(limit=10)).total == 1


# --- Legacy import --------------------------------------------------------


def _write_legacy_db(path: Path, rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE clips (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            timestamp TEXT,
            label TEXT,
            assistant_id TEXT,
            duration REAL,
            sample_rate INTEGER,
            deleted INTEGER
        )
        """
    )
    connection.executemany(
        "INSERT INTO clips (filename, timestamp, label, assistant_id, duration,"
        " sample_rate, deleted) VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    connection.commit()
    connection.close()


def test_import_legacy_clips_maps_labels(hass: HomeAssistant, clean_db: None) -> None:
    legacy = db.get_storage_dir(hass) / "clips.db"
    _write_legacy_db(
        legacy,
        [
            ("a.wav", "2026-01-01T00:00:00", "Positive", "kitchen", 2.0, 16000, 0),
            ("b.wav", "2026-01-01T00:01:00", "False Positive", "kitchen", 2.0, 16000, 1),
            ("c.wav", "2026-01-01T00:02:00", "Unknown", "kitchen", 2.0, 16000, 0),
            ("d.wav", "2026-01-01T00:03:00", "Nonsense", "kitchen", 2.0, 16000, 0),
            ("", "2026-01-01T00:04:00", "Positive", "kitchen", 2.0, 16000, 0),
        ],
    )

    assert db.import_legacy_clips(hass, legacy) == 4
    # Re-importing skips filenames that already exist.
    assert db.import_legacy_clips(hass, legacy) == 0

    response = db.fetch_clips_page(hass, ClipListRequest(limit=50, include_deleted=True))
    by_name = {clip.filename: clip for clip in response.clips}
    assert by_name["a.wav"].label == LABEL_TRUE_POSITIVE
    assert by_name["b.wav"].label == LABEL_FALSE_POSITIVE
    assert by_name["b.wav"].deleted_at is not None
    assert by_name["c.wav"].label == LABEL_UNLABELED
    assert by_name["d.wav"].label == LABEL_UNLABELED


def test_import_legacy_clips_missing_and_malformed(
    hass: HomeAssistant, clean_db: None, tmp_path: Path
) -> None:
    assert db.import_legacy_clips(hass, tmp_path / "nope.db") == 0

    junk = tmp_path / "junk.db"
    junk.write_bytes(b"not a database at all")
    assert db.import_legacy_clips(hass, junk) == 0


def test_import_legacy_clips_tolerates_sparse_columns(
    hass: HomeAssistant, clean_db: None, tmp_path: Path
) -> None:
    legacy = tmp_path / "sparse.db"
    connection = sqlite3.connect(legacy)
    connection.execute("CREATE TABLE clips (id INTEGER PRIMARY KEY, filename TEXT)")
    connection.execute("INSERT INTO clips (filename) VALUES ('minimal.wav')")
    connection.commit()
    connection.close()

    assert db.import_legacy_clips(hass, legacy) == 1
    clip = db.fetch_clips_page(hass, ClipListRequest(limit=10)).clips[0]
    assert clip.filename == "minimal.wav"
    assert clip.label == LABEL_UNLABELED
    assert clip.assistant_id is None


# --- Schema migration -----------------------------------------------------


def test_ensure_schema_migrates_id_based_chats(hass: HomeAssistant) -> None:
    """A pre-2025 database keyed chats by autoincrement id."""
    db.dispose_client(hass)
    db_path = db.get_db_path(hass)
    db_path.unlink(missing_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            created_at DATETIME
        );
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            timestamp DATETIME,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            data TEXT
        );
        CREATE TABLE corrected_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_chat_id INTEGER,
            created_at DATETIME,
            updated_at DATETIME
        );
        CREATE TABLE corrected_chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corrected_chat_id INTEGER,
            original_message_id INTEGER,
            position INTEGER,
            timestamp DATETIME,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            data TEXT
        );
        INSERT INTO chats (id, conversation_id, created_at)
            VALUES (1, 'conv-legacy', '2026-01-01T00:00:00');
        INSERT INTO chat_messages (chat_id, timestamp, sender, text, data)
            VALUES (1, '2026-01-01T00:00:00', 'user', 'Legacy question', NULL);
        INSERT INTO corrected_chats (id, original_chat_id, created_at, updated_at)
            VALUES (1, 1, '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        INSERT INTO corrected_chat_messages
            (corrected_chat_id, original_message_id, position, timestamp, sender, text, data)
            VALUES (1, 1, 0, '2026-01-01T00:00:00', 'user', 'Legacy fix', NULL);
        """
    )
    connection.commit()
    connection.close()

    db.init_db(hass)
    try:
        chats = db.fetch_recent_chats(hass)
        assert [chat.conversation_id for chat in chats] == ["conv-legacy"]
        assert chats[0].pipeline_run_id == "legacy"
        assert [msg.text for msg in chats[0].messages] == ["Legacy question"]
        assert chats[0].corrected is not None
        assert [msg.text for msg in chats[0].corrected.messages] == ["Legacy fix"]
    finally:
        db.dispose_client(hass)


def test_ensure_schema_migrates_conversation_keyed_chats(hass: HomeAssistant) -> None:
    """The intermediate schema keyed chats by conversation_id with no run id."""
    db.dispose_client(hass)
    db_path = db.get_db_path(hass)
    db_path.unlink(missing_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE chats (
            conversation_id TEXT PRIMARY KEY,
            created_at DATETIME
        );
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            timestamp DATETIME,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            data TEXT
        );
        CREATE TABLE corrected_chats (
            conversation_id TEXT PRIMARY KEY,
            original_conversation_id TEXT,
            created_at DATETIME,
            updated_at DATETIME
        );
        CREATE TABLE corrected_chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corrected_chat_id TEXT,
            original_message_id INTEGER,
            position INTEGER,
            timestamp DATETIME,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            data TEXT
        );
        INSERT INTO chats (conversation_id, created_at)
            VALUES ('conv-mid', '2026-01-01T00:00:00');
        INSERT INTO chat_messages (chat_id, timestamp, sender, text, data)
            VALUES ('conv-mid', '2026-01-01T00:00:00', 'user', 'Mid question', NULL);
        INSERT INTO corrected_chats
            (conversation_id, original_conversation_id, created_at, updated_at)
            VALUES ('conv-mid', 'conv-mid', '2026-01-01T00:00:00', '2026-01-01T00:00:00');
        INSERT INTO corrected_chat_messages
            (corrected_chat_id, original_message_id, position, timestamp, sender, text, data)
            VALUES ('conv-mid', 1, 0, '2026-01-01T00:00:00', 'assistant', 'Mid fix', NULL);
        """
    )
    connection.commit()
    connection.close()

    db.init_db(hass)
    try:
        chats = db.fetch_recent_chats(hass)
        assert [chat.conversation_id for chat in chats] == ["conv-mid"]
        assert [msg.text for msg in chats[0].messages] == ["Mid question"]
        assert chats[0].corrected is not None
        assert [msg.text for msg in chats[0].corrected.messages] == ["Mid fix"]
    finally:
        db.dispose_client(hass)


def test_ensure_schema_adds_position_and_deleted_at(hass: HomeAssistant) -> None:
    """A current-shape database missing only the newer columns is patched in place."""
    db.dispose_client(hass)
    db_path = db.get_db_path(hass)
    db_path.unlink(missing_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE chats (
            conversation_id TEXT NOT NULL,
            pipeline_run_id TEXT NOT NULL,
            run_timestamp DATETIME,
            created_at DATETIME,
            PRIMARY KEY (conversation_id, pipeline_run_id)
        );
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            pipeline_run_id TEXT NOT NULL,
            timestamp DATETIME,
            sender TEXT NOT NULL,
            text TEXT NOT NULL,
            data TEXT
        );
        INSERT INTO chats VALUES ('conv-1', 'run-1', NULL, '2026-01-01T00:00:00');
        INSERT INTO chat_messages (chat_id, pipeline_run_id, timestamp, sender, text, data)
            VALUES ('conv-1', 'run-1', '2026-01-01T00:00:00', 'user', 'Hi', NULL);
        """
    )
    connection.commit()
    connection.close()

    db.init_db(hass)
    try:
        chats = db.fetch_recent_chats(hass)
        assert [msg.text for msg in chats[0].messages] == ["Hi"]
        # A NULL run_timestamp falls back rather than crashing the row mapper.
        assert chats[0].run_timestamp is not None
    finally:
        db.dispose_client(hass)


def test_ensure_schema_migrates_chats_without_a_messages_table(hass: HomeAssistant) -> None:
    """An older database can have `chats` but no `chat_messages` yet."""
    db.dispose_client(hass)
    db_path = db.get_db_path(hass)
    db_path.unlink(missing_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE chats (
            conversation_id TEXT PRIMARY KEY,
            created_at DATETIME
        );
        INSERT INTO chats (conversation_id, created_at)
            VALUES ('conv-bare', '2026-01-01T00:00:00');
        """
    )
    connection.commit()
    connection.close()

    db.init_db(hass)
    try:
        chats = db.fetch_recent_chats(hass)
        assert [(chat.conversation_id, chat.pipeline_run_id) for chat in chats] == [
            ("conv-bare", "legacy")
        ]
        assert chats[0].messages == []
    finally:
        db.dispose_client(hass)


def test_ensure_schema_is_idempotent(hass: HomeAssistant, clean_db: None) -> None:
    """Re-running the migration over a current schema changes nothing."""
    db.upsert_chat(hass, _chat("conv-1", "run-1"))
    db._get_client(hass).ensure_initialized()

    chats = db.fetch_recent_chats(hass)
    assert [msg.text for msg in chats[0].messages] == ["Turn on the light", "Done"]


def test_upsert_chat_recovers_from_an_integrity_error(
    hass: HomeAssistant, clean_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A concurrent writer can insert the same chat between merge and commit."""
    db.upsert_chat(hass, _chat("conv-1", "run-1"))

    real_merge = Session.merge
    calls = {"n": 0}

    def _merge(self, instance, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("insert", (), Exception("UNIQUE constraint failed"))
        return real_merge(self, instance, **kwargs)

    monkeypatch.setattr(Session, "merge", _merge)
    assert db.upsert_chat(hass, _chat("conv-1", "run-1")) == ("conv-1", "run-1")

    # The retry re-merged the chat and both of its messages.
    chats = db.fetch_recent_chats(hass)
    assert len(chats) == 1
    assert [msg.text for msg in chats[0].messages] == [
        "Turn on the light",
        "Done",
        "Turn on the light",
        "Done",
    ]


def test_upsert_chat_reraises_when_the_chat_really_is_missing(
    hass: HomeAssistant, clean_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the row is genuinely absent, the integrity error was not a race."""

    def _merge(self, instance, **kwargs):
        raise IntegrityError("insert", (), Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(Session, "merge", _merge)
    with pytest.raises(IntegrityError):
        db.upsert_chat(hass, _chat("conv-missing", "run-1"))


def test_known_clip_filenames(hass: HomeAssistant, add_clip) -> None:
    add_clip(filename="one.wav")
    add_clip(filename="two.wav")
    client = db._get_client(hass)
    assert client.known_clip_filenames() == {"one.wav", "two.wav"}


def test_get_client_is_cached(hass: HomeAssistant, clean_db: None) -> None:
    assert db._get_client(hass) is db._get_client(hass)


@pytest.mark.parametrize("restore", [True, False])
def test_tombstone_clips_with_no_matches(
    hass: HomeAssistant, clean_db: None, restore: bool
) -> None:
    assert db.tombstone_clips(hass, [12345], restore=restore) == 0
