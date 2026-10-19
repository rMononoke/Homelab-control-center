from typing import Any, Dict, List
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ContainerCallback(CallbackData, prefix="cnt"):
    action: str  # restart, stop, start, logs, refresh
    container_id: str


class HostCallback(CallbackData, prefix="host"):
    action: str  # refresh


def get_status_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Обновить статус",
        callback_data=HostCallback(action="refresh").pack(),
    )
    return builder.as_markup()


def get_containers_keyboard(containers: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for c in containers:
        # Telegram callback_data has a 64-byte limit, so always use short_id (12 chars)
        short_id = c.get("short_id") or (c.get("id") or "")[:12]
        name = c.get("name", "unknown")
        status = c.get("status", "")
        is_running = status.lower() == "running"

        state_icon = "🟢" if is_running else "🔴"

        # Container header button (informational, clicking shows logs)
        builder.row(
            InlineKeyboardButton(
                text=f"{state_icon} {name}",
                callback_data=ContainerCallback(action="logs", container_id=short_id).pack(),
            )
        )

        # Action buttons row
        row_buttons = [
            InlineKeyboardButton(
                text="🔄 Restart",
                callback_data=ContainerCallback(action="restart", container_id=short_id).pack(),
            )
        ]

        if is_running:
            row_buttons.append(
                InlineKeyboardButton(
                    text="⏹ Stop",
                    callback_data=ContainerCallback(action="stop", container_id=short_id).pack(),
                )
            )
        else:
            row_buttons.append(
                InlineKeyboardButton(
                    text="▶️ Start",
                    callback_data=ContainerCallback(action="start", container_id=short_id).pack(),
                )
            )

        row_buttons.append(
            InlineKeyboardButton(
                text="📜 Logs",
                callback_data=ContainerCallback(action="logs", container_id=short_id).pack(),
            )
        )

        builder.row(*row_buttons)

    # General refresh button at bottom
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить список",
            callback_data=ContainerCallback(action="refresh", container_id="all").pack(),
        )
    )

    return builder.as_markup()
