from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from content.courses import get_courses_by_category, COURSES_BY_ID


def category_courses_kb(category_id: str) -> InlineKeyboardMarkup:
    """Список курсов в категории."""
    buttons = []
    for course in get_courses_by_category(category_id):
        buttons.append([InlineKeyboardButton(
            text=f"{course['emoji']} {course['title']}",
            callback_data=f"course:{course['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_detail_kb(course_id: str, is_free: bool, category_id: str | None) -> InlineKeyboardMarkup:
    """Страница курса."""
    buttons = []
    if is_free:
        buttons.append([InlineKeyboardButton(text="▶️ Начать курс", callback_data=f"modules:{course_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🔒 Скоро будет доступно", callback_data="soon")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def modules_kb(course_id: str) -> InlineKeyboardMarkup:
    """Список модулей курса."""
    course = COURSES_BY_ID.get(course_id)
    buttons = []
    for module in course.get("modules", []):
        lessons_count = len(module["lessons"])
        quiz = " + тест" if module["has_quiz"] else ""
        buttons.append([InlineKeyboardButton(
            text=f"{module['emoji']} {module['title']} ({lessons_count} ур.{quiz})",
            callback_data=f"module:{course_id}:{module['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def lessons_kb(course_id: str, module_id: str) -> InlineKeyboardMarkup:
    """Список уроков модуля."""
    course = COURSES_BY_ID.get(course_id)
    module = next((m for m in course["modules"] if m["id"] == module_id), None)
    buttons = []
    for lesson in module["lessons"]:
        buttons.append([InlineKeyboardButton(
            text=f"📖 {lesson['title']}",
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


def back_to_modules_kb(course_id: str, module_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К урокам", callback_data=f"module:{course_id}:{module_id}")],
        [InlineKeyboardButton(text="📋 К модулям", callback_data=f"modules:{course_id}")],
    ])
