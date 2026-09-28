import aiosqlite
import datetime
from typing import Optional, Dict, Any, List

DB_PATH = "bot_data.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_subscribed BOOLEAN DEFAULT 0,
                subscription_until TIMESTAMP,
                generations_count INTEGER DEFAULT 0,
                free_generations_left INTEGER DEFAULT 3,
                referrer_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stack TEXT,
                user_prompt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tariff TEXT,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_or_create_user(user_id: int, username: Optional[str], first_name: str, referrer_id: Optional[int] = None) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Update username if changed
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                    (username, first_name, user_id)
                )
                await db.commit()
                return dict(row)
            
            # New user
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, free_generations_left, referrer_id)
                VALUES (?, ?, ?, 3, ?)
            """, (user_id, username, first_name, referrer_id))
            
            # Reward referrer if exists
            if referrer_id and referrer_id != user_id:
                await db.execute("""
                    UPDATE users 
                    SET free_generations_left = free_generations_left + 3 
                    WHERE user_id = ?
                """, (referrer_id,))
                
            await db.commit()
            
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as new_cursor:
                new_row = await new_cursor.fetchone()
                return dict(new_row)

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def use_generation(user_id: int, stack: str, prompt: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user:
                return False
            
            is_sub = bool(user["is_subscribed"])
            # Check if subscription expired
            if is_sub and user["subscription_until"]:
                sub_end = datetime.datetime.fromisoformat(user["subscription_until"])
                if datetime.datetime.now() > sub_end:
                    is_sub = False
                    await db.execute("UPDATE users SET is_subscribed = 0 WHERE user_id = ?", (user_id,))
            
            if not is_sub and user["free_generations_left"] <= 0:
                return False
            
            # Deduct free generation if not subscribed
            if not is_sub:
                await db.execute(
                    "UPDATE users SET free_generations_left = free_generations_left - 1, generations_count = generations_count + 1 WHERE user_id = ?",
                    (user_id,)
                )
            else:
                await db.execute(
                    "UPDATE users SET generations_count = generations_count + 1 WHERE user_id = ?",
                    (user_id,)
                )
                
            await db.execute(
                "INSERT INTO generations (user_id, stack, user_prompt) VALUES (?, ?, ?)",
                (user_id, stack, prompt)
            )
            await db.commit()
            return True

async def activate_subscription(user_id: int, days: int = 30):
    until = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_subscribed = 1, subscription_until = ? WHERE user_id = ?",
            (until, user_id)
        )
        await db.commit()

async def get_stats() -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_subscribed = 1") as c2:
            active_subs = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM generations") as c3:
            total_gens = (await c3.fetchone())[0]
            
        return {
            "total_users": total_users,
            "active_subs": active_subs,
            "total_gens": total_gens
        }

async def get_all_user_ids() -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
