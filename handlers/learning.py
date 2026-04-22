import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ai.tutor import generate_lesson_summary, get_tutor_reply
from content.courses import (
    COURSES_BY_ID,
    get_lesson,
    get_module,
    get_next_lesson,
    is_last_lesson_of_module,
    total_lessons_in_course,
)
from database.db import (
    get_completed_lesson_keys,
    get_conversation,
    get_course_summaries,
    get_or_create_user,
    get_quiz_result,
    mark_course_completed,
    save_lesson_summary,
    save_message,
)
from keyboards.inline import (
    after_lesson_kb,
    complete_lesson_kb,
    course_completed_kb,
)
from keyboards.reply import main_menu_kb
from states.learning import LearningState

log = logging.getLogger(__name__)
router = Router()

DONE_MARKER = "[LESSON_DONE]"


# ==========================
# Вспомогательные функции
# ==========================

def _strip_done_marker(text: str) -> tuple[str, bool]:
    """Вытаскивает маркер окончания урока. Возвращает (очищенный_текст, done_flag)."""
    if DONE_MARKER in text:
        cleaned = text.replace(DONE_MARKER, "").rstrip()
        return cleaned, True
    return text, False


async def _generate_and_save_summary(user_db_id: int, data: dict) -> None:
    """Фоновая генерация резюме урока."""
    course_id    = data["course_id"]
    module_id    = data["module_id"]
    lesson_id    = data["lesson_id"]
    lesson_title = data["lesson_title"]
    try:
        history = await get_conversation(user_db_id, course_id, module_id, lesson_id)
        if not history:
            return
        summary = await generate_lesson_summary(lesson_title, history)
        await save_lesson_summary(
            user_db_id, course_id, module_id, lesson_id, lesson_title, summary
        )
        completed = await get_completed_lesson_keys(user_db_id, course_id)
        if len(completed) >= total_lessons_in_course(course_id):
            await mark_course_completed(user_db_id, course_id)
    except Exception as e:
        log.warning("Не удалось сохранить резюме урока: %s", e)


async def _pause_lesson(message: Message, state: FSMContext) -> None:
    """Выход из урока БЕЗ отметки о завершении. Прогресс last_lesson сохраняется."""
    data = await state.get_data()
    await state.clear()
    if not data or "lesson_id" not in data:
        await message.answer("Главное меню 👇", reply_markup=main_menu_kb())
        return
    await message.answer(
        "⏸ Урок на паузе. Ты сможешь вернуться к нему с того же места — "
        "он ждёт тебя в «▶️ Продолжить».",
        reply_markup=main_menu_kb(),
    )


async def _complete_lesson(
    message: Message,
    user_db_id: int,
    course_id: str,
    module_id: str,
    lesson_id: str,
) -> None:
    """Отмечает урок пройденным и показывает кнопки «дальше»."""
    lesson = get_lesson(course_id, module_id, lesson_id)
    lesson_title = lesson["title"] if lesson else lesson_id

    # Предварительно кладём заглушку-резюме, чтобы lesson сразу попал в completed.
    # Полноценное AI-резюме сгенерится в фоне и перезапишет его.
    await save_lesson_summary(
        user_db_id, course_id, module_id, lesson_id, lesson_title,
        f"Урок «{lesson_title}» пройден.",
    )

    completed = await get_completed_lesson_keys(user_db_id, course_id)
    if len(completed) >= total_lessons_in_course(course_id):
        await mark_course_completed(user_db_id, course_id)

    next_lesson = get_next_lesson(course_id, module_id, lesson_id)
    quiz_done = await get_quiz_result(user_db_id, course_id, module_id)
    show_quiz = is_last_lesson_of_module(course_id, module_id, lesson_id) and not (
        quiz_done and quiz_done["passed"]
    )

    if not next_lesson and not show_quiz:
        await message.answer(
            "🎉 *Поздравляем!* Ты прошёл весь бесплатный курс «Первый шаг».\n\n"
            "Теперь ты можешь выбрать направление и двигаться глубже.",
            reply_markup=course_completed_kb(course_id),
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "✅ Урок пройден. Что дальше? 👇",
            reply_markup=after_lesson_kb(course_id, module_id, next_lesson, show_quiz),
        )

    # Перегенерируем AI-резюме в фоне (перезапишет заглушку)
    data = {
        "course_id": course_id,
        "module_id": module_id,
        "lesson_id": lesson_id,
        "lesson_title": lesson_title,
    }
    asyncio.create_task(_generate_and_save_summary(user_db_id, data))


