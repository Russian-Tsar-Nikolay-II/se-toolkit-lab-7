from __future__ import annotations

import asyncio
import re
import sys
from typing import Any, Callable

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from services.llm_router import LLMRouter
from services.lms_client import LMSClient, load_env

load_env()

client = LMSClient()
router = LLMRouter(client=client)


def start_text() -> str:
    return (
        "Welcome to SE Toolkit Bot!\n"
        "You can use slash commands or just ask in plain English.\n"
        "Examples: 'what labs are available?', 'show me scores for lab 4', "
        "'which lab has the lowest pass rate?'"
    )


def help_text() -> str:
    return (
        "Available commands:\n"
        "/start — welcome message\n"
        "/help — list all commands\n"
        "/health — check backend status\n"
        "/labs — list available labs\n"
        "/scores <lab> — show per-task pass rates, for example /scores lab-04\n\n"
        "You can also ask plain-text questions like:\n"
        "- what labs are available?\n"
        "- show me scores for lab 4\n"
        "- which lab has the lowest pass rate?\n"
        "- who are the top 5 students in lab 4?"
    )


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="What labs are available?",
                    callback_data="ask:what labs are available?",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Show scores for Lab 04",
                    callback_data="ask:show me scores for lab 4",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Lowest pass rate",
                    callback_data="ask:which lab has the lowest pass rate?",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Top 5 students in Lab 04",
                    callback_data="ask:who are the top 5 students in lab 4?",
                )
            ],
        ]
    )


def error_or_none(response: Any) -> str | None:
    if isinstance(response, dict) and "error" in response:
        return f"Backend error: {response['error']}"
    return None


def normalize_lab_slug(raw: str) -> str:
    value = raw.strip().lower()
    match = re.search(r"(\d+)", value)
    if match:
        return f"lab-{int(match.group(1)):02d}"
    return value.replace(" ", "")


def lab_label_from_text(raw: str) -> str:
    match = re.search(r"(\d+)", raw)
    if match:
        return f"Lab {int(match.group(1)):02d}"
    return raw.strip()


def split_lab_title(title: str, slug: str, fallback_id: object) -> tuple[int, str, str]:
    clean_title = " ".join(str(title or "").split())
    clean_slug = str(slug or "").strip().lower()

    title_match = re.match(r"(?i)^lab\s*0*(\d+)\s*[-—–:]\s*(.+)$", clean_title)
    if title_match:
        number = int(title_match.group(1))
        return number, f"Lab {number:02d}", title_match.group(2).strip()

    generic_match = re.match(r"(?i)^lab\s*0*(\d+)\b", clean_title)
    if generic_match:
        number = int(generic_match.group(1))
        desc = re.sub(r"(?i)^lab\s*0*\d+\s*[-—–:]?\s*", "", clean_title).strip()
        if not desc:
            desc = clean_title
        return number, f"Lab {number:02d}", desc

    slug_match = re.search(r"lab[-_\s]*0*(\d+)", clean_slug)
    if slug_match:
        number = int(slug_match.group(1))
        desc = clean_title or f"Lab {number:02d}"
        return number, f"Lab {number:02d}", desc

    if isinstance(fallback_id, int):
        return fallback_id, f"Lab {fallback_id:02d}", clean_title or f"Lab {fallback_id:02d}"

    return 999, clean_title or "Lab", clean_title or "Unnamed lab"


def health_text() -> str:
    response = client.get_items()
    error = error_or_none(response)
    if error:
        return error
    assert isinstance(response, list)
    return f"Backend is healthy. {len(response)} items available."


def labs_text() -> str:
    response = client.get_items()
    error = error_or_none(response)
    if error:
        return error
    assert isinstance(response, list)

    rows: list[tuple[int, str, str]] = []
    seen: set[str] = set()

    for item in response:
        item_type = str(item.get("type") or item.get("kind") or "").strip().lower()
        title = str(item.get("title") or item.get("name") or "").strip()
        slug = str(item.get("slug") or item.get("code") or item.get("lab") or "").strip()
        item_id = item.get("id")

        looks_like_lab = (
            item_type == "lab"
            or bool(re.match(r"(?i)^lab\s*0*\d+\b", title))
            or bool(re.match(r"(?i)^lab-\d+$", slug))
        )
        if not looks_like_lab:
            continue

        number, label, desc = split_lab_title(title, slug, item_id)
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append((number, label, desc))

    if not rows:
        return "No labs found."

    rows.sort(key=lambda row: row[0])
    lines = ["Available labs:"]
    for _, label, desc in rows:
        lines.append(f"- {label} — {desc}")
    return "\n".join(lines)


