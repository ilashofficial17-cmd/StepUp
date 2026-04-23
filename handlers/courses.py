import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ai.tutor import start_lesson
from content.courses import (
    CATEGORIES_BY_BTN,
    COURSES_BY_ID,
    QUIZ_PASS_THRESHOLD,
    get_lesson,
    get_module,
    get_quiz_questions,
    total_lessons_in_course,
)
from database.db import (
    get_completed_lesson_keys,
    get_course_summaries,
    get_last_lesson,
    get_or_create_user,
    get_passed_modules,
    get_quiz_result,
    get_quiz_score,
    get_student_conspect,
    get_user_profile,
    get_user_progress,
    grant_course_access,
    has_course_access,
    is_profile_complete,
    list_user_conspects,
    reset_quiz,
    save_message,
    save_quiz_answer,
    save_quiz_result,
    start_course,
    update_lesson_progress,
)
from handlers import onboarding
from keyboards.inline import (
    back_to_modules_kb,
    category_courses_kb,
    conspect_view_kb,
    conspects_list_kb,
    course_detail_kb,
    lesson_info_kb,
    lessons_kb,
    modules_kb,
    quiz_next_kb,
    quiz_question_kb,
    quiz_result_kb,
)
from keyboards.reply import lesson_kb
from states.learning import LearningState

log = logging.getLogger(__name__)
router = Router()


# ==========================
# Reply-кнопки
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
        await message.answer(text, parse_mode="Markdown")
        return

    lines = ["📊 *Мой прогресс*\n"]
    for course_id, data in progress.items():
        course = COURSES_BY_ID.get(course_id)
        if not course:
            continue
        total = total_lessons_in_course(course_id)
        completed = await get_completed_lesson_keys(user_db_id, course_id)
        passed = await get_passed_modules(user_db_id, course_id)
        done_count = len(completed)

        header = f"{course['emoji']} *{course['title']}*"
        if data["completed"] or (total > 0 and done_count >= total):
            status = f"  ✅ Завершён ({done_count}/{total} уроков)"
        else:
            status = f"  📖 Пройдено {done_count}/{total} уроков"
        lines.append(f"{header}\n{status}")

        quiz_modules = [m for m in course["modules"] if m.get("has_quiz")]
        if quiz_modules:
            passed_count = sum(1 for m in quiz_modules if m["id"] in passed)
            lines.append(f"  🧪 Тесты: {passed_count}/{len(quiz_modules)} пройдено")

    await message.answer("\n\n".join(lines), parse_mode="Markdown")


# ==========================
# Inline: навигация по курсу
# ==========================

