from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆓 Первый шаг")],
            [KeyboardButton(text="📣 Продвижение"), KeyboardButton(text="💼 Бизнес")],
            [KeyboardButton(text="🤖 Технологии"), KeyboardButton(text="📊 Прогресс")],
        ],
        resize_keyboard=True,
        persistent=True,
    )
