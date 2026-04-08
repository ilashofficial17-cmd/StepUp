CATEGORIES = [
    {"id": "promo",    "title": "Продвижение и контент", "emoji": "📣", "btn": "📣 Продвижение"},
    {"id": "business", "title": "Бизнес и продажи",      "emoji": "💼", "btn": "💼 Бизнес"},
    {"id": "tech",     "title": "Технологии",             "emoji": "🤖", "btn": "🤖 Технологии"},
]

CATEGORIES_BY_ID  = {c["id"]: c for c in CATEGORIES}
CATEGORIES_BY_BTN = {c["btn"]: c for c in CATEGORIES}

# ==========================
# Модули и уроки курса «Первый шаг»
# ==========================
INTRO_MODULES = [
    {
        "id": "m1",
        "title": "Как устроен онлайн-рынок",
        "emoji": "🌐",
        "lessons": [
            {"id": "m1l1", "title": "Что такое digital и почему сейчас самое время"},
            {"id": "m1l2", "title": "Кто платит деньги и за что"},
            {"id": "m1l3", "title": "Какие профессии есть и сколько зарабатывают"},
        ],
        "has_quiz": True,
    },
    {
        "id": "m2",
        "title": "Трафик и контент",
        "emoji": "📣",
        "lessons": [
            {"id": "m2l1", "title": "SMM — как бренды живут в соцсетях"},
            {"id": "m2l2", "title": "Реклама и таргет — как бизнес находит клиентов"},
            {"id": "m2l3", "title": "Контент и копирайтинг — слова, которые продают"},
        ],
        "has_quiz": True,
    },
    {
        "id": "m3",
        "title": "Продажи и технологии",
        "emoji": "⚙️",
        "lessons": [
            {"id": "m3l1", "title": "Воронки и CRM — как продавать системно"},
            {"id": "m3l2", "title": "No-code и AI — делать в 10 раз больше"},
            {"id": "m3l3", "title": "Личный бренд и фриланс — продавать себя"},
        ],
        "has_quiz": True,
    },
]

INTRO_MODULES_BY_ID = {m["id"]: m for m in INTRO_MODULES}

# ==========================
# Список всех курсов
# ==========================
COURSES = [
    {
        "id": "intro",
        "title": "Первый шаг",
        "emoji": "🆓",
        "is_free": True,
        "category": None,
        "description": (
            "Вводный курс в мир онлайн-маркетинга и заработка в интернете.\n\n"
            "3 модуля · 9 уроков · тесты после каждого модуля\n\n"
            "Пройди и узнай какое направление тебе подходит."
        ),
        "modules": INTRO_MODULES,
    },
    {
        "id": "smm",
        "title": "SMM-специалист",
        "emoji": "📱",
        "is_free": False,
        "category": "promo",
        "description": "Ведение соцсетей, контент-стратегия, работа с аудиторией и аналитика.",
        "modules": [],
    },
    {
        "id": "target",
        "title": "Таргетолог",
        "emoji": "🎯",
        "is_free": False,
        "category": "promo",
        "description": "Настройка рекламы в VK, Telegram Ads, Meta. Аналитика и оптимизация.",
        "modules": [],
    },
    {
        "id": "content",
        "title": "Контент-маркетинг",
        "emoji": "✍️",
        "is_free": False,
        "category": "promo",
        "description": "Контент-стратегия, редполитика, дистрибуция и продвижение.",
        "modules": [],
    },
    {
        "id": "copy",
        "title": "Копирайтинг",
        "emoji": "📝",
        "is_free": False,
        "category": "promo",
        "description": "Продающие тексты, посты, лендинги. Пишем так, чтобы покупали.",
        "modules": [],
    },
    {
        "id": "email",
        "title": "Email-маркетинг",
        "emoji": "📧",
        "is_free": False,
        "category": "promo",
        "description": "Рассылки, автоворонки, сегментация базы и аналитика.",
        "modules": [],
    },
    {
        "id": "influence",
        "title": "Influence-маркетинг",
        "emoji": "🌟",
        "is_free": False,
        "category": "promo",
        "description": "Работа с блогерами, посевы, коллаборации и оценка эффективности.",
        "modules": [],
    },
    {
        "id": "sales",
        "title": "Автоматизация продаж",
        "emoji": "⚙️",
        "is_free": False,
        "category": "business",
        "description": "CRM, чат-боты, воронки продаж. Продавай системно и автоматически.",
        "modules": [],
    },
    {
        "id": "ecom",
        "title": "Маркетплейсы (e-com)",
        "emoji": "🛒",
        "is_free": False,
        "category": "business",
        "description": "Продажи на Ozon и Wildberries: карточки, реклама, масштабирование.",
        "modules": [],
    },
    {
        "id": "freelance",
        "title": "Фриланс и продажа услуг",
        "emoji": "💼",
        "is_free": False,
        "category": "business",
        "description": "Упакуй себя как специалиста, найди клиентов и выстрой доход.",
        "modules": [],
    },
    {
        "id": "brand",
        "title": "Личный бренд",
        "emoji": "⭐",
        "is_free": False,
        "category": "business",
        "description": "Позиционирование, экспертность и монетизация личного бренда.",
        "modules": [],
    },
    {
        "id": "nocode",
        "title": "No-code автоматизация",
        "emoji": "🔧",
        "is_free": False,
        "category": "tech",
        "description": "Make, n8n, Zapier — автоматизируй процессы без кода.",
        "modules": [],
    },
    {
        "id": "vibe",
        "title": "Вайб-кодинг",
        "emoji": "🤖",
        "is_free": False,
        "category": "tech",
        "description": "Создавай продукты с ИИ: Cursor, Claude, v0. Без опыта в разработке.",
        "modules": [],
    },
]

COURSES_BY_ID = {c["id"]: c for c in COURSES}


def get_courses_by_category(category_id: str) -> list:
    return [c for c in COURSES if c["category"] == category_id]
