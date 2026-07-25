from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

from homeassistant.core import HomeAssistant
import orjson
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    and_,
    create_engine,
    event,
    func,
    or_,
    select,
    text,
    tuple_,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)

from .const import (
    CLIPS_DIR,
    DB_NAME,
    DOMAIN,
    LABEL_UNLABELED,
    STORAGE_DIR,
    WAKE_LABELS,
)
from .models import (
    Chat,
    ChatMessage,
    Clip,
    ClipListRequest,
    ClipListResponse,
    CorrectedChat,
    CorrectedChatMessage,
    TombstoneTarget,
)
from .utils import parse_timestamp

_CLIENT_KEY: Final = "db_client"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_dumps(value: object) -> str:
    return orjson.dumps(value).decode()


class _DBBase(DeclarativeBase):
    pass


# New chat-centric schema
class ChatRow(_DBBase):
    __tablename__ = "chats"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "pipeline_run_id",
            name="uniq_chats_conversation_pipeline",
        ),
    )

    conversation_id: Mapped[str] = mapped_column(String, primary_key=True)
    pipeline_run_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages: Mapped[list[ChatMessageRow]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ChatMessageRow.timestamp, ChatMessageRow.id",
    )
    corrected: Mapped[CorrectedChatRow | None] = relationship(
        back_populates="original_chat",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )


