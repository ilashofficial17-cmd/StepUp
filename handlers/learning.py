import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ai.tutor import (
    generate_lesson_summary,
    generate_student_conspect,
    get_tutor_reply,
    strip_done_marker,
    strip_phase_marker,
)
from content.courses import (
    get_lesson,
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
    get_user_profile,
    mark_course_completed,
    save_lesson_summary,
    save_message,
    save_student_conspect,
)
from keyboards.inline import (
    after_lesson_kb,
    complete_lesson_kb,
    course_completed_kb,
)
from keyboards.reply import QUICK_REPLIES, main_menu_kb
from states.learning import LearningState

log = logging.getLogger(__name__)
router = Router()


# ==========================
# Вспомогательные функции
# ==========================

def _format_phase_header(phase: tuple[int, int] | None) -> str:
    if not phase:
        return ""
    current, total = phase
    return f"📍 Фаза {current} из {total}\n\n"


async def _generate_and_save_internal_summary(user_db_id: int, data: dict) -> None:
    """Фоновая генерация структурированного резюме для памяти тьютора.
    Конспект-для-студента генерируется синхронно при завершении."""
    course_id    = data["course_id"]
    module_id    = data["module_id"]
    lesson_id    = data["lesson_id"]
    lesson_title = data["lesson_title"]
    try:
        history = await get_conversation(user_db_id, course_id, module_id, lesson_id)
        if not history:
            return
        summary = await generate_lesson_summary(lesson_title, history)
        # student_conspect уже сохранён — передаём None чтобы не перетереть
        await save_lesson_summary(
            user_db_id, course_id, module_id, lesson_id, lesson_title, summary,
        )
        completed = await get_completed_lesson_keys(user_db_id, course_id)
        if len(completed) >= total_lessons_in_course(course_id):
            await mark_course_completed(user_db_id, course_id)
    except Exception as e:
        log.warning("Не удалось сохранить внутреннее резюме: %s", e)


async def _pause_lesson(message: Message, state: FSMContext) -> None:
    """Выход без отметки о завершении — прогресс last_lesson остаётся."""
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
    """Завершает урок: генерирует конспект и показывает его студенту,
    ставит отметку о прохождении, предлагает следующие шаги."""
    lesson = get_lesson(course_id, module_id, lesson_id)
    lesson_title = lesson["title"] if lesson else lesson_id

    # Сначала — минимальная отметка чтобы урок сразу попал в completed
    await save_lesson_summary(
        user_db_id, course_id, module_id, lesson_id, lesson_title,
        f"Урок «{lesson_title}» пройден.",
    )

    # Собираем конспект — это UX-критический шаг, ждём
    thinking = await message.answer("🧩 Собираю твой конспект...")
    try:
        history = await get_conversation(user_db_id, course_id, module_id, lesson_id)
        conspect = await generate_student_conspect(lesson_title, history)
    except Exception as e:
        log.warning("Не удалось сгенерировать конспект: %s", e)
        conspect = (
            f"🎯 Главное за 3 тезиса\n"
            f"• Урок «{lesson_title}» пройден.\n"
            f"• Подробный конспект не удалось собрать.\n"
            f"• Загляни в «📝 Конспекты» позже — или пройди урок заново."
        )
    await save_student_conspect(user_db_id, course_id, module_id, lesson_id, conspect)
    try:
        await thinking.delete()
    except Exception:
        pass

    await message.answer(
        f"📝 *Конспект урока*\n\n{conspect}",
        parse_mode="Markdown",
    )

    # Проверяем — курс пройден полностью?
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
            "Что дальше? 👇",
            reply_markup=after_lesson_kb(course_id, module_id, next_lesson, show_quiz),
        )

    # Внутреннее резюме (для памяти тьютора) — в фоне
    bg_data = {
        "course_id": course_id,
        "module_id": module_id,
        "lesson_id": lesson_id,
        "lesson_title": lesson_title,
    }
    asyncio.create_task(_generate_and_save_internal_summary(user_db_id, bg_data))


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
    ai_model      = data.get("ai_model")

    # Быстрые ответы — подставляем полноценную реплику для AI,
    # сохраняем её же в истории, чтобы AI видел чёткий запрос.
    user_text = QUICK_REPLIES.get(message.text, message.text)

    user_db_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )

    await save_message(user_db_id, course_id, module_id, lesson_id, "user", user_text)

    history = await get_conversation(user_db_id, course_id, module_id, lesson_id)
    history = history[:-1]

    thinking = await message.answer("✍️ Репетитор печатает...")
    student_history = await get_course_summaries(user_db_id, course_id)
    student_profile = await get_user_profile(user_db_id)

    try:
        reply = await get_tutor_reply(
            course_title=course_title,
            module_title=module_title,
            lesson_title=lesson_title,
            history=history,
            user_message=user_text,
            lesson_plan=lesson_plan,
            lesson_terms=lesson_terms,
            student_history=student_history or None,
            student_profile=student_profile,
            model=ai_model,
        )
    except Exception as e:
        log.error("Tutor reply error: %s", e)
        try:
            await thinking.delete()
        except Exception:
            pass
        await message.answer("⚠️ Ошибка связи с репетитором. Попробуй ещё раз.")
        return

    try:
        await thinking.delete()
    except Exception:
        pass

    # Снимаем служебные маркеры — по порядку: сначала фаза, потом финал
    cleaned, phase = strip_phase_marker(reply)
    cleaned, is_done = strip_done_marker(cleaned)

    # В БД сохраняем уже очищенный текст — без маркеров
    await save_message(user_db_id, course_id, module_id, lesson_id, "assistant", cleaned)

    display = _format_phase_header(phase) + cleaned

    if is_done:
        await message.answer(
            display,
            reply_markup=complete_lesson_kb(course_id, module_id, lesson_id),
        )
    else:
        await message.answer(display)


# ==========================
# Callback: завершить урок
# ==========================

from aiogram.types import CallbackQuery  # noqa: E402


@router.callback_query(F.data.startswith("complete:"))
async def cb_complete_lesson(callback: CallbackQuery, state: FSMContext):
    _, course_id, module_id, lesson_id = callback.data.split(":")
    current = await state.get_state()
    if current == LearningState.in_lesson.state:
        await state.clear()

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )

    # Снимаем reply-клавиатуру урока
    await callback.message.answer("✅ Отлично!", reply_markup=main_menu_kb())
    await callback.answer()

    await _complete_lesson(
        callback.message, user_db_id, course_id, module_id, lesson_id
    )
