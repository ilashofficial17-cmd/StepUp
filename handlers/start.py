from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from content.courses import COURSES_BY_ID, get_lesson
from database.db import get_or_create_user, get_user_progress
from keyboards.inline import continue_course_kb
from keyboards.reply import main_menu_kb

router = Router()

WELCOME_TEXT = (
    "Привет! 👋 Добро пожаловать в *StepUp*!\n\n"
    "Мы делаем обучение маркетингу, SMM, таргету и "
    "автоматизации простым и понятным. 🚀\n\n"
    "Выбери категорию внизу 👇"
)

MENU_TEXT = "Главное меню 👇"


async def _find_continue_target(user_db_id: int):
    """Возвращает (course_id, module_id, lesson_id, lesson_title) для самого
    свежего незавершённого курса, либо None."""
    progress = await get_user_progress(user_db_id)
    if not progress:
        return None
    # Берём первый незавершённый курс с сохранённым last_lesson_id.
    # (Сейчас бесплатный курс один — «intro» — так что этого достаточно.)
    for course_id, data in progress.items():
        if data.get("completed"):
            continue
        module_id = data.get("last_module_id")
        lesson_id = data.get("last_lesson_id")
        if not module_id or not lesson_id:
            continue
        lesson = get_lesson(course_id, module_id, lesson_id)
        if not lesson:
            continue
        return course_id, module_id, lesson_id, lesson["title"]
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_db_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(), parse_mode="Markdown")

    target = await _find_continue_target(user_db_id)
    if target:
        course_id, module_id, lesson_id, title = target
        course = COURSES_BY_ID.get(course_id)
        course_name = course["title"] if course else course_id
        await message.answer(
            f"📖 Ты остановился в курсе «{course_name}» на уроке «{title}».",
            reply_markup=continue_course_kb(course_id, module_id, lesson_id, title),
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    user_db_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )
    await message.answer(MENU_TEXT, reply_markup=main_menu_kb())
    target = await _find_continue_target(user_db_id)
    if target:
        course_id, module_id, lesson_id, title = target
        await message.answer(
            "Продолжим обучение? 👇",
            reply_markup=continue_course_kb(course_id, module_id, lesson_id, title),
        )