def extract_task_name(task: dict[str, Any]) -> str:
    for key in ("task", "name", "title", "task_name", "item_title", "label"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Unknown task"


def extract_attempts(task: dict[str, Any]) -> int:
    for key in ("attempts", "submission_count", "count", "num_attempts", "submissions"):
        value = task.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def extract_rate(task: dict[str, Any]) -> float:
    for key in ("pass_rate", "avg_score", "rate", "percentage", "avg"):
        value = task.get(key)
        if value is None:
            continue
        try:
            number = float(value)
            if 0.0 <= number <= 1.0:
                number *= 100.0
            return number
        except (TypeError, ValueError):
            continue
    return 0.0


def format_percent(value: float) -> str:
    rounded = round(value, 1)
    return f"{rounded:.1f}%"


def scores_text(arg: str | None) -> str:
    if not arg or not arg.strip():
        return "Please specify a lab: /scores <lab-id>"

    requested = arg.strip()
    lab_slug = normalize_lab_slug(requested)
    response = client.get_pass_rates(lab_slug)

    error = error_or_none(response)
    if error:
        return error
    assert isinstance(response, list)

    if not response:
        return f"No pass rates found for {lab_slug}."

    heading = lab_label_from_text(lab_slug)
    lines = [f"Pass rates for {heading}:"]
    for task in response:
        name = extract_task_name(task)
        rate = format_percent(extract_rate(task))
        attempts = extract_attempts(task)
        lines.append(f"- {name}: {rate} ({attempts} attempts)")
    return "\n".join(lines)


def unknown_command_text(command: str) -> str:
    return f"Unknown command '{command}'. Try /help"


TEST_COMMANDS: dict[str, Callable[..., str]] = {
    "/start": lambda: start_text(),
    "/help": lambda: help_text(),
    "/health": lambda: health_text(),
    "/labs": lambda: labs_text(),
    "/scores": scores_text,
}


def route_test_or_text(raw: str) -> str:
    text = raw.strip()
    if not text:
        return help_text()

    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        command = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        handler = TEST_COMMANDS.get(command)
        if handler is None:
            return unknown_command_text(command)

        if command == "/scores":
            return handler(arg)
        return handler()

    return router.route(text)


def run_test_mode() -> None:
    if len(sys.argv) < 3:
        print('Usage: uv run bot.py --test "/command [arg]"')
        raise SystemExit(1)

    raw = sys.argv[2]
    print(route_test_or_text(raw))


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Welcome message"),
            BotCommand(command="help", description="List commands"),
            BotCommand(command="health", description="Check backend status"),
            BotCommand(command="labs", description="List available labs"),
            BotCommand(command="scores", description="Show pass rates for a lab"),
        ]
    )


async def run_telegram_mode() -> None:
    from os import getenv

    token = getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN is not set. Configure it or run with --test.")

    dp = Dispatcher()

    @dp.message(CommandStart())
    async def handle_start(message: Message) -> None:
        await message.answer(start_text(), reply_markup=start_keyboard())

    @dp.message(Command("help"))
    async def handle_help(message: Message) -> None:
        await message.answer(help_text(), reply_markup=start_keyboard())

    @dp.message(Command("health"))
    async def handle_health(message: Message) -> None:
        await message.answer(health_text())

    @dp.message(Command("labs"))
    async def handle_labs(message: Message) -> None:
        await message.answer(labs_text())

    @dp.message(Command("scores"))
    async def handle_scores(message: Message, command: CommandObject) -> None:
        await message.answer(scores_text(command.args))

    @dp.callback_query(F.data.startswith("ask:"))
    async def handle_inline_question(callback: CallbackQuery) -> None:
        raw = callback.data[len("ask:") :] if callback.data else ""
        answer = await asyncio.to_thread(router.route, raw)
        if callback.message:
            await callback.message.answer(answer)
        await callback.answer()

    @dp.message(F.text.startswith("/"))
    async def handle_unknown_command(message: Message) -> None:
        assert message.text is not None
        command = message.text.strip().split(maxsplit=1)[0]
        await message.answer(unknown_command_text(command))

    @dp.message(F.text)
    async def handle_plain_text(message: Message) -> None:
        assert message.text is not None
        answer = await asyncio.to_thread(router.route, message.text)
        await message.answer(answer)

    bot = Bot(token=token)
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if "--test" in sys.argv:
        run_test_mode()
    else:
        asyncio.run(run_telegram_mode())
