import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = os.getenv("DB_PATH", "stepup.db")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Модель по умолчанию (для бесплатного курса). Каждый курс может задать свою
# через поле 'ai_model' в content/courses.py.
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
# Модель для платных курсов по умолчанию — можно переопределить через env.
OPENROUTER_PAID_MODEL = os.getenv("OPENROUTER_PAID_MODEL", "anthropic/claude-haiku-4.5")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

CONVERSATION_HISTORY_LIMIT = 20

# --- Админы (список telegram_id через запятую) ---
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
}

# --- Оплата ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", "https://t.me/")  # вернуть студента в бот
PAYMENT_CURRENCY = "usd"
