import logging
import aiohttp
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL
from ai.prompts import get_lesson_system_prompt

log = logging.getLogger(__name__)

HEADERS = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://stepup-bot.railway.app",
    "X-Title": "StepUp",
}


async def _call(messages: list) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY не задан в переменных окружения")

    headers = {**HEADERS, "Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 600,
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


async def start_lesson(course_title: str, module_title: str, lesson_title: str) -> str:
    system_prompt = get_lesson_system_prompt(course_title, module_title, lesson_title)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": "Начинаем урок!"},
    ]
    return await _call(messages)


async def get_tutor_reply(
    course_title: str,
    module_title: str,
    lesson_title: str,
    history: list[dict],
    user_message: str,
) -> str:
    system_prompt = get_lesson_system_prompt(course_title, module_title, lesson_title)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return await _call(messages)
