from __future__ import annotations

import json
from typing import Any

from homeassistant.core import HomeAssistant

from . import db
from .models import (
    CorrectedChatExportRequest,
    CorrectedChatExportResponse,
    CorrectedChatMessage,
)


def _stringify_tool_result(value: Any) -> str:
    if isinstance(value, dict):
        content = value.get("content")
        if isinstance(content, list):
            texts = [
                str(item.get("text"))
                for item in content
                if isinstance(item, dict) and item.get("text") is not None
            ]
            if texts:
                return "\n".join(texts)
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=True)
    if value is None:
        return ""
    return str(value)


def _parse_tool_arguments(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_corrected_messages(
    messages: list[CorrectedChatMessage],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    used_tool_call_ids: set[str] = set()
    last_assistant_tool_call_ids: list[str] = []
    tool_call_counter = 0

    def _allocate_tool_call_id(raw_id: str | None) -> str:
        nonlocal tool_call_counter
        if raw_id and raw_id not in used_tool_call_ids:
            used_tool_call_ids.add(raw_id)
            return raw_id
        while True:
            tool_call_counter += 1
            candidate = f"tool_call_{tool_call_counter}"
            if candidate not in used_tool_call_ids:
                used_tool_call_ids.add(candidate)
                return candidate

    for message in messages:
        data = message.data or {}
        role = data.get("role") or message.sender
        has_tool_calls = "tool_calls" in data and data.get("tool_calls") is not None
        is_tool_result = role == "tool_result" or "tool_result" in data
        if role == "assistant" and not has_tool_calls:
            content_text = message.text
        else:
            content = data.get("content")
            if content is None:
                content = message.text
            content_text = str(content) if content is not None else ""

        if is_tool_result:
            tool_result = data.get("tool_result", message.text)
            tool_call_id = data.get("tool_call_id")
            if last_assistant_tool_call_ids and tool_call_id not in last_assistant_tool_call_ids:
                tool_call_id = last_assistant_tool_call_ids[-1]
            entry: dict[str, Any] = {
                "role": "tool",
                "content": _stringify_tool_result(tool_result),
            }
            tool_name = data.get("tool_name")
            if tool_name:
                entry["tool_name"] = tool_name
            if tool_call_id:
                entry["tool_call_id"] = tool_call_id
            output.append(entry)
            continue

        tool_calls_payload: list[dict[str, Any]] = []
        if has_tool_calls:
            raw_calls = data.get("tool_calls")
            if isinstance(raw_calls, list):
                for raw_call in raw_calls:
                    if isinstance(raw_call, dict):
                        name = raw_call.get("name") or raw_call.get("tool_name") or "unknown_tool"
                        arguments = _parse_tool_arguments(raw_call.get("tool_args"))
                        raw_id = raw_call.get("tool_call_id") or raw_call.get("id")
                    else:
                        name = str(raw_call)
                        arguments = {}
                        raw_id = None
                    tool_call_id = _allocate_tool_call_id(
                        str(raw_id) if raw_id is not None else None
                    )
                    tool_calls_payload.append(
                        {
                            "name": name,
                            "arguments": arguments if arguments is not None else {},
                            "tool_call_id": tool_call_id,
                        }
                    )
            last_assistant_tool_call_ids = [call["tool_call_id"] for call in tool_calls_payload]

        if "tool_call" in content_text or has_tool_calls:
            role = "assistant"

        if output and output[-1].get("role") == "system" and role != "tool":
            role = "user"

        entry = {"role": role}
        if tool_calls_payload:
            entry["tool_calls"] = tool_calls_payload
        if content_text or not tool_calls_payload:
            entry["content"] = content_text
        output.append(entry)
        if (role == "assistant" and not tool_calls_payload) or role in {"user", "system"}:
            last_assistant_tool_call_ids = []

    return output


def generate_corrected_jsonl(
    hass: HomeAssistant,
    request: CorrectedChatExportRequest,
) -> dict[str, Any]:
    chats = db.fetch_recent_chats(
        hass,
        request.limit,
        corrected=True,
        start=request.start,
        end=request.end,
    )
    grouped: dict[str, list[Any]] = {}
    for chat in chats:
        grouped.setdefault(chat.conversation_id, []).append(chat)
    lines: list[str] = []
    for conversation_id in sorted(grouped.keys()):
        runs = grouped[conversation_id]
        runs.sort(key=lambda run: (run.run_timestamp, run.created_at))
        combined: list[dict[str, Any]] = []
        for run in runs:
            corrected = run.corrected
            if corrected is None:
                continue
            normalized = _normalize_corrected_messages(corrected.messages)
            if normalized:
                combined.extend(normalized)
        if not combined:
            continue
        lines.append(json.dumps({"messages": combined}, ensure_ascii=True))

    response = CorrectedChatExportResponse(jsonl="\n".join(lines), count=len(lines))
    return response.model_dump(mode="json")
