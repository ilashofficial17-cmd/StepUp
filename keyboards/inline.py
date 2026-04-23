from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from content.courses import get_courses_by_category, COURSES_BY_ID


def category_courses_kb(category_id: str) -> InlineKeyboardMarkup:
    buttons = []
    for course in get_courses_by_category(category_id):
        buttons.append([InlineKeyboardButton(
            text=f"{course['emoji']} {course['title']}",
            callback_data=f"course:{course['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_detail_kb(
    course_id: str,
    is_free: bool,
    category_id: str | None,
    has_access: bool = False,
    price_usd: int | None = None,
    has_modules: bool = True,
) -> InlineKeyboardMarkup:
    buttons = []
    # Бесплатный курс ИЛИ платный на который есть доступ — показываем «Начать»
    if (is_free or has_access) and has_modules:
        buttons.append([InlineKeyboardButton(
            text="▶️ Начать курс", callback_data=f"modules:{course_id}"
        )])
    # Платный без доступа — кнопка покупки
    elif not is_free and price_usd and has_modules:
        buttons.append([InlineKeyboardButton(
            text=f"💳 Купить за ${price_usd}",
            callback_data=f"buy:{course_id}",
        )])
    # Заглушка «скоро» — если контента ещё нет
    else:
        buttons.append([InlineKeyboardButton(text="🔒 Скоро будет доступно", callback_data="soon")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def modules_kb(
    course_id: str,
    last_lesson: dict | None = None,
    completed_keys: set | None = None,
    passed_modules: set | None = None,
) -> InlineKeyboardMarkup:
    course = COURSES_BY_ID.get(course_id)
    completed_keys = completed_keys or set()
    passed_modules = passed_modules or set()
    buttons = []

    if last_lesson:
        module_id = last_lesson["module_id"]
        lesson_id = last_lesson["lesson_id"]
        module = next((m for m in course["modules"] if m["id"] == module_id), None)
        lesson = next((l for l in module["lessons"] if l["id"] == lesson_id), None) if module else None
        if lesson:
            buttons.append([InlineKeyboardButton(
                text=f"▶️ Продолжить: {lesson['title']}",
                callback_data=f"lesson:{course_id}:{module_id}:{lesson_id}",
            )])

    for module in course.get("modules", []):
        lessons = module["lessons"]
        done = sum(1 for l in lessons if (module["id"], l["id"]) in completed_keys)
        total = len(lessons)
        quiz_badge = ""
        if module.get("has_quiz"):
            quiz_badge = " ✅" if module["id"] in passed_modules else " 🧪"
        lessons_badge = f"{done}/{total}" if done else f"{total} ур."
        buttons.append([InlineKeyboardButton(
            text=f"{module['emoji']} {module['title']} ({lessons_badge}){quiz_badge}",
            callback_data=f"module:{course_id}:{module['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lessons_kb(
    course_id: str,
    module_id: str,
    completed_keys: set | None = None,
    quiz_passed: bool = False,
) -> InlineKeyboardMarkup:
    course = COURSES_BY_ID.get(course_id)
    module = next((m for m in course["modules"] if m["id"] == module_id), None)
    completed_keys = completed_keys or set()
    buttons = []
    for i, lesson in enumerate(module["lessons"], 1):
        mark = "✅" if (module_id, lesson["id"]) in completed_keys else f"{i}."
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {lesson['title']}",
            callback_data=f"lesson:{course_id}:{module_id}:{lesson['id']}",
        )])
    if module.get("has_quiz"):
        quiz_text = "✅ Тест пройден" if quiz_passed else "🧪 Тест по модулю"
        buttons.append([InlineKeyboardButton(
            text=quiz_text,
            callback_data=f"quiz:{course_id}:{module_id}",
        )])
    buttons.append([InlineKeyboardButton(
        text="⬅️ К модулям",
        callback_data=f"modules:{course_id}",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lesson_info_kb(
    course_id: str,
    module_id: str,
    lesson_id: str,
    is_completed: bool = False,
) -> InlineKeyboardMarkup:
    start_text = "🔁 Пройти заново" if is_completed else "▶️ Начать урок"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=start_text,
            callback_data=f"begin:{course_id}:{module_id}:{lesson_id}",
        )],
        [InlineKeyboardButton(
            text="⬅️ К урокам",
            callback_data=f"module:{course_id}:{module_id}",
        )],
    ])


ONBOARDING_EXP = [
    ("🌱 Совсем новичок", "new"),
    ("📚 Что-то читал, пробовал", "beginner"),
    ("💼 Работаю в близкой сфере", "related"),
    ("🚀 Уже в digital / маркетинге", "pro"),
]

ONBOARDING_GOAL = [
    ("💰 Подработка / фриланс", "freelance"),
    ("🔄 Сменить профессию", "career"),
    ("🏢 Для своего бизнеса", "business"),
    ("🧭 Просто развиваюсь", "curious"),
]


def onboarding_experience_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"ob_exp:{code}")]
        for label, code in ONBOARDING_EXP
    ])


