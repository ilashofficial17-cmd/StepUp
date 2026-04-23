import logging
import re

import aiohttp

from ai.prompts import (
    get_lesson_system_prompt,
    get_student_conspect_prompt,
    get_summary_prompt,
)
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

log = logging.getLogger(__name__)

DONE_MARKER = "[LESSON_DONE]"
PHASE_RE = re.compile(r"\[PHASE:\s*(\d+)\s*/\s*(\d+)\s*\]")


def strip_done_marker(text: str) -> tuple[str, bool]:
    """Вытаскивает служебный маркер окончания урока.
    Возвращает (очищенный_текст, done_flag)."""
    if DONE_MARKER in text:
        return text.replace(DONE_MARKER, "").rstrip(), True
    return text, False


def strip_phase_marker(text: str) -> tuple[str, tuple[int, int] | None]:
    """Вытаскивает служебный маркер фазы [PHASE:X/N].
    Возвращает (очищенный_текст, (X, N) | None)."""
    match = PHASE_RE.search(text)
    if not match:
        return text, None
    current, total = int(match.group(1)), int(match.group(2))
    cleaned = PHASE_RE.sub("", text, count=1).lstrip("\n").lstrip()
    return cleaned, (current, total)

HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://stepup-bot.railway.app",
    "X-Title": "StepUp",
}


async def _call(messages: list, model: str | None = None) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY не задан в переменных окружения")

    headers = {**HEADERS, "Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": model or OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.7,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"OpenRouter вернул {resp.status}: {text}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]


async def start_lesson(
    course_title: str,
    module_title: str,
    lesson_title: str,
    lesson_plan: str = "",
    lesson_terms: str = "",
    student_history: list[dict] | None = None,
    student_profile: dict | None = None,
    model: str | None = None,
) -> str:
    system_prompt = get_lesson_system_prompt(
        course_title, module_title, lesson_title,
        lesson_plan, lesson_terms,
        student_history=student_history,
        student_profile=student_profile,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": "Начинаем урок!"},
    ]
    return await _call(messages, model=model)


async def get_tutor_reply(
    course_title: str,
    module_title: str,
    lesson_title: str,
    history: list[dict],
    user_message: str,
    lesson_plan: str = "",
    lesson_terms: str = "",
    student_history: list[dict] | None = None,
    student_profile: dict | None = None,
    model: str | None = None,
) -> str:
    system_prompt = get_lesson_system_prompt(
        course_title, module_title, lesson_title,
        lesson_plan, lesson_terms,
        student_history=student_history,
        student_profile=student_profile,
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return await _call(messages, model=model)


async def generate_lesson_summary(lesson_title: str, history: list[dict]) -> str:
    """Генерирует краткое резюме урока для памяти репетитора."""
    if not history:
        return f"Урок '{lesson_title}' был начат, но диалог не состоялся."
    messages = [
        {"role": "system", "content": get_summary_prompt()},
        *history,
        {"role": "user", "content": f"Составь резюме этого урока на тему: {lesson_title}"},
    ]
    try:
        return await _call(messages)
    except Exception:
        return f"Урок '{lesson_title}' пройден."


async def generate_student_conspect(lesson_title: str, history: list[dict]) -> str:
    """Генерирует конспект урока ДЛЯ СТУДЕНТА — тот, что покажется в UI."""
    if not history:
        return (
            f"🎯 Урок «{lesson_title}» был начат, но вы не успели разобрать материал. "
            "Пройди его заново — получишь полноценный конспект."
        )
    messages = [
        {"role": "system", "content": get_student_conspect_prompt(lesson_title)},
        *history,
        {"role": "user", "content": "Собери конспект этого урока по шаблону."},
    ]
    try:
        raw = await _call(messages)
        # На всякий случай — если модель всё-таки вставила служебные маркеры, уберём
        raw, _ = strip_phase_marker(raw)
        raw, _ = strip_done_marker(raw)
        return raw
    except Exception as e:
        log.warning("Не удалось сгенерировать конспект: %s", e)
        return f"🎯 Урок «{lesson_title}» пройден. Подробный конспект не удалось собрать — попробуй нажать «📝 Конспекты» позже."