# ==========================
# Команды во время урока
# ==========================

@router.message(LearningState.in_lesson, CommandStart())
async def lesson_start_command(message: Message, state: FSMContext):
    await _pause_lesson(message, state)


@router.message(LearningState.in_lesson, Command("menu"))
async def lesson_menu_command(message: Message, state: FSMContext):
    await _pause_lesson(message, state)


@router.message(
    LearningState.in_lesson,
    F.text.in_({"⏸ На паузу", "🚪 Завершить урок"}),
)
async def pause_button(message: Message, state: FSMContext):
    await _pause_lesson(message, state)


# ==========================
# Диалог с AI
# ==========================

@router.message(LearningState.in_lesson, F.text)
async def handle_lesson_message(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data or "lesson_id" not in data:
        await state.clear()
        await message.answer(
            "⚠️ Урок прервался. Вернись в меню и продолжи с того места где остановился.",
            reply_markup=main_menu_kb(),
        )
        return

    course_id     = data["course_id"]
    module_id     = data["module_id"]
    lesson_id     = data["lesson_id"]
    course_title  = data["course_title"]
    module_title  = data["module_title"]
    lesson_title  = data["lesson_title"]
    lesson_plan   = data.get("lesson_plan", "")
    lesson_terms  = data.get("lesson_terms", "")

    user_db_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )

    await save_message(user_db_id, course_id, module_id, lesson_id, "user", message.text)

    history = await get_conversation(user_db_id, course_id, module_id, lesson_id)
    history = history[:-1]

    thinking = await message.answer("✍️ Репетитор печатает...")
    student_history = await get_course_summaries(user_db_id, course_id)

    try:
        reply = await get_tutor_reply(
            course_title=course_title,
            module_title=module_title,
            lesson_title=lesson_title,
            history=history,
            user_message=message.text,
            lesson_plan=lesson_plan,
            lesson_terms=lesson_terms,
            student_history=student_history or None,
        )
    except Exception as e:
        log.error("Tutor reply error: %s", e)
        await thinking.delete()
        await message.answer("⚠️ Ошибка связи с репетитором. Попробуй ещё раз.")
        return

    await thinking.delete()

    cleaned, is_done = _strip_done_marker(reply)
    # В БД сохраняем уже очищенный вариант
    await save_message(user_db_id, course_id, module_id, lesson_id, "assistant", cleaned)

    if is_done:
        await message.answer(
            cleaned,
            reply_markup=complete_lesson_kb(course_id, module_id, lesson_id),
        )
    else:
        await message.answer(cleaned)


# ==========================
# Callback: завершить урок
# ==========================

@router.callback_query(F.data.startswith("complete:"))
async def cb_complete_lesson(callback: CallbackQuery, state: FSMContext):
    _, course_id, module_id, lesson_id = callback.data.split(":")
    # Сбросим состояние, если юзер ещё внутри урока
    current = await state.get_state()
    if current == LearningState.in_lesson.state:
        await state.clear()

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )

    # Убираем reply-клавиатуру урока, если она ещё висит
    await callback.message.answer("✅ Отлично!", reply_markup=main_menu_kb())

    await _complete_lesson(
        callback.message, user_db_id, course_id, module_id, lesson_id
    )
    await callback.answer()
