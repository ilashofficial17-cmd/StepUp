"""Админ-команды. Доступны только telegram_id из config.ADMIN_IDS."""

import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import ADMIN_IDS
from content.courses import COURSES_BY_ID
from database.db import (
    get_or_create_user,
    get_user_by_telegram_id,
    grant_course_access,
    has_course_access,
)

log = logging.getLogger(__name__)
router = Router()


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


@router.message(Command("grant"))
async def cmd_grant(message: Message, command: CommandObject):
    """`/grant <telegram_id> <course_id>` — выдать доступ к платному курсу вручную.

    Пример: /grant 123456789 target
    """
    if not _is_admin(message.from_user.id):
        return  # молча игнорируем — не выдаём что это админ-команда

    args = (command.args or "").split()
    if len(args) != 2:
        await message.answer(
            "Использование: `/grant <telegram_id> <course_id>`\n"
            "Пример: `/grant 123456789 target`",
            parse_mode="Markdown",
        )
        return

    try:
        target_tg = int(args[0])
    except ValueError:
        await message.answer("telegram_id должен быть числом")
        return
    course_id = args[1]

    course = COURSES_BY_ID.get(course_id)
    if not course:
        await message.answer(f"Курс `{course_id}` не найден.", parse_mode="Markdown")
        return
    if course["is_free"]:
        await message.answer(f"Курс `{course_id}` бесплатный — доступ уже есть у всех.", parse_mode="Markdown")
        return

    user_db_id = await get_user_by_telegram_id(target_tg)
    if not user_db_id:
        # Если пользователь ещё не пользовался ботом — создадим запись
        user_db_id = await get_or_create_user(target_tg, "", "")
        note = " (пользователь создан впервые)"
    else:
        note = ""

    if await has_course_access(user_db_id, course_id):
        await message.answer(
            f"У пользователя `{target_tg}` уже есть доступ к курсу «{course['title']}».",
            parse_mode="Markdown",
        )
        return

    await grant_course_access(user_db_id, course_id, source="admin")
    await message.answer(
        f"✅ Выдан доступ: `{target_tg}` → «{course['title']}`{note}.",
        parse_mode="Markdown",
    )
    log.info("Admin %s granted %s → %s", message.from_user.id, target_tg, course_id)


@router.message(Command("whoami"))
async def cmd_whoami(message: Message):
    """Показывает telegram_id отправителя — полезно владельцу чтобы узнать свой id для ADMIN_IDS."""
    await message.answer(
        f"Твой telegram_id: `{message.from_user.id}`\n"
        f"{'Ты админ ✅' if _is_admin(message.from_user.id) else 'Ты не админ.'}",
        parse_mode="Markdown",
    )
