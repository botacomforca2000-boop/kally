import random
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import embed


def xp_needed(level: int) -> int:
    return 5 * level ** 2 + 50 * level + 100


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns: dict[tuple[int, int], float] = {}

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild:
            return
        key, now = (msg.guild.id, msg.author.id), time.time()
        if now - self.cooldowns.get(key, 0) < 60:
            return
        self.cooldowns[key] = now

        db = self.bot.db
        row = await db.fetchone("SELECT xp, level FROM levels WHERE guild_id=? AND user_id=?", *key)
        xp, level = (row["xp"], row["level"]) if row else (0, 0)
        xp += random.randint(15, 25)
        leveled = False
        while xp >= xp_needed(level):
            xp -= xp_needed(level)
            level += 1
            leveled = True
        await db.execute(
            "INSERT INTO levels(guild_id,user_id,xp,level) VALUES(?,?,?,?) "
            "ON CONFLICT(guild_id,user_id) DO UPDATE SET xp=excluded.xp, level=excluded.level",
            *key, xp, level)

        if leveled:
            cfg = await db.get_config(msg.guild.id)
            channel = msg.guild.get_channel(cfg["level_channel"]) if cfg["level_channel"] else msg.channel
            try:
                await channel.send(f"🎉 {msg.author.mention} subiu para o **nível {level}**!")
            except discord.HTTPException:
                pass

    @app_commands.command(name="rank", description="Mostra seu nível e XP")
    @app_commands.guild_only()
    async def rank(self, i: discord.Interaction, membro: Optional[discord.Member] = None):
        m = membro or i.user
        row = await self.bot.db.fetchone("SELECT xp, level FROM levels WHERE guild_id=? AND user_id=?", i.guild_id, m.id)
        xp, level = (row["xp"], row["level"]) if row else (0, 0)
        need = xp_needed(level)
        filled = int(xp / need * 10)
        bar = "🟪" * filled + "⬛" * (10 - filled)
        e = embed(f"Rank de {m.display_name}", f"**Nível {level}**\n{bar}\n`{xp}/{need} XP`")
        e.set_thumbnail(url=m.display_avatar.url)
        await i.response.send_message(embed=e)

    @app_commands.command(name="top", description="Ranking de níveis do servidor")
    @app_commands.guild_only()
    async def top(self, i: discord.Interaction):
        rows = await self.bot.db.fetchall(
            "SELECT user_id, xp, level FROM levels WHERE guild_id=? ORDER BY level DESC, xp DESC LIMIT 10", i.guild_id)
        if not rows:
            return await i.response.send_message("Ninguém tem XP ainda.", ephemeral=True)
        medals = ["🥇", "🥈", "🥉"]
        desc = "\n".join(f"{medals[n] if n < 3 else f'`{n + 1}.`'} <@{r['user_id']}> — nível **{r['level']}** ({r['xp']} XP)" for n, r in enumerate(rows))
        await i.response.send_message(embed=embed("🏆 Top níveis", desc))


async def setup(bot):
    await bot.add_cog(Levels(bot))
