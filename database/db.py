import aiosqlite
from config import DB_PATH, CONVERSATION_HISTORY_LIMIT


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                lesson_id INTEGER DEFAULT 0,
                last_module_id TEXT DEFAULT NULL,
                last_lesson_id TEXT DEFAULT NULL,
                completed INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, course_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS lesson_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                lesson_title TEXT NOT NULL,
                summary TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, course_id, module_id, lesson_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                q_idx INTEGER NOT NULL,
                chosen INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, course_id, module_id, q_idx)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, course_id, module_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                experience TEXT,
                goal TEXT,
                context TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                source TEXT NOT NULL,
                amount_usd REAL,
                payment_ref TEXT,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, course_id)
            )
        """)
        # Migrate existing progress table if columns missing
        try:
            await db.execute("ALTER TABLE progress ADD COLUMN last_module_id TEXT DEFAULT NULL")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE progress ADD COLUMN last_lesson_id TEXT DEFAULT NULL")
        except Exception:
            pass
        # Колонка с конспектом-для-студента (отличается от internal summary)
        try:
            await db.execute("ALTER TABLE lesson_summaries ADD COLUMN student_conspect TEXT")
        except Exception:
            pass
        await db.commit()


async def get_or_create_user(telegram_id: int, username: str, full_name: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        cursor = await db.execute(
            "INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)",
            (telegram_id, username, full_name),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_progress(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT course_id, lesson_id, completed, last_module_id, last_lesson_id
               FROM progress WHERE user_id = ?""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return {
            row[0]: {
                "lesson_id": row[1],
                "completed": bool(row[2]),
                "last_module_id": row[3],
                "last_lesson_id": row[4],
            }
            for row in rows
        }


async def start_course(user_id: int, course_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO progress (user_id, course_id, lesson_id) VALUES (?, ?, 0)",
            (user_id, course_id),
        )
        await db.commit()


async def update_lesson_progress(
    user_id: int, course_id: str, module_id: str, lesson_id: str
):
    """Сохраняет на каком уроке остановился студент."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO progress (user_id, course_id, lesson_id, last_module_id, last_lesson_id)
               VALUES (?, ?, 0, ?, ?)
               ON CONFLICT(user_id, course_id) DO UPDATE SET
                   last_module_id = excluded.last_module_id,
                   last_lesson_id = excluded.last_lesson_id,
                   updated_at = CURRENT_TIMESTAMP""",
            (user_id, course_id, module_id, lesson_id),
        )
        await db.commit()


async def get_last_lesson(user_id: int, course_id: str) -> dict | None:
    """Возвращает последний урок где был студент, или None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT last_module_id, last_lesson_id
               FROM progress WHERE user_id = ? AND course_id = ?""",
            (user_id, course_id),
        )
        row = await cursor.fetchone()
        if row and row[0] and row[1]:
            return {"module_id": row[0], "lesson_id": row[1]}
        return None


# ==========================
# Резюме уроков
# ==========================

async def save_lesson_summary(
    user_id: int,
    course_id: str,
    module_id: str,
    lesson_id: str,
    lesson_title: str,
    summary: str,
    student_conspect: str | None = None,
):
    """Сохраняет AI-резюме (для памяти тьютора) и при наличии — конспект для студента."""
    async with aiosqlite.connect(DB_PATH) as db:
        if student_conspect is None:
            await db.execute(
                """INSERT INTO lesson_summaries
                   (user_id, course_id, module_id, lesson_id, lesson_title, summary)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_id, course_id, module_id, lesson_id) DO UPDATE SET
                       summary = excluded.summary,
                       lesson_title = excluded.lesson_title,
                       completed_at = CURRENT_TIMESTAMP""",
                (user_id, course_id, module_id, lesson_id, lesson_title, summary),
            )
        else:
            await db.execute(
                """INSERT INTO lesson_summaries
                   (user_id, course_id, module_id, lesson_id, lesson_title, summary, student_conspect)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_id, course_id, module_id, lesson_id) DO UPDATE SET
                       summary = excluded.summary,
                       student_conspect = excluded.student_conspect,
                       lesson_title = excluded.lesson_title,
                       completed_at = CURRENT_TIMESTAMP""",
                (user_id, course_id, module_id, lesson_id, lesson_title, summary, student_conspect),
            )
        await db.commit()


async def save_student_conspect(
    user_id: int,
    course_id: str,
    module_id: str,
    lesson_id: str,
    conspect: str,
) -> None:
    """Отдельное обновление только конспекта-для-студента."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE lesson_summaries SET student_conspect = ?
               WHERE user_id = ? AND course_id = ? AND module_id = ? AND lesson_id = ?""",
            (conspect, user_id, course_id, module_id, lesson_id),
        )
        await db.commit()


async def get_student_conspect(
    user_id: int, course_id: str, module_id: str, lesson_id: str,
) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT student_conspect FROM lesson_summaries
               WHERE user_id = ? AND course_id = ? AND module_id = ? AND lesson_id = ?""",
            (user_id, course_id, module_id, lesson_id),
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] else None


