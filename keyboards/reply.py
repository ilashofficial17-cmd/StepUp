from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Курсы"), KeyboardButton(text="📊 Мой прогресс")],
        ],
        resize_keyboard=True,
        persistent=True,
    )
