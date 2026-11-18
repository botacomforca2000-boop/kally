import time
from collections import defaultdict, deque

import discord
from discord.ext import commands

from utils import embed

WINDOW = 10        # segundos para contar entradas
LOCKDOWN = 120     # segundos de lockdown após disparar


class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.joins: dict[int, deque] = defaultdict(deque)
        self.lockdown_until: dict[int, float] = {}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = await self.bot.db.get_config(member.guild.id)
        if not cfg["antiraid_enabled"] or member.bot:
            return
        gid, now = member.guild.id, time.time()
        q = self.joins[gid]
        q.append(now)
        while q and now - q[0] > WINDOW:
            q.popleft()

        active = self.lockdown_until.get(gid, 0) > now
        if not active and len(q) >= cfg["antiraid_threshold"]:
            self.lockdown_until[gid] = now + LOCKDOWN
            active = True
            await self._alert(member.guild, cfg, len(q))
            # expulsa também quem entrou na janela que disparou o alerta
        if active:
            try:
                await member.kick(reason="Kally Anti-Raid: lockdown ativo")
            except discord.HTTPException:
                pass

    async def _alert(self, guild: discord.Guild, cfg, count: int):
        if not cfg["log_channel"]:
            return
        ch = guild.get_channel(cfg["log_channel"])
        if ch:
            await ch.send(embed=embed(
                "🚨 Raid detectado",
                f"**{count}** entradas em {WINDOW}s. Lockdown de **{LOCKDOWN}s**: novos membros serão expulsos.",
                0xED4245))


async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
