from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from content.courses import COURSES_BY_ID, CATEGORIES, get_courses_by_category


def courses_main_kb() -> InlineKeyboardMarkup:
    """Главный экран курсов: бесплатный курс + 3 категории."""
    free_course = COURSES_BY_ID["intro"]
    buttons = [
        [InlineKeyboardButton(
            text=f"{free_course['emoji']} {free_course['title']} — БЕСПЛАТНО",
            callback_data="course:intro",
        )],
    ]
    for cat in CATEGORIES:
        buttons.append([InlineKeyboardButton(
            text=f"{cat['emoji']} {cat['title']}",
            callback_data=f"category:{cat['id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_courses_kb(category_id: str) -> InlineKeyboardMarkup:
    """Список курсов внутри категории."""
    buttons = []
    for course in get_courses_by_category(category_id):
        buttons.append([InlineKeyboardButton(
            text=f"{course['emoji']} {course['title']}",
            callback_data=f"course:{course['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="courses")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_detail_kb(course_id: str, is_free: bool, category_id: str | None) -> InlineKeyboardMarkup:
    """Страница курса с кнопками действий."""
    buttons = []
    if is_free:
        buttons.append([InlineKeyboardButton(text="▶️ Начать курс", callback_data=f"start_course:{course_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🔒 Скоро будет доступно", callback_data="soon")])

    if category_id:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"category:{category_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="⬅️ К курсам", callback_data="courses")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_courses_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку курсов", callback_data="courses")],
    ])