async def list_user_conspects(user_id: int) -> list[dict]:
    """Все уроки студента с конспектом, отсортированные по дате завершения."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT course_id, module_id, lesson_id, lesson_title, completed_at,
                      CASE WHEN student_conspect IS NOT NULL AND student_conspect != ''
                           THEN 1 ELSE 0 END AS has_conspect
               FROM lesson_summaries
               WHERE user_id = ?
               ORDER BY completed_at DESC""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "course_id": r[0],
                "module_id": r[1],
                "lesson_id": r[2],
                "lesson_title": r[3],
                "completed_at": r[4],
                "has_conspect": bool(r[5]),
            }
            for r in rows
        ]


async def get_course_summaries(user_id: int, course_id: str) -> list[dict]:
    """Возвращает резюме всех пройденных уроков в курсе."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT module_id, lesson_id, lesson_title, summary
               FROM lesson_summaries
               WHERE user_id = ? AND course_id = ?
               ORDER BY completed_at ASC""",
            (user_id, course_id),
        )
        rows = await cursor.fetchall()
        return [
            {
                "module_id": row[0],
                "lesson_id": row[1],
                "lesson_title": row[2],
                "summary": row[3],
            }
            for row in rows
        ]


# ==========================
# История диалога с репетитором
# ==========================

async def save_message(
    user_id: int, course_id: str, module_id: str, lesson_id: str, role: str, content: str
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO conversations (user_id, course_id, module_id, lesson_id, role, content)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, course_id, module_id, lesson_id, role, content),
        )
        await db.commit()


async def get_conversation(
    user_id: int, course_id: str, module_id: str, lesson_id: str
) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT role, content FROM conversations
               WHERE user_id=? AND course_id=? AND module_id=? AND lesson_id=?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, course_id, module_id, lesson_id, CONVERSATION_HISTORY_LIMIT),
        )
        rows = await cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]


async def clear_conversation(
    user_id: int, course_id: str, module_id: str, lesson_id: str
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """DELETE FROM conversations
               WHERE user_id=? AND course_id=? AND module_id=? AND lesson_id=?""",
            (user_id, course_id, module_id, lesson_id),
        )
        await db.commit()


# ==========================
# Отметки о прохождении
# ==========================

async def get_completed_lesson_keys(user_id: int, course_id: str) -> set:
    """Возвращает множество кортежей (module_id, lesson_id) пройденных уроков."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT module_id, lesson_id FROM lesson_summaries
               WHERE user_id = ? AND course_id = ?""",
            (user_id, course_id),
        )
        rows = await cursor.fetchall()
        return {(row[0], row[1]) for row in rows}


async def mark_course_completed(user_id: int, course_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE progress SET completed = 1, updated_at = CURRENT_TIMESTAMP
               WHERE user_id = ? AND course_id = ?""",
            (user_id, course_id),
        )
        await db.commit()


# ==========================
# Тесты
# ==========================

async def reset_quiz(user_id: int, course_id: str, module_id: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """DELETE FROM quiz_answers
               WHERE user_id = ? AND course_id = ? AND module_id = ?""",
            (user_id, course_id, module_id),
        )
        await db.execute(
            """DELETE FROM quiz_results
               WHERE user_id = ? AND course_id = ? AND module_id = ?""",
            (user_id, course_id, module_id),
        )
        await db.commit()


