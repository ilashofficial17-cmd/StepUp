from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from content.courses import COURSES_BY_ID, CATEGORIES_BY_BTN, CATEGORIES_BY_ID
from keyboards.inline import (
    category_courses_kb, course_detail_kb,
    modules_kb, lessons_kb, back_to_modules_kb,
)
from database.db import get_or_create_user, get_user_progress, start_course

router = Router()


# ==========================
# Reply-кнопки (нижняя клавиатура)
# ==========================

@router.message(F.text == "🆓 Первый шаг")
async def msg_intro(message: Message):
    course = COURSES_BY_ID["intro"]
    await message.answer(
        f"{course['emoji']} *{course['title']}*\n🆓 БЕСПЛАТНО\n\n{course['description']}",
        reply_markup=course_detail_kb("intro", True, None),
        parse_mode="Markdown",
    )


@router.message(F.text.in_({"📣 Продвижение", "💼 Бизнес", "🤖 Технологии"}))
async def msg_category(message: Message):
    category = CATEGORIES_BY_BTN.get(message.text)
    if not category:
        return
    await message.answer(
        f"{category['emoji']} *{category['title']}*\n\nВыбери курс:",
        reply_markup=category_courses_kb(category["id"]),
        parse_mode="Markdown",
    )


@router.message(F.text == "📊 Прогресс")
async def msg_progress(message: Message):
    user_db_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or "",
    )
    progress = await get_user_progress(user_db_id)

    if not progress:
        text = (
            "📊 *Мой прогресс*\n\n"
            "Ты ещё не начал ни одного курса.\n\n"
            "Начни с бесплатного *«Первый шаг»* 👇"
        )
    else:
        lines = ["📊 *Мой прогресс*\n"]
        for course_id, data in progress.items():
            course = COURSES_BY_ID.get(course_id)
            if course:
                status = "✅ Завершён" if data["completed"] else f"📖 Урок {data['lesson_id'] + 1}"
                lines.append(f"{course['emoji']} {course['title']}: {status}")
        text = "\n".join(lines)

    await message.answer(text, parse_mode="Markdown")


# ==========================
# Inline callbacks
# ==========================

@router.callback_query(F.data.startswith("course:"))
async def cb_course_detail(callback: CallbackQuery):
    course_id = callback.data.split(":")[1]
    course = COURSES_BY_ID.get(course_id)
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return

    tag = "🆓 БЕСПЛАТНО" if course["is_free"] else "🔒 Скоро"
    text = f"{course['emoji']} *{course['title']}*\n{tag}\n\n{course['description']}"

    await callback.message.edit_text(
        text,
        reply_markup=course_detail_kb(course_id, course["is_free"], course["category"]),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("modules:"))
async def cb_modules(callback: CallbackQuery):
    course_id = callback.data.split(":")[1]
    course = COURSES_BY_ID.get(course_id)
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    await start_course(user_db_id, course_id)

    await callback.message.edit_text(
        f"📋 *{course['title']}* — модули\n\nВыбери модуль для начала:",
        reply_markup=modules_kb(course_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("module:"))
async def cb_module(callback: CallbackQuery):
    _, course_id, module_id = callback.data.split(":")
    course = COURSES_BY_ID.get(course_id)
    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return
    module = next((m for m in course["modules"] if m["id"] == module_id), None)
    if not module:
        await callback.answer("Модуль не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"{module['emoji']} *{module['title']}*\n\nВыбери урок:",
        reply_markup=lessons_kb(course_id, module_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lesson:"))
async def cb_lesson(callback: CallbackQuery):
    _, course_id, module_id, lesson_id = callback.data.split(":")
    course = COURSES_BY_ID.get(course_id)
    module = next((m for m in course["modules"] if m["id"] == module_id), None)
    lesson = next((l for l in module["lessons"] if l["id"] == lesson_id), None)
    if not lesson:
        await callback.answer("Урок не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"📖 *{lesson['title']}*\n\n"
        "_Контент урока готовится. Скоро здесь появится материал с ИИ-репетитором!_",
        reply_markup=back_to_modules_kb(course_id, module_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz:"))
async def cb_quiz(callback: CallbackQuery):
    _, course_id, module_id = callback.data.split(":")
    module = next(
        (m for m in COURSES_BY_ID[course_id]["modules"] if m["id"] == module_id), None
    )
    await callback.message.edit_text(
        f"🧪 *Тест: {module['title']}*\n\n"
        "_Тесты появятся вместе с контентом уроков. Совсем скоро!_",
        reply_markup=back_to_modules_kb(course_id, module_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "soon")
async def cb_soon(callback: CallbackQuery):
    await callback.answer("Этот курс скоро будет доступен! 🔜", show_alert=True)
