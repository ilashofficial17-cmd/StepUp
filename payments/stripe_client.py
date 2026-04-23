"""Создание Stripe Checkout-сессий для покупки курсов.

Минимальная обёртка: принимает курс + telegram_id, возвращает URL.
Webhook обрабатывает POST от Stripe и выдаёт доступ.
"""

import logging
from typing import Optional

import aiohttp

from config import (
    PAYMENT_CURRENCY,
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
)

log = logging.getLogger(__name__)

STRIPE_API_URL = "https://api.stripe.com/v1/checkout/sessions"


def is_stripe_configured() -> bool:
    return bool(STRIPE_SECRET_KEY)


async def create_checkout_url(
    course_id: str,
    course_title: str,
    price_usd: int,
    telegram_id: int,
    user_db_id: int,
) -> Optional[str]:
    """Создаёт Stripe Checkout-сессию. Возвращает URL или None если Stripe не настроен
    / произошла ошибка. Метаданные (course_id, user_db_id, telegram_id) передаются
    чтобы webhook мог выдать доступ нужному пользователю.
    """
    if not is_stripe_configured():
        log.warning("Stripe не настроен — STRIPE_SECRET_KEY пуст")
        return None

    # Stripe ожидает x-www-form-urlencoded, поэтому формируем список кортежей
    form = [
        ("mode", "payment"),
        ("success_url", STRIPE_SUCCESS_URL),
        ("cancel_url", STRIPE_SUCCESS_URL),
        ("line_items[0][price_data][currency]", PAYMENT_CURRENCY),
        ("line_items[0][price_data][product_data][name]", f"StepUp · {course_title}"),
        ("line_items[0][price_data][unit_amount]", str(price_usd * 100)),  # в центах
        ("line_items[0][quantity]", "1"),
        ("metadata[course_id]", course_id),
        ("metadata[user_db_id]", str(user_db_id)),
        ("metadata[telegram_id]", str(telegram_id)),
        ("client_reference_id", f"{telegram_id}:{course_id}"),
    ]

    headers = {"Authorization": f"Bearer {STRIPE_SECRET_KEY}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                STRIPE_API_URL, data=form, headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    log.error("Stripe checkout create failed: %s", data)
                    return None
                return data.get("url")
    except Exception as e:
        log.error("Stripe checkout error: %s", e)
        return None