async def save_quiz_answer(
    user_id: int, course_id: str, module_id: str,
    q_idx: int, chosen: int, is_correct: bool,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO quiz_answers
               (user_id, course_id, module_id, q_idx, chosen, is_correct)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, course_id, module_id, q_idx) DO UPDATE SET
                   chosen = excluded.chosen,
                   is_correct = excluded.is_correct,
                   answered_at = CURRENT_TIMESTAMP""",
            (user_id, course_id, module_id, q_idx, chosen, int(is_correct)),
        )
        await db.commit()


async def get_quiz_score(user_id: int, course_id: str, module_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT COALESCE(SUM(is_correct), 0) FROM quiz_answers
               WHERE user_id = ? AND course_id = ? AND module_id = ?""",
            (user_id, course_id, module_id),
        )
        row = await cursor.fetchone()
        return int(row[0]) if row else 0


async def save_quiz_result(
    user_id: int, course_id: str, module_id: str,
    score: int, total: int, passed: bool,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO quiz_results
               (user_id, course_id, module_id, score, total, passed)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, course_id, module_id) DO UPDATE SET
                   score = excluded.score,
                   total = excluded.total,
                   passed = excluded.passed,
                   completed_at = CURRENT_TIMESTAMP""",
            (user_id, course_id, module_id, score, total, int(passed)),
        )
        await db.commit()


async def get_quiz_result(
    user_id: int, course_id: str, module_id: str,
) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT score, total, passed FROM quiz_results
               WHERE user_id = ? AND course_id = ? AND module_id = ?""",
            (user_id, course_id, module_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {"score": row[0], "total": row[1], "passed": bool(row[2])}


# ==========================
# Доступ к курсам (платные)
# ==========================

async def has_course_access(user_id: int, course_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM user_courses WHERE user_id = ? AND course_id = ? LIMIT 1",
            (user_id, course_id),
        )
        return (await cursor.fetchone()) is not None


async def grant_course_access(
    user_id: int,
    course_id: str,
    source: str = "admin",
    amount_usd: float | None = None,
    payment_ref: str | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO user_courses
               (user_id, course_id, source, amount_usd, payment_ref)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, course_id, source, amount_usd, payment_ref),
        )
        await db.commit()


async def get_user_telegram_id(user_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT telegram_id FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_user_by_telegram_id(telegram_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


# ==========================
# Профиль студента
# ==========================

async def save_user_profile(
    user_id: int,
    experience: str | None = None,
    goal: str | None = None,
    context: str | None = None,
) -> None:
    """UPSERT профиля — передавай только заполняемые поля, остальные не трогаются."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT experience, goal, context FROM user_profiles WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        cur_exp, cur_goal, cur_ctx = row if row else (None, None, None)
        new_exp = experience if experience is not None else cur_exp
        new_goal = goal if goal is not None else cur_goal
        new_ctx = context if context is not None else cur_ctx
        await db.execute(
            """INSERT INTO user_profiles (user_id, experience, goal, context)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   experience = excluded.experience,
                   goal = excluded.goal,
                   context = excluded.context,
                   updated_at = CURRENT_TIMESTAMP""",
            (user_id, new_exp, new_goal, new_ctx),
        )
        await db.commit()


async def get_user_profile(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT experience, goal, context FROM user_profiles WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        if not any(row):
            return None
        return {"experience": row[0], "goal": row[1], "context": row[2]}


async def is_profile_complete(user_id: int) -> bool:
    """Профиль считается заполненным если есть опыт и цель (context необязателен)."""
    profile = await get_user_profile(user_id)
    return bool(profile and profile.get("experience") and profile.get("goal"))


async def get_passed_modules(user_id: int, course_id: str) -> set:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT module_id FROM quiz_results
               WHERE user_id = ? AND course_id = ? AND passed = 1""",
            (user_id, course_id),
        )
        rows = await cursor.fetchall()
        return {row[0] for row in rows}
