from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database.db import get_or_create_user
from keyboards.reply import main_menu_kb

router = Router()

WELCOME_TEXT = (
    "Привет! 👋 Добро пожаловать в *StepUp*!\n\n"
    "Мы делаем обучение маркетингу, SMM, таргету и "
    "автоматизации простым и понятным. 🚀\n\n"
    "Выбери категорию внизу 👇"
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="Markdown")