@router.callback_query(F.data.startswith("course:"))
async def cb_course_detail(callback: CallbackQuery):
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

    is_free = course["is_free"]
    has_modules = bool(course.get("modules"))
    access = False
    if not is_free and has_modules:
        access = await has_course_access(user_db_id, course_id)

    if is_free:
        tag = "🆓 БЕСПЛАТНО"
    elif access:
        tag = "✅ У тебя есть доступ"
    elif not has_modules:
        tag = "🔒 Скоро"
    else:
        tag = f"💳 ${course.get('price_usd', 0)} — доступ навсегда"

    text = f"{course['emoji']} *{course['title']}*\n{tag}\n\n{course['description']}"
    await callback.message.edit_text(
        text,
        reply_markup=course_detail_kb(
            course_id,
            is_free,
            course["category"],
            has_access=access,
            price_usd=course.get("price_usd"),
            has_modules=has_modules,
        ),
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
    last_lesson = await get_last_lesson(user_db_id, course_id)
    completed = await get_completed_lesson_keys(user_db_id, course_id)
    passed = await get_passed_modules(user_db_id, course_id)

    total = total_lessons_in_course(course_id)
    progress_line = f"Пройдено: {len(completed)}/{total} уроков" if total else ""

    text = f"📋 *{course['title']}*"
    if progress_line:
        text += f"\n_{progress_line}_"
    text += "\n\nВыбери модуль:" if not last_lesson else "\n\nПродолжи с места где остановился 👇"

    await callback.message.edit_text(
        text,
        reply_markup=modules_kb(course_id, last_lesson, completed, passed),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("module:"))
async def cb_module(callback: CallbackQuery):
    _, course_id, module_id = callback.data.split(":")
    module = get_module(course_id, module_id)
    if not module:
        await callback.answer("Модуль не найден", show_alert=True)
        return
    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    completed = await get_completed_lesson_keys(user_db_id, course_id)
    quiz_res = await get_quiz_result(user_db_id, course_id, module_id)
    quiz_passed = bool(quiz_res and quiz_res["passed"])

    await callback.message.edit_text(
        f"{module['emoji']} *{module['title']}*\n\nВыбери урок:",
        reply_markup=lessons_kb(course_id, module_id, completed, quiz_passed),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lesson:"))
async def cb_lesson(callback: CallbackQuery):
    _, course_id, module_id, lesson_id = callback.data.split(":")
    lesson = get_lesson(course_id, module_id, lesson_id)
    if not lesson:
        await callback.answer("Урок не найден", show_alert=True)
        return

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    completed = await get_completed_lesson_keys(user_db_id, course_id)
    is_done = (module_id, lesson_id) in completed
    status = "✅ Урок пройден\n\n" if is_done else ""

    text = (
        f"📖 *{lesson['title']}*\n\n"
        f"{status}{lesson['description']}\n\n"
        f"✅ *Что получишь:*\n{lesson['outcome']}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=lesson_info_kb(course_id, module_id, lesson_id, is_done),
        parse_mode="Markdown",
    )
    await callback.answer()


async def launch_lesson(
    message,  # aiogram Message (.answer доступен)
    state: FSMContext,
    user_db_id: int,
    course_id: str,
    module_id: str,
    lesson_id: str,
) -> None:
    """Ставит FSM-стейт, зовёт AI, отправляет приветственное сообщение."""
    course = COURSES_BY_ID.get(course_id)
    module = get_module(course_id, module_id)
    lesson = get_lesson(course_id, module_id, lesson_id)
    if not (course and module and lesson):
        await message.answer("⚠️ Урок не найден")
        return

    # Access-check для платных курсов
    if not course["is_free"] and not await has_course_access(user_db_id, course_id):
        await message.answer(
            f"🔒 Этот курс доступен после покупки.\n\n"
            f"Стоимость: ${course.get('price_usd', 35)} — доступ навсегда.\n\n"
            f"Нажми на курс в каталоге чтобы оплатить.",
        )
        return

    await state.set_state(LearningState.in_lesson)
    await state.update_data(
        course_id=course_id,
        module_id=module_id,
        lesson_id=lesson_id,
        course_title=course["title"],
        module_title=module["title"],
        lesson_title=lesson["title"],
        lesson_plan=lesson.get("plan", ""),
        lesson_terms=lesson.get("terms", ""),
        ai_model=course.get("ai_model"),
    )

    await message.answer(
        f"📖 *{lesson['title']}*\n\nРепетитор настраивается под тебя...",
        reply_markup=lesson_kb(),
        parse_mode="Markdown",
    )
    await update_lesson_progress(user_db_id, course_id, module_id, lesson_id)

    try:
        from ai.tutor import strip_done_marker, strip_phase_marker
        student_history = await get_course_summaries(user_db_id, course_id)
        student_profile = await get_user_profile(user_db_id)
        intro = await start_lesson(
            course_title=course["title"],
            module_title=module["title"],
            lesson_title=lesson["title"],
            lesson_plan=lesson.get("plan", ""),
            lesson_terms=lesson.get("terms", ""),
            student_history=student_history or None,
            student_profile=student_profile,
            model=course.get("ai_model"),
        )
        cleaned, phase = strip_phase_marker(intro)
        cleaned, _ = strip_done_marker(cleaned)
        await save_message(user_db_id, course_id, module_id, lesson_id, "assistant", cleaned)
        header = f"📍 Фаза {phase[0]} из {phase[1]}\n\n" if phase else ""
        await message.answer(header + cleaned)
    except Exception as e:
        log.error("Tutor start_lesson error: %s", e)
        await message.answer(
            "⚠️ Не удалось подключиться к репетитору. Проверь OPENROUTER_API_KEY в настройках."
        )


@router.callback_query(F.data.startswith("begin:"))
async def cb_begin_lesson(callback: CallbackQuery, state: FSMContext):
    _, course_id, module_id, lesson_id = callback.data.split(":")
    if not get_lesson(course_id, module_id, lesson_id):
        await callback.answer("Урок не найден", show_alert=True)
        return

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )

    await callback.answer()

    # Первый урок — сначала короткая диагностика
    if not await is_profile_complete(user_db_id):
        await onboarding.start_onboarding(
            callback.message, state, course_id, module_id, lesson_id
        )
        return

    await launch_lesson(callback.message, state, user_db_id, course_id, module_id, lesson_id)


# ==========================
# Квизы
# ==========================

def _render_question(course_id: str, module_id: str, q_idx: int, q: dict) -> tuple[str, object]:
    total = len(get_quiz_questions(course_id, module_id))
    text = (
        f"🧪 *Вопрос {q_idx + 1}/{total}*\n\n"
        f"{q['q']}"
    )
    return text, quiz_question_kb(course_id, module_id, q_idx, q["options"])


@router.callback_query(F.data.startswith("quiz:"))
async def cb_quiz_start(callback: CallbackQuery):
    _, course_id, module_id = callback.data.split(":")
    questions = get_quiz_questions(course_id, module_id)
    module = get_module(course_id, module_id)

    if not questions or not module:
        await callback.message.edit_text(
            "🧪 Тест пока недоступен.",
            reply_markup=back_to_modules_kb(course_id, module_id),
        )
        await callback.answer()
        return

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    await reset_quiz(user_db_id, course_id, module_id)

    text, kb = _render_question(course_id, module_id, 0, questions[0])
    intro = (
        f"🧪 *Тест: {module['title']}*\n"
        f"_Ответь правильно на {QUIZ_PASS_THRESHOLD} из {len(questions)}, чтобы пройти._\n\n"
    )
    await callback.message.edit_text(intro + text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("qa:"))
async def cb_quiz_answer(callback: CallbackQuery):
    _, course_id, module_id, q_idx_s, chosen_s = callback.data.split(":")
    q_idx = int(q_idx_s)
    chosen = int(chosen_s)
    questions = get_quiz_questions(course_id, module_id)
    if q_idx >= len(questions):
        await callback.answer("Вопрос не найден", show_alert=True)
        return

    q = questions[q_idx]
    is_correct = chosen == q["correct"]

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    await save_quiz_answer(user_db_id, course_id, module_id, q_idx, chosen, is_correct)

    if is_correct:
        feedback = f"✅ *Верно!*\n\n{q['options'][q['correct']]}"
    else:
        feedback = (
            f"❌ *Неверно.*\n\n"
            f"Правильный ответ: *{q['options'][q['correct']]}*"
        )

    is_last = q_idx + 1 >= len(questions)
    next_idx = q_idx + 1
    await callback.message.edit_text(
        feedback,
        reply_markup=quiz_next_kb(course_id, module_id, next_idx, is_last),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("qn:"))
async def cb_quiz_next(callback: CallbackQuery):
    _, course_id, module_id, q_idx_s = callback.data.split(":")
    q_idx = int(q_idx_s)
    questions = get_quiz_questions(course_id, module_id)
    if q_idx >= len(questions):
        await callback.answer()
        return

    text, kb = _render_question(course_id, module_id, q_idx, questions[q_idx])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("qr:"))
