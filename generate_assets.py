"""
Генератор картинок для уроков StepUp.
Запуск: python3 generate_assets.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

# ── Цвета ──────────────────────────────────────────────────────────
BG           = (26, 15, 60)      # #1A0F3C
ORANGE       = (232, 83, 26)     # #E8531A
WHITE        = (255, 255, 255)   # #FFFFFF
PURPLE_DARK  = (45, 27, 105)     # #2D1B69
PURPLE_LIGHT = (155, 142, 196)   # #9B8EC4
PURPLE_MID   = (196, 181, 232)   # #C4B5E8

W, H = 1080, 1080
PAD = 60

# ── Шрифты ─────────────────────────────────────────────────────────
FONT_BOLD    = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size)

# ── Хелперы ────────────────────────────────────────────────────────
def new_image():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)

def draw_brand(draw):
    """StepUp в верхнем левом углу."""
    f = font(36, bold=True)
    draw.text((PAD, PAD), "Step", font=f, fill=PURPLE_DARK)
    w = draw.textlength("Step", font=f)
    draw.text((PAD + w, PAD), "Up", font=f, fill=ORANGE)

def draw_hline(draw, y, color=PURPLE_DARK, width=400):
    x0 = (W - width) // 2
    draw.line([(x0, y), (x0 + width, y)], fill=color, width=2)

def draw_centered(draw, text, y, size, color, bold=False):
    f = font(size, bold)
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, y), text, font=f, fill=color)
    _, _, _, h = draw.textbbox((0, 0), text, font=f)
    return y + h

def draw_pill(draw, text, cx, y, bg, fg, size=26):
    f = font(size, bold=True)
    tw = draw.textlength(text, font=f)
    ph, pv = 20, 10
    x0 = cx - tw / 2 - ph
    x1 = cx + tw / 2 + ph
    y0 = y
    y1 = y + size + pv * 2
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=bg)
    draw.text((cx - tw / 2, y + pv), text, font=f, fill=fg)
    return y1

def wrap_text(draw, text, max_width, size, bold=False):
    """Переносит текст по словам."""
    f = font(size, bold)
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textlength(test, font=f) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def draw_wrapped(draw, text, x, y, max_width, size, color, bold=False, center=False):
    f = font(size, bold)
    lines = wrap_text(draw, text, max_width, size, bold)
    for line in lines:
        if center:
            lw = draw.textlength(line, font=f)
            draw.text(((W - lw) / 2, y), line, font=f, fill=color)
        else:
            draw.text((x, y), line, font=f, fill=color)
        y += size + 8
    return y

# ── Картинки ───────────────────────────────────────────────────────

def make_banner():
    img, draw = new_image()
    draw_brand(draw)

    y = 320
    # Подзаголовок
    y = draw_centered(draw, "Модуль 1  ·  Первый шаг", y, 28, PURPLE_LIGHT)
    y += 24

    # Номер урока
    y = draw_centered(draw, "Урок 1", y, 80, ORANGE, bold=True)
    y += 20

    # Название
    y = draw_centered(draw, "Что такое digital", y, 52, WHITE, bold=True)
    y += 8
    y = draw_centered(draw, "и почему сейчас", y, 52, WHITE, bold=True)
    y += 8
    y = draw_centered(draw, "самое время", y, 52, WHITE, bold=True)
    y += 48

    draw_hline(draw, y, PURPLE_DARK, 300)
    y += 16
    draw_centered(draw, "StepUp · Первый шаг", y, 22, PURPLE_LIGHT)

    img.save("assets/lesson1_banner.png")
    print("✅ lesson1_banner.png")


def make_glossary():
    img, draw = new_image()
    draw_brand(draw)

    # Плашка заголовка
    y = draw_pill(draw, "📖  СЛОВАРЬ УРОКА", W // 2, 130, ORANGE, WHITE, size=28)
    y += 40

    terms = [
        ("Digital-маркетинг", "Продвижение бизнеса через интернет: соцсети, реклама, сайты, email"),
        ("Онлайн-присутствие", "Существование бизнеса в интернете — сайт, соцсети, реклама"),
        ("Путь клиента", "Все шаги человека от «не знал о тебе» до «купил»"),
        ("Digital-специалист", "Человек который управляет онлайн-продвижением бизнеса"),
    ]

    for term, definition in terms:
        draw.text((PAD, y), term, font=font(30, bold=True), fill=WHITE)
        y += 38
        y = draw_wrapped(draw, definition, PAD, y, W - PAD * 2, 24, PURPLE_LIGHT)
        y += 14
        draw.line([(PAD, y), (W - PAD, y)], fill=PURPLE_DARK, width=1)
        y += 24

    img.save("assets/lesson1_glossary.png")
    print("✅ lesson1_glossary.png")


def make_path():
    img, draw = new_image()
    draw_brand(draw)

    draw_centered(draw, "Как клиент покупает сегодня", 130, 40, WHITE, bold=True)

    # РАНЬШЕ
    rx = 200
    ry = 240
    draw_pill(draw, "РАНЬШЕ", rx, ry, PURPLE_DARK, PURPLE_LIGHT, size=22)
    ry += 60
    old_steps = ["Реклама на ТВ", "Магазин", "Покупка"]
    for step in old_steps:
        bx0, bx1 = rx - 130, rx + 130
        draw.rounded_rectangle([bx0, ry, bx1, ry + 52], radius=10, fill=PURPLE_DARK)
        sw = draw.textlength(step, font=font(22))
        draw.text((rx - sw / 2, ry + 14), step, font=font(22), fill=PURPLE_LIGHT)
        ry += 52
        if step != old_steps[-1]:
            draw.text((rx - 6, ry + 4), "↓", font=font(26, bold=True), fill=PURPLE_LIGHT)
            ry += 36

    # Вертикальная линия
    draw.line([(W // 2, 220), (W // 2, 820)], fill=PURPLE_DARK, width=2)

    # СЕЙЧАС
    sx = 780
    sy = 240
    draw_pill(draw, "СЕЙЧАС", sx, sy, ORANGE, WHITE, size=22)
    sy += 60
    new_steps = ["Соцсети", "Гугл", "Отзывы", "Директ", "Покупка"]
    for step in new_steps:
        bx0, bx1 = sx - 130, sx + 130
        draw.rounded_rectangle([bx0, sy, bx1, sy + 52], radius=10, fill=PURPLE_DARK)
        sw = draw.textlength(step, font=font(22, bold=True))
        draw.text((sx - sw / 2, sy + 14), step, font=font(22, bold=True), fill=WHITE)
        sy += 52
        if step != new_steps[-1]:
            draw.text((sx - 6, sy + 4), "↓", font=font(26, bold=True), fill=ORANGE)
            sy += 36

    draw_centered(draw, "Каждый шаг — онлайн", 920, 30, ORANGE, bold=True)

    img.save("assets/lesson1_path.png")
    print("✅ lesson1_path.png")


def make_market():
    img, draw = new_image()
    draw_brand(draw)

    draw_centered(draw, "Рынок digital-рекламы", 130, 44, WHITE, bold=True)
    draw_centered(draw, "растёт каждый год", 190, 28, PURPLE_LIGHT)

    data = [
        ("$333 млрд", "2019", PURPLE_LIGHT),
        ("$491 млрд", "2022", PURPLE_MID),
        ("$600+ млрд", "2024", ORANGE),
    ]

    col_w = W // 3
    # Бар-диаграмма
    bar_y = 320
    bar_h_max = 260
    heights = [110, 170, 260]
    bar_w = 140
    for i, ((amount, year, color), h) in enumerate(zip(data, heights)):
        cx = col_w * i + col_w // 2
        # Столбец
        x0 = cx - bar_w // 2
        x1 = cx + bar_w // 2
        y0 = bar_y + bar_h_max - h
        y1 = bar_y + bar_h_max
        draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=color)
        # Сумма над столбцом
        aw = draw.textlength(amount, font=font(34, bold=True))
        draw.text((cx - aw / 2, y0 - 50), amount, font=font(34, bold=True), fill=color)
        # Год под столбцом
        yw = draw.textlength(year, font=font(28))
        draw.text((cx - yw / 2, y1 + 14), year, font=font(28), fill=color)
        # Стрелка между столбцами
        if i < 2:
            ax = col_w * (i + 1) - 14
            draw.text((ax, bar_y + bar_h_max // 2 - 20), "→", font=font(36, bold=True), fill=ORANGE)

    base_y = bar_y + bar_h_max + 60
    draw_hline(draw, base_y, PURPLE_DARK, 700)
    draw_centered(draw, "↑  х2 за 5 лет", base_y + 24, 40, ORANGE, bold=True)

    img.save("assets/lesson1_market.png")
    print("✅ lesson1_market.png")


def make_formula():
    img, draw = new_image()
    draw_brand(draw)

    # Блок 1
    y = 220
    y = draw_centered(draw, "Курс = карта местности", y, 42, WHITE, bold=True)
    y += 12
    y = draw_centered(draw, "Ты = тот кто идёт по ней", y, 32, PURPLE_LIGHT)
    y += 48
    draw_hline(draw, y, PURPLE_DARK, 500)
    y += 48

    # Блок 2 — формула
    parts = [
        ("Знания", PURPLE_MID),
        ("  ×  ", PURPLE_LIGHT),
        ("Практика", ORANGE),
        ("  ×  ", PURPLE_LIGHT),
        ("Дисциплина", WHITE),
    ]
    total_w = sum(draw.textlength(t, font=font(36, bold=True)) for t, _ in parts)
    x = (W - total_w) / 2
    for text, color in parts:
        draw.text((x, y), text, font=font(36, bold=True), fill=color)
        x += draw.textlength(text, font=font(36, bold=True))

    y += 52
    y = draw_centered(draw, "=  Результат", y, 64, ORANGE, bold=True)
    y += 48
    draw_hline(draw, y, PURPLE_DARK, 500)
    y += 48

    # Блок 3
    y = draw_centered(draw, "Курс даёт знания.", y, 30, PURPLE_LIGHT)
    y += 12
    draw_centered(draw, "Остальное — твоя работа.", y, 30, PURPLE_LIGHT)

    img.save("assets/lesson1_formula.png")
    print("✅ lesson1_formula.png")


# ── Main ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    make_banner()
    make_glossary()
    make_path()
    make_market()
    make_formula()
    print("\n🎉 Все картинки сохранены в папку assets/")
