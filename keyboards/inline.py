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


def course_detail_kb(course_id: str, is_free: bool, category_id: str | None) -> InlineKeyboardMarkup:
    buttons = []
    if is_free:
        buttons.append([InlineKeyboardButton(text="▶️ Начать курс", callback_data=f"modules:{course_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🔒 Скоро будет доступно", callback_data="soon")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def modules_kb(course_id: str, last_lesson: dict | None = None) -> InlineKeyboardMarkup:
    course = COURSES_BY_ID.get(course_id)
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
        lessons_count = len(module["lessons"])
        quiz = " + тест" if module["has_quiz"] else ""
        buttons.append([InlineKeyboardButton(
            text=f"{module['emoji']} {module['title']} ({lessons_count} ур.{quiz})",
            callback_data=f"module:{course_id}:{module['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lessons_kb(course_id: str, module_id: str) -> InlineKeyboardMarkup:
    course = COURSES_BY_ID.get(course_id)
    module = next((m for m in course["modules"] if m["id"] == module_id), None)
    buttons = []
    for i, lesson in enumerate(module["lessons"], 1):
        buttons.append([InlineKeyboardButton(
            text=f"{i}. {lesson['title']}",
            callback_data=f"lesson:{course_id}:{module_id}:{lesson['id']}",
        )])
    if module["has_quiz"]:
        buttons.append([InlineKeyboardButton(
            text="🧪 Тест по модулю",
            callback_data=f"quiz:{course_id}:{module_id}",
        )])
    buttons.append([InlineKeyboardButton(
        text="⬅️ К модулям",
        callback_data=f"modules:{course_id}",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lesson_info_kb(course_id: str, module_id: str, lesson_id: str) -> InlineKeyboardMarkup:
    """Страница урока с описанием — кнопка запуска и назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Начать урок",
            callback_data=f"begin:{course_id}:{module_id}:{lesson_id}",
        )],
        [InlineKeyboardButton(
            text="⬅️ К урокам",
            callback_data=f"module:{course_id}:{module_id}",
        )],
    ])


def back_to_modules_kb(course_id: str, module_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К урокам", callback_data=f"module:{course_id}:{module_id}")],
        [InlineKeyboardButton(text="📋 К модулям", callback_data=f"modules:{course_id}")],
    ])
