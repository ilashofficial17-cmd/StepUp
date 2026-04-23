"""HTTP-сервер для приёма Stripe-вебхуков.

Запускается ПАРАЛЛЕЛЬНО с ботом. При платеже checkout.session.completed
выдаёт доступ к курсу пользователю из metadata.

Чтобы включить:
1. Задать STRIPE_SECRET_KEY и STRIPE_WEBHOOK_SECRET в env.
2. Поднять процесс webhook.py (например вторым worker в Railway / на своём сервере).
3. В Stripe Dashboard → Webhooks добавить endpoint указывающий на
   `https://<твой-домен>/stripe/webhook` с событием `checkout.session.completed`.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time

from aiohttp import web

from config import STRIPE_WEBHOOK_SECRET
from database.db import grant_course_access, init_db

log = logging.getLogger(__name__)


def _verify_stripe_signature(payload: bytes, sig_header: str, tolerance: int = 300) -> bool:
    """Проверяет подпись вебхука по инструкции Stripe.
    Формат sig_header: 't=1234567890,v1=abcdef...,v0=...'
    """
    if not STRIPE_WEBHOOK_SECRET or not sig_header:
        return False
    try:
        items = dict(kv.split("=", 1) for kv in sig_header.split(","))
        ts = int(items.get("t", "0"))
        v1 = items.get("v1", "")
    except Exception:
        return False
    if abs(time.time() - ts) > tolerance:
        return False
    signed_payload = f"{ts}.".encode() + payload
    expected = hmac.new(
        STRIPE_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, v1)


async def stripe_webhook(request: web.Request):
    payload = await request.read()
    sig = request.headers.get("Stripe-Signature", "")

    if not _verify_stripe_signature(payload, sig):
        log.warning("Stripe webhook: invalid signature")
        return web.Response(status=400, text="invalid signature")

    event = json.loads(payload)
    if event.get("type") != "checkout.session.completed":
        return web.Response(status=200, text="ignored")

    session = event["data"]["object"]
    metadata = session.get("metadata") or {}
    course_id = metadata.get("course_id")
    user_db_id_raw = metadata.get("user_db_id")
    amount_total = session.get("amount_total")  # в центах

    if not course_id or not user_db_id_raw:
        log.error("Stripe webhook: missing metadata: %s", metadata)
        return web.Response(status=400, text="missing metadata")

    user_db_id = int(user_db_id_raw)
    amount_usd = (amount_total / 100) if amount_total else None

    await grant_course_access(
        user_db_id,
        course_id,
        source="stripe",
        amount_usd=amount_usd,
        payment_ref=session.get("id"),
    )
    log.info(
        "Stripe: granted %s to user_db_id=%s for $%.2f", course_id, user_db_id, amount_usd or 0
    )
    return web.Response(status=200, text="ok")


async def health(_request):
    return web.Response(text="stepup-webhook ok")


async def build_app() -> web.Application:
    await init_db()
    app = web.Application()
    app.router.add_post("/stripe/webhook", stripe_webhook)
    app.router.add_get("/health", health)
    return app


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8080"))
    logging.basicConfig(level=logging.INFO)
    web.run_app(build_app(), port=port)
