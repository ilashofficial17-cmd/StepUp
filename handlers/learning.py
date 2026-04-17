import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states.learning import LearningState
from ai.tutor import get_tutor_reply, generate_lesson_summary
from database.db import get_or_create_user, save_message, get_conversation, save_lesson_summary
from keyboards.reply import main_menu_kb

log = logging.getLogger(__name__)
router = Router()


@router.message(LearningState.in_lesson, F.text == "🚪 Завершить урок")
async def exit_lesson(message: Message, state: FSMContext):
    data = await state.get_data()
    course_id    = data["course_id"]
    module_id    = data["module_id"]
    lesson_id    = data["lesson_id"]
    lesson_title = data["lesson_title"]

    await state.clear()

    user_db_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )

    await message.answer("Урок завершён. Возвращаемся в главное меню 👇", reply_markup=main_menu_kb())

    # Генерируем резюме урока в фоне
    try:
        history = await get_conversation(user_db_id, course_id, module_id, lesson_id)
        if history:
            summary = await generate_lesson_summary(lesson_title, history)
            await save_lesson_summary(user_db_id, course_id, module_id, lesson_id, lesson_title, summary)
    except Exception as e:
        log.warning("Не удалось сохранить резюме урока: %s", e)


@router.message(LearningState.in_lesson, F.text)
async def handle_lesson_message(message: Message, state: FSMContext):
    data = await state.get_data()
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
    # убираем последнее сообщение пользователя из истории — оно уже передаётся отдельно
    history = history[:-1]

    thinking = await message.answer("✍️ Репетитор печатает...")

    try:
        reply = await get_tutor_reply(
            course_title=course_title,
            module_title=module_title,
            lesson_title=lesson_title,
            history=history,
            user_message=message.text,
            lesson_plan=lesson_plan,
            lesson_terms=lesson_terms,
        )
    except Exception as e:
        await thinking.delete()
        await message.answer("⚠️ Ошибка связи с репетитором. Попробуй ещё раз.")
        return

    await thinking.delete()
    await save_message(user_db_id, course_id, module_id, lesson_id, "assistant", reply)
    await message.answer(reply)
