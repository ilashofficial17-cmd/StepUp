CATEGORIES = [
    {
        "id": "promo",
        "title": "Продвижение и контент",
        "emoji": "📣",
    },
    {
        "id": "business",
        "title": "Бизнес и продажи",
        "emoji": "💼",
    },
    {
        "id": "tech",
        "title": "Технологии",
        "emoji": "🤖",
    },
]

CATEGORIES_BY_ID = {c["id"]: c for c in CATEGORIES}

COURSES = [
    {
        "id": "intro",
        "title": "Первый шаг",
        "emoji": "🆓",
        "is_free": True,
        "category": None,
        "description": (
            "Вводный курс в мир онлайн-маркетинга и заработка в интернете.\n\n"
            "За 7 уроков ты познакомишься с каждым направлением, поймёшь "
            "как устроена сфера и выберешь то, что тебе ближе всего."
        ),
        "lessons_count": 7,
    },
    {
        "id": "smm",
        "title": "SMM-специалист",
        "emoji": "📱",
        "is_free": False,
        "category": "promo",
        "description": "Ведение соцсетей, контент-стратегия, работа с аудиторией и аналитика.",
        "lessons_count": 0,
    },
    {
        "id": "target",
        "title": "Таргетолог",
        "emoji": "🎯",
        "is_free": False,
        "category": "promo",
        "description": "Настройка рекламы в VK, Telegram Ads, Meta. Аналитика и оптимизация кампаний.",
        "lessons_count": 0,
    },
    {
        "id": "content",
        "title": "Контент-маркетинг",
        "emoji": "✍️",
        "is_free": False,
        "category": "promo",
        "description": "Контент-стратегия, редполитика, дистрибуция и продвижение через контент.",
        "lessons_count": 0,
    },
    {
        "id": "copy",
        "title": "Копирайтинг",
        "emoji": "📝",
        "is_free": False,
        "category": "promo",
        "description": "Продающие тексты, посты, лендинги. Пишем так, чтобы читали и покупали.",
        "lessons_count": 0,
    },
    {
        "id": "email",
        "title": "Email-маркетинг",
        "emoji": "📧",
        "is_free": False,
        "category": "promo",
        "description": "Рассылки, автоворонки, сегментация базы и аналитика open rate / CTR.",
        "lessons_count": 0,
    },
    {
        "id": "influence",
        "title": "Influence-маркетинг",
        "emoji": "🌟",
        "is_free": False,
        "category": "promo",
        "description": "Работа с блогерами, посевы, коллаборации и оценка эффективности размещений.",
        "lessons_count": 0,
    },
    {
        "id": "sales",
        "title": "Автоматизация продаж",
        "emoji": "⚙️",
        "is_free": False,
        "category": "business",
        "description": "CRM-системы, чат-боты, воронки продаж. Автоматизируй бизнес и продавай пока спишь.",
        "lessons_count": 0,
    },
    {
        "id": "ecom",
        "title": "Маркетплейсы (e-com)",
        "emoji": "🛒",
        "is_free": False,
        "category": "business",
        "description": "Продажи на Ozon и Wildberries: карточки, реклама, аналитика и масштабирование.",
        "lessons_count": 0,
    },
    {
        "id": "freelance",
        "title": "Фриланс и продажа услуг",
        "emoji": "💼",
        "is_free": False,
        "category": "business",
        "description": "Упакуй себя как специалиста, найди первых клиентов и выстрой стабильный доход.",
        "lessons_count": 0,
    },
    {
        "id": "brand",
        "title": "Личный бренд",
        "emoji": "⭐",
        "is_free": False,
        "category": "business",
        "description": "Позиционирование, экспертность, работа с аудиторией и монетизация личного бренда.",
        "lessons_count": 0,
    },
    {
        "id": "nocode",
        "title": "No-code автоматизация",
        "emoji": "🔧",
        "is_free": False,
        "category": "tech",
        "description": "Make, n8n, Zapier — автоматизируй бизнес-процессы без единой строчки кода.",
        "lessons_count": 0,
    },
    {
        "id": "vibe",
        "title": "Вайб-кодинг",
        "emoji": "🤖",
        "is_free": False,
        "category": "tech",
        "description": "Создавай продукты с помощью ИИ: Cursor, Claude, v0. Без опыта в разработке.",
        "lessons_count": 0,
    },
]

COURSES_BY_ID = {c["id"]: c for c in COURSES}


def get_courses_by_category(category_id: str) -> list:
    return [c for c in COURSES if c["category"] == category_id]