class ChatMessageRow(_DBBase):
    __tablename__ = "chat_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["chat_id", "pipeline_run_id"],
            ["chats.conversation_id", "chats.pipeline_run_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String)
    pipeline_run_id: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    sender: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chat: Mapped[ChatRow] = relationship(back_populates="messages")


class CorrectedChatRow(_DBBase):
    __tablename__ = "corrected_chats"
    __table_args__ = (
        UniqueConstraint(
            "original_conversation_id",
            "original_pipeline_run_id",
            name="uniq_corrected_original_conversation",
        ),
        ForeignKeyConstraint(
            ["original_conversation_id", "original_pipeline_run_id"],
            ["chats.conversation_id", "chats.pipeline_run_id"],
            ondelete="CASCADE",
        ),
    )

    conversation_id: Mapped[str] = mapped_column(String, primary_key=True)
    pipeline_run_id: Mapped[str] = mapped_column(String, primary_key=True)
    original_conversation_id: Mapped[str] = mapped_column(String, index=True)
    original_pipeline_run_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages: Mapped[list[CorrectedChatMessageRow]] = relationship(
        back_populates="corrected_chat",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CorrectedChatMessageRow.position",
    )
    original_chat: Mapped[ChatRow] = relationship(back_populates="corrected")


class CorrectedChatMessageRow(_DBBase):
    __tablename__ = "corrected_chat_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["corrected_chat_id", "corrected_pipeline_run_id"],
            ["corrected_chats.conversation_id", "corrected_chats.pipeline_run_id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    corrected_chat_id: Mapped[str] = mapped_column(String)
    corrected_pipeline_run_id: Mapped[str] = mapped_column(String)
    original_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    sender: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    corrected_chat: Mapped[CorrectedChatRow] = relationship(back_populates="messages")


class ClipRow(_DBBase):
    """One captured wake-word audio clip and its review label."""

    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    label: Mapped[str] = mapped_column(String, nullable=False, default=LABEL_UNLABELED, index=True)
    assistant_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    wake_word: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Precomputed waveform envelope so the panel renders without fetching audio.
    peaks: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


def get_storage_dir(hass: HomeAssistant) -> Path:
    """Directory holding the database and clips, included in HA backups."""
    return Path(hass.config.path(STORAGE_DIR))


def get_db_path(hass: HomeAssistant) -> Path:
    return get_storage_dir(hass) / DB_NAME


def get_clips_dir(hass: HomeAssistant) -> Path:
    return get_storage_dir(hass) / CLIPS_DIR


class IntentsityDBClient:
    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._engine: Engine | None = None

    def ensure_initialized(self) -> None:
        engine = self._get_engine()
        _DBBase.metadata.create_all(engine)
        self._ensure_schema(engine)

    def _ensure_schema(self, engine: Engine) -> None:
        def _columns(table_name: str) -> set[str]:
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            return {row[1] for row in result.fetchall()}

        def _table_exists(table_name: str) -> bool:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
                {"name": table_name},
            )
            return result.fetchone() is not None

        with engine.begin() as conn:
            # `create_all` has already run, so every table exists; only a legacy
            # table's column set is unknown.
            chat_messages_columns = _columns("chat_messages")
            if "position" not in chat_messages_columns:
                conn.execute(
                    text("ALTER TABLE chat_messages ADD COLUMN position INTEGER NOT NULL DEFAULT 0")
                )

            chats_exists = _table_exists("chats")
            chats_columns = _columns("chats") if chats_exists else set()
            needs_chat_migration = chats_exists and (
                "id" in chats_columns
                or "pipeline_run_id" not in chats_columns
                or "pipeline_run_id" not in chat_messages_columns
                or "run_timestamp" not in chats_columns
            )
            if needs_chat_migration:
                conn.execute(text("PRAGMA foreign_keys=OFF"))

                conn.execute(
                    text(
                        """
                        CREATE TABLE chats_new (
                            conversation_id TEXT NOT NULL,
                            pipeline_run_id TEXT NOT NULL,
                            run_timestamp DATETIME,
                            created_at DATETIME,
                            PRIMARY KEY (conversation_id, pipeline_run_id)
                        )
                        """
                    )
                )
                # `needs_chat_migration` implies `chats_exists`, so there is always a
                # table to copy from; only its shape is in question.
                if "id" in chats_columns:
                    conn.execute(
                        text(
                            """
                            INSERT INTO chats_new (
                                conversation_id,
                                pipeline_run_id,
                                run_timestamp,
                                created_at
                            )
                            SELECT
                                COALESCE(conversation_id, 'legacy-' || id),
                                'legacy',
                                created_at,
                                created_at
                            FROM chats
                            """
                        )
                    )
                    chat_join = "chats.id = chat_messages.chat_id"
                    chat_id_expr = "COALESCE(chats.conversation_id, 'legacy-' || chats.id)"
                    corrected_chat_join = "chats.id = corrected_chats.original_chat_id"
                    corrected_chat_id_expr = (
                        "COALESCE(chats.conversation_id, 'legacy-' || chats.id)"
                    )
                    corrected_message_join = (
                        "corrected_chats.id = corrected_chat_messages.corrected_chat_id"
                    )
                else:
                    conn.execute(
                        text(
                            """
                            INSERT INTO chats_new (
                                conversation_id,
                                pipeline_run_id,
                                run_timestamp,
                                created_at
                            )
                            SELECT conversation_id, 'legacy', created_at, created_at
                            FROM chats
                            """
                        )
                    )
                    chat_join = "chats.conversation_id = chat_messages.chat_id"
                    chat_id_expr = "chat_messages.chat_id"
                    corrected_chat_join = (
                        "corrected_chats.original_conversation_id = chats.conversation_id"
                    )
                    corrected_chat_id_expr = "corrected_chats.conversation_id"
                    corrected_message_join = (
                        "corrected_chats.conversation_id "
                        "= corrected_chat_messages.corrected_chat_id"
                    )

                conn.execute(
                    text(
                        """
                        CREATE TABLE chat_messages_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            chat_id TEXT NOT NULL,
                            pipeline_run_id TEXT NOT NULL,
                            position INTEGER NOT NULL DEFAULT 0,
                            timestamp DATETIME,
                            sender TEXT NOT NULL,
                            text TEXT NOT NULL,
                            data TEXT,
                            FOREIGN KEY(chat_id, pipeline_run_id)
                                REFERENCES chats_new(conversation_id, pipeline_run_id)
                                ON DELETE CASCADE
                        )
                        """
                    )
                )
                if _table_exists("chat_messages") and chats_exists:
                    conn.execute(
                        text(
                            f"""
                            INSERT INTO chat_messages_new (
                                id,
                                chat_id,
                                pipeline_run_id,
                                position,
                                timestamp,
                                sender,
                                text,
                                data
                            )
                            SELECT
                                chat_messages.id,
                                {chat_id_expr},
                                'legacy',
                                chat_messages.position,
                                chat_messages.timestamp,
                                chat_messages.sender,
                                chat_messages.text,
                                chat_messages.data
                            FROM chat_messages
                            JOIN chats ON {chat_join}
                            """
                        )
                    )

                conn.execute(
                    text(
                        """
                        CREATE TABLE corrected_chats_new (
                            conversation_id TEXT NOT NULL,
                            pipeline_run_id TEXT NOT NULL,
                            original_conversation_id TEXT NOT NULL,
                            original_pipeline_run_id TEXT NOT NULL,
                            created_at DATETIME,
                            updated_at DATETIME,
                            UNIQUE(original_conversation_id, original_pipeline_run_id),
                            PRIMARY KEY (conversation_id, pipeline_run_id),
                            FOREIGN KEY(original_conversation_id, original_pipeline_run_id)
                                REFERENCES chats_new(conversation_id, pipeline_run_id)
                                ON DELETE CASCADE
                        )
                        """
                    )
                )
                if _table_exists("corrected_chats"):
                    if "id" in chats_columns:
                        conn.execute(
                            text(
                                f"""
                                INSERT INTO corrected_chats_new (
                                    conversation_id,
                                    pipeline_run_id,
                                    original_conversation_id,
                                    original_pipeline_run_id,
                                    created_at,
                                    updated_at
                                )
                                SELECT
                                    {corrected_chat_id_expr},
                                    'legacy',
                                    {corrected_chat_id_expr},
                                    'legacy',
                                    corrected_chats.created_at,
                                    corrected_chats.updated_at
                                FROM corrected_chats
                                JOIN chats ON {corrected_chat_join}
                                """
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                """
                                INSERT INTO corrected_chats_new (
                                    conversation_id,
                                    pipeline_run_id,
                                    original_conversation_id,
                                    original_pipeline_run_id,
                                    created_at,
                                    updated_at
                                )
                                SELECT
                                    corrected_chats.conversation_id,
                                    'legacy',
                                    corrected_chats.original_conversation_id,
                                    'legacy',
                                    corrected_chats.created_at,
                                    corrected_chats.updated_at
                                FROM corrected_chats
                                """
                            )
                        )

                conn.execute(
                    text(
                        """
                        CREATE TABLE corrected_chat_messages_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            corrected_chat_id TEXT NOT NULL,
                            corrected_pipeline_run_id TEXT NOT NULL,
                            original_message_id INTEGER,
                            position INTEGER NOT NULL DEFAULT 0,
                            timestamp DATETIME,
                            sender TEXT NOT NULL,
                            text TEXT NOT NULL,
                            data TEXT,
                            FOREIGN KEY(corrected_chat_id, corrected_pipeline_run_id)
                                REFERENCES corrected_chats_new(conversation_id, pipeline_run_id)
                                ON DELETE CASCADE,
                            FOREIGN KEY(original_message_id)
                                REFERENCES chat_messages_new(id)
                                ON DELETE SET NULL
                        )
                        """
                    )
                )
                if _table_exists("corrected_chat_messages"):
                    if "id" in chats_columns:
                        conn.execute(
                            text(
                                f"""
                                INSERT INTO corrected_chat_messages_new (
                                    id,
                                    corrected_chat_id,
                                    corrected_pipeline_run_id,
                                    original_message_id,
                                    position,
                                    timestamp,
                                    sender,
                                    text,
                                    data
                                )
                                SELECT
                                    corrected_chat_messages.id,
                                    {corrected_chat_id_expr},
                                    'legacy',
                                    corrected_chat_messages.original_message_id,
                                    corrected_chat_messages.position,
                                    corrected_chat_messages.timestamp,
                                    corrected_chat_messages.sender,
                                    corrected_chat_messages.text,
                                    corrected_chat_messages.data
                                FROM corrected_chat_messages
                                JOIN corrected_chats
                                    ON {corrected_message_join}
                                JOIN chats
                                    ON {corrected_chat_join}
                                """
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                f"""
                                INSERT INTO corrected_chat_messages_new (
                                    id,
                                    corrected_chat_id,
                                    corrected_pipeline_run_id,
                                    original_message_id,
                                    position,
                                    timestamp,
                                    sender,
                                    text,
                                    data
                                )
                                SELECT
                                    corrected_chat_messages.id,
                                    corrected_chats.conversation_id,
                                    'legacy',
                                    corrected_chat_messages.original_message_id,
                                    corrected_chat_messages.position,
                                    corrected_chat_messages.timestamp,
                                    corrected_chat_messages.sender,
                                    corrected_chat_messages.text,
                                    corrected_chat_messages.data
                                FROM corrected_chat_messages
                                JOIN corrected_chats
                                    ON {corrected_message_join}
                                """
                            )
                        )

                conn.execute(text("DROP TABLE IF EXISTS corrected_chat_messages"))
                conn.execute(text("DROP TABLE IF EXISTS corrected_chats"))
                conn.execute(text("DROP TABLE IF EXISTS chat_messages"))
                conn.execute(text("DROP TABLE IF EXISTS chats"))

                conn.execute(text("ALTER TABLE chats_new RENAME TO chats"))
                conn.execute(text("ALTER TABLE chat_messages_new RENAME TO chat_messages"))
                conn.execute(text("ALTER TABLE corrected_chats_new RENAME TO corrected_chats"))
                conn.execute(
                    text(
                        "ALTER TABLE corrected_chat_messages_new RENAME TO corrected_chat_messages"
                    )
                )

                conn.execute(text("PRAGMA foreign_keys=ON"))

            for table_name in (
                "chats",
                "chat_messages",
                "corrected_chats",
                "corrected_chat_messages",
            ):
                columns = _columns(table_name)
                if "deleted_at" not in columns:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN deleted_at DATETIME"))

    # New chat persistence methods
    def upsert_chat(self, chat: Chat) -> tuple[str, str]:
        engine = self._get_engine()
        with Session(engine) as session:
            chat_row = ChatRow(
                created_at=chat.created_at,
                conversation_id=chat.conversation_id,
                pipeline_run_id=chat.pipeline_run_id,
                run_timestamp=chat.run_timestamp,
            )
            try:
                session.merge(chat_row)
                session.flush()
                for index, msg in enumerate(chat.messages):
                    msg_row = ChatMessageRow(
                        id=msg.id,
                        chat_id=chat.conversation_id,
                        pipeline_run_id=chat.pipeline_run_id,
                        position=msg.position if msg.position is not None else index,
                        timestamp=msg.timestamp,
                        sender=msg.sender,
                        text=msg.text,
                        data=_json_dumps(msg.data) if msg.data else None,
                    )
                    session.merge(msg_row)
                session.commit()
            except IntegrityError:
                session.rollback()
                existing = session.get(
                    ChatRow,
                    {
                        "conversation_id": chat.conversation_id,
                        "pipeline_run_id": chat.pipeline_run_id,
                    },
                )
                if existing is None:
                    raise
                existing.created_at = chat.created_at
                existing.run_timestamp = chat.run_timestamp
                session.flush()
                for index, msg in enumerate(chat.messages):
                    msg_row = ChatMessageRow(
                        id=msg.id,
                        chat_id=chat.conversation_id,
                        pipeline_run_id=chat.pipeline_run_id,
                        position=msg.position if msg.position is not None else index,
                        timestamp=msg.timestamp,
                        sender=msg.sender,
                        text=msg.text,
                        data=_json_dumps(msg.data) if msg.data else None,
                    )
                    session.merge(msg_row)
                session.commit()
            return chat.conversation_id, chat.pipeline_run_id

    def upsert_chat_message(
        self,
        conversation_id: str,
        pipeline_run_id: str,
        message: ChatMessage,
    ) -> int:
        engine = self._get_engine()
        with Session(engine) as session:
            position = message.position
            if position is None:
                max_position = session.scalar(
                    select(func.max(ChatMessageRow.position)).where(
                        ChatMessageRow.chat_id == conversation_id,
                        ChatMessageRow.pipeline_run_id == pipeline_run_id,
                    )
                )
                position = (max_position or 0) + 1
            msg_row = ChatMessageRow(
                id=message.id,
                chat_id=conversation_id,
                pipeline_run_id=pipeline_run_id,
                position=position,
                timestamp=message.timestamp,
                sender=message.sender,
                text=message.text,
                data=_json_dumps(message.data) if message.data else None,
            )
            merged = session.merge(msg_row)
            session.commit()
            return merged.id

    def replace_chat_messages(
        self,
        conversation_id: str,
        pipeline_run_id: str,
        messages: list[ChatMessage],
    ) -> None:
        engine = self._get_engine()
        with Session(engine) as session:
            session.query(ChatMessageRow).filter(
                ChatMessageRow.chat_id == conversation_id,
                ChatMessageRow.pipeline_run_id == pipeline_run_id,
            ).delete()
            for index, msg in enumerate(messages):
                msg_row = ChatMessageRow(
                    chat_id=conversation_id,
                    pipeline_run_id=pipeline_run_id,
                    position=msg.position if msg.position is not None else index,
                    timestamp=msg.timestamp,
                    sender=msg.sender,
                    text=msg.text,
                    data=_json_dumps(msg.data) if msg.data else None,
                )
                session.add(msg_row)
            session.commit()

    def upsert_corrected_chat(
        self,
        original_conversation_id: str,
        original_pipeline_run_id: str,
        messages: list[CorrectedChatMessage],
    ) -> str:
        engine = self._get_engine()
        with Session(engine) as session:
            stmt = select(CorrectedChatRow).where(
                CorrectedChatRow.original_conversation_id == original_conversation_id,
                CorrectedChatRow.original_pipeline_run_id == original_pipeline_run_id,
            )
            corrected = session.scalars(stmt).first()
            now = _utcnow()
            if corrected is None:
                corrected = CorrectedChatRow(
                    conversation_id=original_conversation_id,
                    pipeline_run_id=original_pipeline_run_id,
                    original_conversation_id=original_conversation_id,
                    original_pipeline_run_id=original_pipeline_run_id,
                    created_at=now,
                    updated_at=now,
                )
                session.add(corrected)
                session.flush()
            else:
                corrected.updated_at = now
                # Un-tombstone any previously soft-deleted corrected chat when it is updated:
                # setting deleted_at back to None marks this corrected chat as active again.
                corrected.deleted_at = None
                corrected.messages.clear()
                session.flush()

            for index, msg in enumerate(messages):
                msg_row = CorrectedChatMessageRow(
                    corrected_chat_id=corrected.conversation_id,
                    corrected_pipeline_run_id=corrected.pipeline_run_id,
                    original_message_id=msg.original_message_id,
                    position=index,
                    timestamp=msg.timestamp,
                    sender=msg.sender,
                    text=msg.text,
                    data=_json_dumps(msg.data) if msg.data else None,
                )
                session.add(msg_row)
            session.commit()
            return corrected.conversation_id

    def fetch_recent_chats(
        self,
        limit: int | None = None,
        corrected: bool | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Chat]:
        engine = self._get_engine()
        with Session(engine) as session:
            run_timestamp = func.coalesce(ChatRow.run_timestamp, ChatRow.created_at)
            stmt = (
                select(ChatRow)
                .where(ChatRow.deleted_at.is_(None))
                .order_by(ChatRow.created_at.desc())
            )
            if corrected is True:
                stmt = stmt.join(
                    CorrectedChatRow,
                    (CorrectedChatRow.original_conversation_id == ChatRow.conversation_id)
                    & (CorrectedChatRow.original_pipeline_run_id == ChatRow.pipeline_run_id),
                )
                stmt = stmt.where(CorrectedChatRow.deleted_at.is_(None))
            elif corrected is False:
                stmt = stmt.outerjoin(
                    CorrectedChatRow,
                    (CorrectedChatRow.original_conversation_id == ChatRow.conversation_id)
                    & (CorrectedChatRow.original_pipeline_run_id == ChatRow.pipeline_run_id),
                ).where(
                    (CorrectedChatRow.conversation_id.is_(None))
                    | (CorrectedChatRow.deleted_at.is_not(None))
                )
            if start is not None:
                stmt = stmt.where(run_timestamp >= start)
            if end is not None:
                stmt = stmt.where(run_timestamp <= end)
            stmt = stmt.options(
                selectinload(ChatRow.messages),
                selectinload(ChatRow.corrected).selectinload(CorrectedChatRow.messages),
            )
            if limit:
                stmt = stmt.limit(limit)
            rows = session.scalars(stmt).all()
        return [_row_to_chat(row) for row in rows]

    def fetch_chats_page(
        self,
        limit: int,
        offset: int = 0,
        corrected: bool | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[list[Chat], int]:
        return self._fetch_chats(limit, offset, corrected, start, end, include_total=True)

    def fetch_chats(
        self,
        limit: int,
        offset: int = 0,
        corrected: bool | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Chat]:
        chats, _ = self._fetch_chats(limit, offset, corrected, start, end, include_total=False)
        return chats

    def _fetch_chats(
        self,
        limit: int,
        offset: int,
        corrected: bool | None,
        start: datetime | None,
        end: datetime | None,
        *,
        include_total: bool,
    ) -> tuple[list[Chat], int]:
        engine = self._get_engine()
        with Session(engine) as session:
            run_timestamp = func.coalesce(ChatRow.run_timestamp, ChatRow.created_at)
            filters = [ChatRow.deleted_at.is_(None)]
            join = None
            if corrected is True:
                join = (
                    CorrectedChatRow,
                    (CorrectedChatRow.original_conversation_id == ChatRow.conversation_id)
                    & (CorrectedChatRow.original_pipeline_run_id == ChatRow.pipeline_run_id),
                )
                filters.append(CorrectedChatRow.deleted_at.is_(None))
            elif corrected is False:
                join = (
                    CorrectedChatRow,
                    (CorrectedChatRow.original_conversation_id == ChatRow.conversation_id)
                    & (CorrectedChatRow.original_pipeline_run_id == ChatRow.pipeline_run_id),
                )
                filters.append(
                    (CorrectedChatRow.conversation_id.is_(None))
                    | (CorrectedChatRow.deleted_at.is_not(None))
                )
            if start is not None:
                filters.append(run_timestamp >= start)
            if end is not None:
                filters.append(run_timestamp <= end)

            chats_stmt = select(ChatRow)
            if join is not None:
                if corrected is False:
                    chats_stmt = chats_stmt.outerjoin(*join)
                else:
                    chats_stmt = chats_stmt.join(*join)
            total = 0
            if include_total:
                count_stmt = select(func.count()).select_from(ChatRow)
                if join is not None:
                    count_stmt = (
                        count_stmt.outerjoin(*join)
                        if corrected is False
                        else count_stmt.join(*join)
                    )
                total = session.scalar(count_stmt.where(*filters)) or 0
            rows = session.scalars(
                chats_stmt.where(*filters)
                .order_by(
                    ChatRow.created_at.desc(),
                    ChatRow.conversation_id.desc(),
                    ChatRow.pipeline_run_id.desc(),
                )
                .offset(offset)
                .limit(limit)
                .options(
                    selectinload(ChatRow.messages),
                    selectinload(ChatRow.corrected).selectinload(CorrectedChatRow.messages),
                )
            ).all()
        return [_row_to_chat(row) for row in rows], total

    def fetch_latest_chat_by_conversation_id(self, conversation_id: str) -> Chat | None:
        engine = self._get_engine()
        with Session(engine) as session:
            stmt = (
                select(ChatRow)
                .where(ChatRow.conversation_id == conversation_id)
                .order_by(ChatRow.created_at.desc())
                .limit(1)
                .options(
                    selectinload(ChatRow.messages),
                    selectinload(ChatRow.corrected).selectinload(CorrectedChatRow.messages),
                )
            )
            row = session.scalars(stmt).first()
        if row is None:
            return None
        return _row_to_chat(row)

    def count_uncorrected_chats(self) -> int:
        engine = self._get_engine()
        with Session(engine) as session:
            stmt = (
                select(func.count(ChatRow.conversation_id))
                .outerjoin(
                    CorrectedChatRow,
                    (CorrectedChatRow.original_conversation_id == ChatRow.conversation_id)
                    & (CorrectedChatRow.original_pipeline_run_id == ChatRow.pipeline_run_id),
                )
                .where(ChatRow.deleted_at.is_(None))
                .where(
                    (CorrectedChatRow.conversation_id.is_(None))
                    | (CorrectedChatRow.deleted_at.is_not(None))
                )
            )
            return int(session.scalar(stmt) or 0)

    def delete_chat(self, conversation_id: str, pipeline_run_id: str) -> None:
        engine = self._get_engine()
        with Session(engine) as session:
            chat_row = session.get(
                ChatRow,
                {
                    "conversation_id": conversation_id,
                    "pipeline_run_id": pipeline_run_id,
                },
            )
            if chat_row is None:
                return
            session.delete(chat_row)
            session.commit()

    def delete_corrected_chat(self, conversation_id: str, pipeline_run_id: str) -> None:
        engine = self._get_engine()
        with Session(engine) as session:
            corrected_row = session.get(
                CorrectedChatRow,
                {
                    "conversation_id": conversation_id,
                    "pipeline_run_id": pipeline_run_id,
                },
            )
            if corrected_row is None:
                return
            session.delete(corrected_row)
            session.commit()

    def tombstone_targets(self, targets: list[TombstoneTarget]) -> None:
        if not targets:
            return
        engine = self._get_engine()
        now = _utcnow()
        chat_keys: list[tuple[str, str]] = []
        corrected_chat_keys: list[tuple[str, str]] = []
        message_ids: list[int] = []
        corrected_message_ids: list[int] = []

        for target in targets:
            if target.kind == "chat":
                chat_keys.append((target.conversation_id, target.pipeline_run_id))  # type: ignore[arg-type]
            elif target.kind == "message":
                message_ids.append(target.message_id)  # type: ignore[arg-type]
            elif target.kind == "corrected_chat":
                corrected_chat_keys.append((target.conversation_id, target.pipeline_run_id))  # type: ignore[arg-type]
            elif target.kind == "corrected_message":
                corrected_message_ids.append(target.corrected_message_id)  # type: ignore[arg-type]

        with Session(engine) as session:
            if chat_keys:
                session.query(ChatRow).filter(
                    tuple_(ChatRow.conversation_id, ChatRow.pipeline_run_id).in_(chat_keys)
                ).update({ChatRow.deleted_at: now}, synchronize_session=False)
                session.query(ChatMessageRow).filter(
                    tuple_(ChatMessageRow.chat_id, ChatMessageRow.pipeline_run_id).in_(chat_keys)
                ).update({ChatMessageRow.deleted_at: now}, synchronize_session=False)
                session.query(CorrectedChatRow).filter(
                    tuple_(
                        CorrectedChatRow.original_conversation_id,
                        CorrectedChatRow.original_pipeline_run_id,
                    ).in_(chat_keys)
                ).update({CorrectedChatRow.deleted_at: now}, synchronize_session=False)
                session.query(CorrectedChatMessageRow).filter(
                    tuple_(
                        CorrectedChatMessageRow.corrected_chat_id,
                        CorrectedChatMessageRow.corrected_pipeline_run_id,
                    ).in_(chat_keys)
                ).update({CorrectedChatMessageRow.deleted_at: now}, synchronize_session=False)

            if corrected_chat_keys:
                session.query(CorrectedChatRow).filter(
                    tuple_(CorrectedChatRow.conversation_id, CorrectedChatRow.pipeline_run_id).in_(
                        corrected_chat_keys
                    )
                ).update({CorrectedChatRow.deleted_at: now}, synchronize_session=False)
                session.query(CorrectedChatMessageRow).filter(
                    tuple_(
                        CorrectedChatMessageRow.corrected_chat_id,
                        CorrectedChatMessageRow.corrected_pipeline_run_id,
                    ).in_(corrected_chat_keys)
                ).update({CorrectedChatMessageRow.deleted_at: now}, synchronize_session=False)

            if message_ids:
                session.query(ChatMessageRow).filter(ChatMessageRow.id.in_(message_ids)).update(
                    {ChatMessageRow.deleted_at: now}, synchronize_session=False
                )

            if corrected_message_ids:
                session.query(CorrectedChatMessageRow).filter(
                    CorrectedChatMessageRow.id.in_(corrected_message_ids)
                ).update({CorrectedChatMessageRow.deleted_at: now}, synchronize_session=False)

            session.commit()

    # --- Clips ------------------------------------------------------------

    def insert_clip(self, clip: Clip) -> int:
        """Insert a clip, returning its id. Re-inserting a filename is a no-op."""
        engine = self._get_engine()
        with Session(engine) as session:
            row = session.execute(
                select(ClipRow).where(ClipRow.filename == clip.filename)
            ).scalar_one_or_none()
            if row is None:
                row = ClipRow(
                    filename=clip.filename,
                    timestamp=clip.timestamp,
                    label=clip.label,
                    assistant_id=clip.assistant_id,
                    wake_word=clip.wake_word,
                    confidence=clip.confidence,
                    duration=clip.duration,
                    sample_rate=clip.sample_rate,
                    sample_width=clip.sample_width,
                    channels=clip.channels,
                    peaks=_json_dumps(clip.peaks) if clip.peaks else None,
                    data=_json_dumps(clip.data) if clip.data else None,
                    deleted_at=clip.deleted_at,
                )
                session.add(row)
                session.flush()
            clip_id = int(row.id)
            session.commit()
            return clip_id

    def _clip_filters(self, request: ClipListRequest) -> list[Any]:
        filters: list[Any] = []
        if request.start is not None:
            filters.append(ClipRow.timestamp >= request.start)
        if request.end is not None:
            filters.append(ClipRow.timestamp <= request.end)
        if request.assistant_id:
            filters.append(ClipRow.assistant_id == request.assistant_id)
        if request.deleted_only:
            filters.append(ClipRow.deleted_at.is_not(None))
        elif not request.include_deleted:
            filters.append(ClipRow.deleted_at.is_(None))
        if request.labeled_only:
            filters.append(
                and_(
                    ClipRow.label.is_not(None),
                    ClipRow.label.not_in((LABEL_UNLABELED, "")),
                )
            )
        if request.label == LABEL_UNLABELED:
            # Treat missing and empty labels as unlabeled too, so clips written by
            # the legacy add-on schema still surface in the review queue.
            filters.append(
                or_(
                    ClipRow.label == LABEL_UNLABELED,
                    ClipRow.label.is_(None),
                    ClipRow.label == "",
                )
            )
        elif request.label:
            filters.append(ClipRow.label == request.label)
        return filters

    def fetch_clips_page(self, request: ClipListRequest) -> ClipListResponse:
        engine = self._get_engine()
        filters = self._clip_filters(request)
        # Per-label totals ignore the queue filters so the panel can render every
        # tab count from one round trip.
        scope = ClipListRequest(
            limit=request.limit,
            offset=request.offset,
            assistant_id=request.assistant_id,
            start=request.start,
            end=request.end,
        )
        scope_filters = self._clip_filters(scope)
        deleted_filters = self._clip_filters(
            scope.model_copy(update={"deleted_only": True}),
        )

        with Session(engine) as session:
            rows = (
                session.execute(
                    select(ClipRow)
                    .where(*filters)
                    .order_by(ClipRow.timestamp.desc(), ClipRow.id.desc())
                    .limit(request.limit)
                    .offset(request.offset)
                )
                .scalars()
                .all()
            )
            total = int(
                session.execute(
                    select(func.count()).select_from(ClipRow).where(*filters)
                ).scalar_one()
            )
            counts = dict(
                session.execute(
                    select(ClipRow.label, func.count())
                    .where(*scope_filters)
                    .group_by(ClipRow.label)
                ).all()
            )
            deleted_total = int(
                session.execute(
                    select(func.count()).select_from(ClipRow).where(*deleted_filters)
                ).scalar_one()
            )

        label_counts = {label: int(counts.get(label, 0)) for label in WAKE_LABELS}
        unlabeled = sum(
            int(count) for label, count in counts.items() if label in (LABEL_UNLABELED, "", None)
        )
        label_counts[LABEL_UNLABELED] = unlabeled
        return ClipListResponse(
            clips=[_row_to_clip(row) for row in rows],
            total=total,
            unlabeled_total=unlabeled,
            labeled_total=sum(label_counts[label] for label in WAKE_LABELS),
            deleted_total=deleted_total,
            label_counts=label_counts,
        )

    def count_unlabeled_clips(self) -> int:
        engine = self._get_engine()
        with Session(engine) as session:
            return int(
                session.execute(
                    select(func.count())
                    .select_from(ClipRow)
                    .where(
                        ClipRow.deleted_at.is_(None),
                        or_(
                            ClipRow.label == LABEL_UNLABELED,
                            ClipRow.label.is_(None),
                            ClipRow.label == "",
                        ),
                    )
                ).scalar_one()
            )

    def count_clips_by_assistant(self) -> dict[str, int]:
        engine = self._get_engine()
        with Session(engine) as session:
            rows = session.execute(
                select(ClipRow.assistant_id, func.count())
                .where(ClipRow.deleted_at.is_(None))
                .group_by(ClipRow.assistant_id)
            ).all()
        return {str(assistant): int(count) for assistant, count in rows if assistant}

    def fetch_clip(self, clip_id: int) -> Clip | None:
        engine = self._get_engine()
        with Session(engine) as session:
            row = session.get(ClipRow, clip_id)
            return _row_to_clip(row) if row is not None else None

    def fetch_clips_for_export(self, request: ClipListRequest) -> list[Clip]:
        engine = self._get_engine()
        filters = self._clip_filters(request)
        with Session(engine) as session:
            rows = (
                session.execute(
                    select(ClipRow)
                    .where(*filters)
                    .order_by(ClipRow.timestamp.desc(), ClipRow.id.desc())
                )
                .scalars()
                .all()
            )
            return [_row_to_clip(row) for row in rows]

    def label_clips(self, clip_ids: list[int], label: str) -> int:
        engine = self._get_engine()
        with Session(engine) as session:
            updated = (
                session.query(ClipRow)
                .filter(ClipRow.id.in_(clip_ids))
                .update({ClipRow.label: label}, synchronize_session=False)
            )
            session.commit()
            return int(updated)

    def tombstone_clips(self, clip_ids: list[int], restore: bool = False) -> int:
        engine = self._get_engine()
        value = None if restore else _utcnow()
        with Session(engine) as session:
            updated = (
                session.query(ClipRow)
                .filter(ClipRow.id.in_(clip_ids))
                .update({ClipRow.deleted_at: value}, synchronize_session=False)
            )
            session.commit()
            return int(updated)

    def purge_clips_before(self, cutoff: datetime) -> list[str]:
        """Hard-delete clip rows older than the cutoff, returning their filenames."""
        engine = self._get_engine()
        with Session(engine) as session:
            rows = (
                session.execute(select(ClipRow).where(ClipRow.timestamp < cutoff)).scalars().all()
            )
            filenames = [row.filename for row in rows]
            for row in rows:
                session.delete(row)
            session.commit()
        return filenames

    def known_clip_filenames(self) -> set[str]:
        engine = self._get_engine()
        with Session(engine) as session:
            return set(session.execute(select(ClipRow.filename)).scalars().all())

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            db_path = get_db_path(self._hass)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._engine = create_engine(f"sqlite:///{db_path}", future=True)
            if self._engine.dialect.name == "sqlite":
                event.listen(self._engine, "connect", _enable_sqlite_foreign_keys)
        return self._engine


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _get_client(hass: HomeAssistant) -> IntentsityDBClient:
    domain_data = hass.data.setdefault(DOMAIN, {})
    client: IntentsityDBClient | None = domain_data.get(_CLIENT_KEY)
    if client is None:
        client = IntentsityDBClient(hass)
        domain_data[_CLIENT_KEY] = client
    return client


def dispose_client(hass: HomeAssistant) -> None:
    domain_data = hass.data.get(DOMAIN)
    if not isinstance(domain_data, dict):
        return

    client: IntentsityDBClient | None = domain_data.pop(_CLIENT_KEY, None)
    if client is not None:
        client.dispose()


def init_db(hass: HomeAssistant) -> None:
    _get_client(hass).ensure_initialized()


def upsert_chat(hass: HomeAssistant, chat: Chat) -> tuple[str, str]:
    return _get_client(hass).upsert_chat(chat)


def upsert_chat_message(
    hass: HomeAssistant,
    conversation_id: str,
    pipeline_run_id: str,
    message: ChatMessage,
) -> int:
    return _get_client(hass).upsert_chat_message(conversation_id, pipeline_run_id, message)


def replace_chat_messages(
    hass: HomeAssistant,
    conversation_id: str,
    pipeline_run_id: str,
    messages: list[ChatMessage],
) -> None:
    return _get_client(hass).replace_chat_messages(conversation_id, pipeline_run_id, messages)


def fetch_recent_chats(
    hass: HomeAssistant,
    limit: int | None = None,
    corrected: bool | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[Chat]:
    return _get_client(hass).fetch_recent_chats(limit, corrected, start, end)


def fetch_chats_page(
    hass: HomeAssistant,
    limit: int,
    offset: int = 0,
    corrected: bool | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[list[Chat], int]:
    return _get_client(hass).fetch_chats_page(limit, offset, corrected, start, end)


def fetch_chats(
    hass: HomeAssistant,
    limit: int,
    offset: int = 0,
    corrected: bool | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[Chat]:
    return _get_client(hass).fetch_chats(limit, offset, corrected, start, end)


def fetch_latest_chat_by_conversation_id(hass: HomeAssistant, conversation_id: str) -> Chat | None:
    return _get_client(hass).fetch_latest_chat_by_conversation_id(conversation_id)


def upsert_corrected_chat(
    hass: HomeAssistant,
    original_conversation_id: str,
    original_pipeline_run_id: str,
    messages: list[CorrectedChatMessage],
) -> str:
    return _get_client(hass).upsert_corrected_chat(
        original_conversation_id, original_pipeline_run_id, messages
    )


def count_uncorrected_chats(hass: HomeAssistant) -> int:
    return _get_client(hass).count_uncorrected_chats()


def delete_chat(
    hass: HomeAssistant,
    conversation_id: str,
    pipeline_run_id: str,
) -> None:
    return _get_client(hass).delete_chat(conversation_id, pipeline_run_id)


def delete_corrected_chat(
    hass: HomeAssistant,
    conversation_id: str,
    pipeline_run_id: str,
) -> None:
    return _get_client(hass).delete_corrected_chat(conversation_id, pipeline_run_id)


def tombstone_targets(hass: HomeAssistant, targets: list[TombstoneTarget]) -> None:
    return _get_client(hass).tombstone_targets(targets)


def insert_clip(hass: HomeAssistant, clip: Clip) -> int:
    return _get_client(hass).insert_clip(clip)


def fetch_clips_page(hass: HomeAssistant, request: ClipListRequest) -> ClipListResponse:
    return _get_client(hass).fetch_clips_page(request)


def fetch_clip(hass: HomeAssistant, clip_id: int) -> Clip | None:
    return _get_client(hass).fetch_clip(clip_id)


def fetch_clips_for_export(hass: HomeAssistant, request: ClipListRequest) -> list[Clip]:
    return _get_client(hass).fetch_clips_for_export(request)


def count_unlabeled_clips(hass: HomeAssistant) -> int:
    return _get_client(hass).count_unlabeled_clips()


def count_clips_by_assistant(hass: HomeAssistant) -> dict[str, int]:
    return _get_client(hass).count_clips_by_assistant()


def label_clips(hass: HomeAssistant, clip_ids: list[int], label: str) -> int:
    return _get_client(hass).label_clips(clip_ids, label)


def tombstone_clips(hass: HomeAssistant, clip_ids: list[int], restore: bool = False) -> int:
    return _get_client(hass).tombstone_clips(clip_ids, restore)


def prune_clips(hass: HomeAssistant, retention_days: int) -> int:
    """Delete clip rows and WAV files older than the retention window."""
    if retention_days <= 0:
        return 0
    cutoff = _utcnow() - timedelta(days=retention_days)
    filenames = _get_client(hass).purge_clips_before(cutoff)
    clips_dir = get_clips_dir(hass)
    for filename in filenames:
        for path in (clips_dir / filename, (clips_dir / filename).with_suffix(".json")):
            path.unlink(missing_ok=True)
    return len(filenames)


def import_legacy_clips(hass: HomeAssistant, legacy_db: Path) -> int:
    """Import rows from a wake-word add-on `clips.db` into the unified schema.

    Existing filenames are skipped, so running this twice is harmless.
    """
    import sqlite3

    from .const import LEGACY_LABEL_MAP

    if not legacy_db.is_file():
        return 0

    client = _get_client(hass)
    client.ensure_initialized()
    known = client.known_clip_filenames()

    imported = 0
    connection = sqlite3.connect(f"file:{legacy_db}?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute("SELECT * FROM clips").fetchall()
        except sqlite3.DatabaseError:
            return 0
        for row in rows:
            keys = row.keys()
            filename = row["filename"] if "filename" in keys else None
            if not filename or filename in known:
                continue
            legacy_label = row["label"] if "label" in keys else None
            deleted = bool(row["deleted"]) if "deleted" in keys else False
            clip = Clip(
                filename=filename,
                timestamp=parse_timestamp(row["timestamp"] if "timestamp" in keys else None),
                label=LEGACY_LABEL_MAP.get(legacy_label or "", LABEL_UNLABELED),
                assistant_id=row["assistant_id"] if "assistant_id" in keys else None,
                duration=row["duration"] if "duration" in keys else None,
                sample_rate=row["sample_rate"] if "sample_rate" in keys else None,
                deleted_at=_utcnow() if deleted else None,
            )
            client.insert_clip(clip)
            imported += 1
    finally:
        connection.close()
    return imported


def _row_to_clip(row: ClipRow) -> Clip:
    return Clip(
        id=row.id,
        filename=row.filename,
        timestamp=parse_timestamp(row.timestamp),
        label=row.label or LABEL_UNLABELED,
        assistant_id=row.assistant_id,
        wake_word=row.wake_word,
        confidence=row.confidence,
        duration=row.duration,
        sample_rate=row.sample_rate,
        sample_width=row.sample_width,
        channels=row.channels,
        peaks=orjson.loads(row.peaks) if row.peaks else [],
        data=orjson.loads(row.data) if row.data else {},
        deleted_at=parse_timestamp(row.deleted_at) if row.deleted_at is not None else None,
    )


def _row_to_chat(row: ChatRow) -> Chat:
    messages = [
        ChatMessage(
            id=msg.id,
            chat_id=msg.chat_id,
            position=msg.position,
            timestamp=parse_timestamp(msg.timestamp),
            sender=msg.sender,
            text=msg.text,
            data=orjson.loads(msg.data) if msg.data else {},
            deleted_at=parse_timestamp(msg.deleted_at) if msg.deleted_at is not None else None,
        )
        for msg in row.messages
        if msg.deleted_at is None
    ]
    corrected = None
    if row.corrected is not None and row.corrected.deleted_at is None:
        corrected_messages = [
            CorrectedChatMessage(
                id=msg.id,
                corrected_chat_id=msg.corrected_chat_id,
                original_message_id=msg.original_message_id,
                position=msg.position,
                timestamp=parse_timestamp(msg.timestamp),
                sender=msg.sender,
                text=msg.text,
                data=orjson.loads(msg.data) if msg.data else {},
                deleted_at=parse_timestamp(msg.deleted_at) if msg.deleted_at is not None else None,
            )
            for msg in row.corrected.messages
            if msg.deleted_at is None
        ]
        corrected = CorrectedChat(
            conversation_id=row.corrected.conversation_id,
            pipeline_run_id=row.corrected.pipeline_run_id,
            original_conversation_id=row.corrected.original_conversation_id,
            original_pipeline_run_id=row.corrected.original_pipeline_run_id,
            created_at=parse_timestamp(row.corrected.created_at),
            updated_at=parse_timestamp(row.corrected.updated_at),
            messages=corrected_messages,
            deleted_at=parse_timestamp(row.corrected.deleted_at)
            if row.corrected.deleted_at is not None
            else None,
        )
    return Chat(
        conversation_id=row.conversation_id,
        pipeline_run_id=row.pipeline_run_id,
        run_timestamp=parse_timestamp(row.run_timestamp),
        created_at=parse_timestamp(row.created_at),
        messages=messages,
        corrected=corrected,
        deleted_at=parse_timestamp(row.deleted_at) if row.deleted_at is not None else None,
    )
