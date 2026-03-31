import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# ==========================
# Настройки бота
# ==========================
API_TOKEN = "BOT_TOKEN"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==========================
# Клавиатура
# ==========================
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Продолжить")]],
    resize_keyboard=True
)

# ==========================
# Хэндлер на команду /start
# ==========================
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    text = (
        "Привет! 👋 Добро пожаловать в StepUp!\n\n"
        "Мы — команда, которая делает обучение маркетингу, SMM, таргету и "
        "автоматизации продаж простым и понятным. 🚀\n\n"
        "С помощью StepUp ты:\n"
        "- Поймёшь, как работает современный маркетинг и автоматизация\n"
        "- Узнаешь, как управлять лидами и продажами, даже если раньше этим не занимался\n"
        "- Получишь практический опыт, а не только теорию\n\n"
        "🎯 Нажми «Продолжить», чтобы начать первый ознакомительный модуль!"
    )
    await message.answer(text, reply_markup=keyboard)

# ==========================
# Хэндлер на кнопку "Продолжить"
# ==========================
@dp.message(F.text == "Продолжить")
async def continue_module(message: types.Message):
    text = "Отлично! 🌟 Дальше пойдёт первый модуль (пока заглушка)."
    await message.answer(text)

# ==========================
# Запуск бота
# ==========================
async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
