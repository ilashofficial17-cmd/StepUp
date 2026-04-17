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
        # Migrate existing progress table if columns missing
        try:
            await db.execute("ALTER TABLE progress ADD COLUMN last_module_id TEXT DEFAULT NULL")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE progress ADD COLUMN last_lesson_id TEXT DEFAULT NULL")
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
):
    """Сохраняет AI-резюме после завершения урока."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO lesson_summaries
               (user_id, course_id, module_id, lesson_id, lesson_title, summary)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, course_id, module_id, lesson_id, lesson_title, summary),
        )
        await db.commit()


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
