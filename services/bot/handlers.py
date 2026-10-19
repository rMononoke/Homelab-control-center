from datetime import datetime
import html
import logging
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from api_client import api_client
from keyboards import (
    ContainerCallback,
    HostCallback,
    get_containers_keyboard,
    get_status_keyboard,
)

logger = logging.getLogger("bot.handlers")
router = Router()


def format_uptime(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts) or "0m"


def format_host_status_text(data: dict) -> str:
    cpu = data.get("cpu_percent", 0.0)
    mem_p = data.get("memory_percent", 0.0)
    mem_u = data.get("memory_used_gb", 0.0)
    mem_t = data.get("memory_total_gb", 0.0)
    disk_p = data.get("disk_percent", 0.0)
    disk_f = data.get("disk_free_gb", 0.0)
    disk_t = data.get("disk_total_gb", 0.0)
    uptime = format_uptime(data.get("uptime_seconds", 0))
    now = datetime.now().strftime("%H:%M:%S")

    return (
        "🖥 <b>Homelab Host Status</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>CPU:</b> <code>{cpu}%</code>\n"
        f"🧠 <b>RAM:</b> <code>{mem_p}%</code> ({mem_u} GB / {mem_t} GB)\n"
        f"💾 <b>Диск:</b> <code>{disk_p}%</code> (свободно {disk_f} GB из {disk_t} GB)\n"
        f"⏱ <b>Uptime:</b> <code>{uptime}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>🕒 Обновлено: {now}</i>"
    )


def format_containers_header(count: int) -> str:
    now = datetime.now().strftime("%H:%M:%S")
    return (
        "🐳 <b>Управление Docker-контейнерами:</b>\n\n"
        f"Всего контейнеров: <b>{count}</b>\n"
        f"<i>🕒 Обновлено: {now}</i>\n\n"
        "Выберите контейнер и действие:"
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "👋 <b>Добро пожаловать в Homelab Control Center!</b>\n\n"
        "Доступные команды управления:\n"
        "📊 /status — Текущее состояние ресурсов хоста (CPU, RAM, Диск, Uptime)\n"
        "🐳 /containers — Список и управление Docker-контейнерами\n\n"
        "Все управляющие действия логируются в PostgreSQL Audit Log."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("status"))
