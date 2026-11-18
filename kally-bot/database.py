import aiosqlite

CONFIG_KEYS = {
    "log_channel", "level_channel", "vip_role", "insta_channel",
    "ticket_category", "ticket_staff_role", "antiraid_enabled", "antiraid_threshold",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    log_channel INTEGER,
    level_channel INTEGER,
    vip_role INTEGER,
    insta_channel INTEGER,
    ticket_category INTEGER,
    ticket_staff_role INTEGER,
    antiraid_enabled INTEGER DEFAULT 0,
    antiraid_threshold INTEGER DEFAULT 5
);
CREATE TABLE IF NOT EXISTS levels (
    guild_id INTEGER, user_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS economy (
    guild_id INTEGER, user_id INTEGER, balance INTEGER DEFAULT 0, last_daily REAL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS vips (
    guild_id INTEGER, user_id INTEGER, expires_at INTEGER,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER,
    mod_id INTEGER, reason TEXT, created_at INTEGER
);
CREATE TABLE IF NOT EXISTS insta_posts (
    message_id INTEGER PRIMARY KEY, guild_id INTEGER, user_id INTEGER, created_at INTEGER
);
CREATE TABLE IF NOT EXISTS insta_likes (
    message_id INTEGER, user_id INTEGER, PRIMARY KEY (message_id, user_id)
);
"""


class DB:
    def __init__(self, path: str = "kally.db"):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def execute(self, query: str, *args):
        cur = await self.conn.execute(query, args)
        await self.conn.commit()
        return cur

    async def fetchone(self, query: str, *args):
        cur = await self.conn.execute(query, args)
        return await cur.fetchone()

    async def fetchall(self, query: str, *args):
        cur = await self.conn.execute(query, args)
        return await cur.fetchall()

    async def get_config(self, guild_id: int):
        row = await self.fetchone("SELECT * FROM guild_config WHERE guild_id=?", guild_id)
        if row is None:
            await self.execute("INSERT INTO guild_config(guild_id) VALUES(?)", guild_id)
            row = await self.fetchone("SELECT * FROM guild_config WHERE guild_id=?", guild_id)
        return row

    async def set_config(self, guild_id: int, key: str, value):
        if key not in CONFIG_KEYS:
            raise ValueError(f"Chave inválida: {key}")
        await self.get_config(guild_id)
        await self.execute(f"UPDATE guild_config SET {key}=? WHERE guild_id=?", value, guild_id)