def onboarding_goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"ob_goal:{code}")]
        for label, code in ONBOARDING_GOAL
    ])


def onboarding_skip_context_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустить и начать урок", callback_data="ob_skip_ctx")],
    ])


def complete_lesson_kb(course_id: str, module_id: str, lesson_id: str) -> InlineKeyboardMarkup:
    """Инлайн-кнопка которая появляется когда AI сигналит об окончании урока."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Завершить урок",
            callback_data=f"complete:{course_id}:{module_id}:{lesson_id}",
        )],
    ])


def continue_course_kb(course_id: str, module_id: str, lesson_id: str, title: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"▶️ Продолжить: {title}",
            callback_data=f"lesson:{course_id}:{module_id}:{lesson_id}",
        )],
    ])


def after_lesson_kb(
    course_id: str,
    module_id: str,
    next_lesson: dict | None,
    show_quiz: bool,
) -> InlineKeyboardMarkup:
    """Клавиатура после завершения урока."""
    buttons = []
    if show_quiz:
        buttons.append([InlineKeyboardButton(
            text="🧪 Пройти тест по модулю",
            callback_data=f"quiz:{course_id}:{module_id}",
        )])
    if next_lesson:
        prefix = "▶️ Следующий модуль" if next_lesson["is_first_of_next_module"] else "▶️ Следующий урок"
        buttons.append([InlineKeyboardButton(
            text=f"{prefix}: {next_lesson['title']}",
            callback_data=f"lesson:{course_id}:{next_lesson['module_id']}:{next_lesson['lesson_id']}",
        )])
    buttons.append([InlineKeyboardButton(
        text="📋 К модулям",
        callback_data=f"modules:{course_id}",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_completed_kb(course_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 К модулям курса", callback_data=f"modules:{course_id}")],
    ])


def quiz_question_kb(
    course_id: str, module_id: str, q_idx: int, options: list[str],
) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{chr(ord('A') + i)}. {opt}",
            callback_data=f"qa:{course_id}:{module_id}:{q_idx}:{i}",
        )]
        for i, opt in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quiz_next_kb(
    course_id: str, module_id: str, next_idx: int, is_last: bool,
) -> InlineKeyboardMarkup:
    action = "qr" if is_last else "qn"
    text = "📊 Посмотреть результат" if is_last else "➡️ Следующий вопрос"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=text,
            callback_data=f"{action}:{course_id}:{module_id}:{next_idx}",
        )],
    ])


def quiz_result_kb(course_id: str, module_id: str, passed: bool) -> InlineKeyboardMarkup:
    buttons = []
    if not passed:
        buttons.append([InlineKeyboardButton(
            text="🔁 Пройти тест заново",
            callback_data=f"quiz:{course_id}:{module_id}",
        )])
    buttons.append([InlineKeyboardButton(
        text="⬅️ К урокам модуля",
        callback_data=f"module:{course_id}:{module_id}",
    )])
    buttons.append([InlineKeyboardButton(
        text="📋 К модулям",
        callback_data=f"modules:{course_id}",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def conspects_list_kb(items: list[dict]) -> InlineKeyboardMarkup:
    """items: [{'course_id', 'module_id', 'lesson_id', 'lesson_title', 'has_conspect'}]"""
    buttons = []
    for item in items:
        mark = "📝" if item.get("has_conspect") else "📄"
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {item['lesson_title']}",
            callback_data=f"csp:{item['course_id']}:{item['module_id']}:{item['lesson_id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def conspect_view_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку конспектов", callback_data="csp_list")],
    ])


def back_to_modules_kb(course_id: str, module_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К урокам", callback_data=f"module:{course_id}:{module_id}")],
        [InlineKeyboardButton(text="📋 К модулям", callback_data=f"modules:{course_id}")],
    ])