async def cb_quiz_result(callback: CallbackQuery):
    _, course_id, module_id, _ = callback.data.split(":")
    questions = get_quiz_questions(course_id, module_id)
    total = len(questions)
    module = get_module(course_id, module_id)

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    score = await get_quiz_score(user_db_id, course_id, module_id)
    passed = score >= QUIZ_PASS_THRESHOLD
    await save_quiz_result(user_db_id, course_id, module_id, score, total, passed)

    if passed:
        text = (
            f"🎉 *Тест пройден: {score}/{total}*\n\n"
            f"Модуль «{module['title']}» закрыт ✅"
        )
    else:
        text = (
            f"😕 *Результат: {score}/{total}*\n\n"
            f"Нужно минимум {QUIZ_PASS_THRESHOLD} из {total}. "
            f"Пересмотри уроки модуля и попробуй ещё раз."
        )

    await callback.message.edit_text(
        text,
        reply_markup=quiz_result_kb(course_id, module_id, passed),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "soon")
async def cb_soon(callback: CallbackQuery):
    await callback.answer("Этот курс скоро будет доступен! 🔜", show_alert=True)


# ==========================
# Покупка курса
# ==========================

@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_course(callback: CallbackQuery):
    from payments.stripe_client import create_checkout_url, is_stripe_configured

    course_id = callback.data.split(":")[1]
    course = COURSES_BY_ID.get(course_id)
    if not course or course["is_free"]:
        await callback.answer("Курс недоступен", show_alert=True)
        return

    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )

    if await has_course_access(user_db_id, course_id):
        await callback.answer("У тебя уже есть доступ к этому курсу ✅", show_alert=True)
        return

    price = course.get("price_usd", 0)

    if not is_stripe_configured():
        # Stripe пока не настроен — даём инструкцию
        await callback.message.answer(
            f"💳 *Покупка курса «{course['title']}»*\n\n"
            f"Цена: ${price}\n\n"
            "Оплата временно недоступна в боте — напиши в поддержку, "
            "мы пришлём ссылку и выдадим доступ вручную.",
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    url = await create_checkout_url(
        course_id=course_id,
        course_title=course["title"],
        price_usd=price,
        telegram_id=callback.from_user.id,
        user_db_id=user_db_id,
    )
    if not url:
        await callback.message.answer(
            "⚠️ Не удалось создать ссылку на оплату. Попробуй позже."
        )
        await callback.answer()
        return

    await callback.message.answer(
        f"💳 *«{course['title']}» — ${price}*\n\n"
        "Нажми на ссылку ниже, оплати картой. Доступ откроется автоматически через несколько секунд после оплаты.\n\n"
        f"🔗 {url}\n\n"
        "После оплаты вернись в бот и зайди в раздел курса — кнопка «Начать» будет активна.",
        parse_mode="Markdown",
        disable_web_page_preview=False,
    )
    await callback.answer()


# ==========================
# Конспекты пройденных уроков
# ==========================

async def _render_conspects_list(message_or_cb, edit: bool = False):
    user_db_id = await get_or_create_user(
        telegram_id=message_or_cb.from_user.id,
        username=message_or_cb.from_user.username or "",
        full_name=message_or_cb.from_user.full_name or "",
    )
    items = await list_user_conspects(user_db_id)
    if not items:
        text = (
            "📝 *Мои конспекты*\n\n"
            "Пока что тут пусто. Заверши хотя бы один урок — и конспект появится здесь."
        )
        if edit:
            await message_or_cb.message.edit_text(text, parse_mode="Markdown")
        else:
            await message_or_cb.answer(text, parse_mode="Markdown")
        return

    text = (
        "📝 *Мои конспекты*\n\n"
        "Короткая выжимка из каждого урока — чтобы вспомнить главное. Выбери урок:"
    )
    kb = conspects_list_kb(items)
    if edit:
        await message_or_cb.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message_or_cb.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.message(F.text == "📝 Конспекты")
async def msg_conspects(message: Message):
    await _render_conspects_list(message, edit=False)


@router.callback_query(F.data == "csp_list")
async def cb_conspects_list(callback: CallbackQuery):
    await _render_conspects_list(callback, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("csp:"))
async def cb_conspect_view(callback: CallbackQuery):
    _, course_id, module_id, lesson_id = callback.data.split(":")
    user_db_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name or "",
    )
    lesson = get_lesson(course_id, module_id, lesson_id)
    title = lesson["title"] if lesson else lesson_id
    conspect = await get_student_conspect(user_db_id, course_id, module_id, lesson_id)

    if not conspect:
        text = (
            f"📝 *{title}*\n\n"
            "Для этого урока пока нет конспекта — возможно, он был завершён без "
            "диалога. Можешь пройти урок заново — конспект сгенерируется."
        )
    else:
        text = f"📝 *{title}*\n\n{conspect}"

    await callback.message.edit_text(
        text,
        reply_markup=conspect_view_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()