async def cmd_status(message: Message):
    try:
        data = await api_client.get_host_status()
        text = format_host_status_text(data)
        await message.answer(text, reply_markup=get_status_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error fetching host status: {e}")
        await message.answer(f"❌ Ошибка получения статуса хоста: {html.escape(str(e))}")


@router.callback_query(HostCallback.filter(F.action == "refresh"))
async def cb_refresh_status(callback: CallbackQuery):
    try:
        data = await api_client.get_host_status()
        text = format_host_status_text(data)
        try:
            await callback.message.edit_text(text, reply_markup=get_status_keyboard(), parse_mode="HTML")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
        await callback.answer("✅ Статус обновлен")
    except Exception as e:
        logger.error(f"Error updating host status: {e}")
        await callback.answer("❌ Ошибка обновления", show_alert=True)


@router.message(Command("containers"))
async def cmd_containers(message: Message):
    try:
        containers = await api_client.get_containers()
        if not containers:
            await message.answer("ℹ️ Контейнеры не найдены на хосте.")
            return

        text = format_containers_header(len(containers))
        await message.answer(
            text,
            reply_markup=get_containers_keyboard(containers),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error fetching containers: {e}")
        await message.answer(f"❌ Ошибка получения контейнеров: {html.escape(str(e))}")


@router.callback_query(ContainerCallback.filter(F.action == "refresh"))
async def cb_refresh_containers(callback: CallbackQuery):
    try:
        containers = await api_client.get_containers()
        text = format_containers_header(len(containers))
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_containers_keyboard(containers),
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
        await callback.answer("✅ Список контейнеров актуален")
    except Exception as e:
        logger.error(f"Error refreshing containers: {e}")
        await callback.answer("❌ Ошибка при обновлении списка", show_alert=True)


@router.callback_query(ContainerCallback.filter(F.action == "restart"))
async def cb_restart_container(callback: CallbackQuery, callback_data: ContainerCallback):
    cid = callback_data.container_id
    user_tag = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)

    await callback.answer("⏳ Перезапускаю контейнер...", show_alert=False)
    try:
        await api_client.restart_container(cid, triggered_by=user_tag)
        await callback.answer("✅ Контейнер перезапущен!", show_alert=True)

        containers = await api_client.get_containers()
        now = datetime.now().strftime("%H:%M:%S")
        text = (
            "🐳 <b>Управление Docker-контейнерами:</b>\n\n"
            f"✅ Контейнер <code>{cid[:12]}</code> успешно перезапущен!\n"
            f"Всего контейнеров: <b>{len(containers)}</b>\n"
            f"<i>🕒 Обновлено: {now}</i>"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_containers_keyboard(containers),
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
    except Exception as e:
        logger.error(f"Error restarting container {cid}: {e}")
        await callback.answer(f"❌ Ошибка рестарта: {str(e)[:100]}", show_alert=True)


@router.callback_query(ContainerCallback.filter(F.action == "stop"))
async def cb_stop_container(callback: CallbackQuery, callback_data: ContainerCallback):
    cid = callback_data.container_id
    user_tag = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)

    await callback.answer("⏳ Останавливаю контейнер...", show_alert=False)
    try:
        await api_client.stop_container(cid, triggered_by=user_tag)
        await callback.answer("⏹ Контейнер остановлен!", show_alert=True)

        containers = await api_client.get_containers()
        now = datetime.now().strftime("%H:%M:%S")
        text = (
            "🐳 <b>Управление Docker-контейнерами:</b>\n\n"
            f"⏹ Контейнер <code>{cid[:12]}</code> остановлен.\n"
            f"Всего контейнеров: <b>{len(containers)}</b>\n"
            f"<i>🕒 Обновлено: {now}</i>"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_containers_keyboard(containers),
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
    except Exception as e:
        logger.error(f"Error stopping container {cid}: {e}")
        await callback.answer(f"❌ Ошибка остановки: {str(e)[:100]}", show_alert=True)


@router.callback_query(ContainerCallback.filter(F.action == "start"))
async def cb_start_container(callback: CallbackQuery, callback_data: ContainerCallback):
    cid = callback_data.container_id
    user_tag = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)

    await callback.answer("⏳ Запускаю контейнер...", show_alert=False)
    try:
        await api_client.start_container(cid, triggered_by=user_tag)
        await callback.answer("▶️ Контейнер запущен!", show_alert=True)

        containers = await api_client.get_containers()
        now = datetime.now().strftime("%H:%M:%S")
        text = (
            "🐳 <b>Управление Docker-контейнерами:</b>\n\n"
            f"▶️ Контейнер <code>{cid[:12]}</code> запущен.\n"
            f"Всего контейнеров: <b>{len(containers)}</b>\n"
            f"<i>🕒 Обновлено: {now}</i>"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=get_containers_keyboard(containers),
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
    except Exception as e:
        logger.error(f"Error starting container {cid}: {e}")
        await callback.answer(f"❌ Ошибка запуска: {str(e)[:100]}", show_alert=True)


@router.callback_query(ContainerCallback.filter(F.action == "logs"))
async def cb_get_logs(callback: CallbackQuery, callback_data: ContainerCallback):
    cid = callback_data.container_id
    user_tag = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)

    await callback.answer("⏳ Запрашиваю логи...", show_alert=False)
    try:
        resp = await api_client.get_container_logs(cid, tail=20, triggered_by=user_tag)
        logs = resp.get("logs", "")
        if not logs.strip():
            logs = "Логи пусты."
        if len(logs) > 3500:
            logs = logs[-3500:]

        escaped_logs = html.escape(logs)
        await callback.message.answer(
            f"📜 <b>Логи контейнера <code>{cid[:12]}</code> (последние 20 строк):</b>\n\n"
            f"<pre><code>{escaped_logs}</code></pre>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error fetching logs for {cid}: {e}")
        await callback.answer(f"❌ Ошибка получения логов: {str(e)[:100]}", show_alert=True)
