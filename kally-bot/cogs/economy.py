import random
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import embed

DAILY = 500
COIN = "🪙"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def balance(self, gid: int, uid: int) -> int:
        row = await self.bot.db.fetchone("SELECT balance FROM economy WHERE guild_id=? AND user_id=?", gid, uid)
        return row["balance"] if row else 0

    async def add(self, gid: int, uid: int, amount: int):
        await self.bot.db.execute(
            "INSERT INTO economy(guild_id,user_id,balance) VALUES(?,?,?) "
            "ON CONFLICT(guild_id,user_id) DO UPDATE SET balance=balance+?",
            gid, uid, amount, amount)

    @app_commands.command(name="saldo", description="Mostra seu saldo")
    @app_commands.guild_only()
    async def saldo(self, i: discord.Interaction, membro: Optional[discord.Member] = None):
        m = membro or i.user
        await i.response.send_message(f"{COIN} **{m.display_name}** tem **{await self.balance(i.guild_id, m.id):,}** moedas.")

    @app_commands.command(name="daily", description="Resgate sua recompensa diária")
    @app_commands.guild_only()
    async def daily(self, i: discord.Interaction):
        row = await self.bot.db.fetchone("SELECT last_daily FROM economy WHERE guild_id=? AND user_id=?", i.guild_id, i.user.id)
        last, now = (row["last_daily"] if row else 0), time.time()
        if now - last < 86400:
            return await i.response.send_message(f"⏳ Volte <t:{int(last + 86400)}:R>.", ephemeral=True)
        await self.add(i.guild_id, i.user.id, DAILY)
        await self.bot.db.execute("UPDATE economy SET last_daily=? WHERE guild_id=? AND user_id=?", now, i.guild_id, i.user.id)
        await i.response.send_message(f"🎁 Você recebeu **{DAILY}** {COIN}!")

    @app_commands.command(name="trabalhar", description="Trabalhe para ganhar moedas (1x por hora)")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 3600, key=lambda i: (i.guild_id, i.user.id))
    async def trabalhar(self, i: discord.Interaction):
        jobs = ["programou um bot", "entregou pizzas", "moderou um servidor", "editou vídeos", "fez freelas de design"]
        gain = random.randint(80, 250)
        await self.add(i.guild_id, i.user.id, gain)
        await i.response.send_message(f"💼 Você {random.choice(jobs)} e ganhou **{gain}** {COIN}.")

    @app_commands.command(name="apostar", description="Aposte moedas (chance de 45%)")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
    async def apostar(self, i: discord.Interaction, valor: app_commands.Range[int, 1, 100000]):
        if await self.balance(i.guild_id, i.user.id) < valor:
            return await i.response.send_message("❌ Saldo insuficiente.", ephemeral=True)
        if random.random() < 0.45:
            await self.add(i.guild_id, i.user.id, valor)
            await i.response.send_message(f"🎰 Você **ganhou** {valor} {COIN}!")
        else:
            await self.add(i.guild_id, i.user.id, -valor)
            await i.response.send_message(f"💸 Você **perdeu** {valor} {COIN}.")

    @app_commands.command(name="pagar", description="Envia moedas para outro membro")
    @app_commands.guild_only()
    async def pagar(self, i: discord.Interaction, membro: discord.Member, valor: app_commands.Range[int, 1, 1000000]):
        if membro.bot or membro.id == i.user.id:
            return await i.response.send_message("❌ Destinatário inválido.", ephemeral=True)
        if await self.balance(i.guild_id, i.user.id) < valor:
            return await i.response.send_message("❌ Saldo insuficiente.", ephemeral=True)
        await self.add(i.guild_id, i.user.id, -valor)
        await self.add(i.guild_id, membro.id, valor)
        await i.response.send_message(f"💸 {i.user.mention} enviou **{valor}** {COIN} para {membro.mention}.")

    @app_commands.command(name="ricos", description="Ranking dos mais ricos")
    @app_commands.guild_only()
    async def ricos(self, i: discord.Interaction):
        rows = await self.bot.db.fetchall(
            "SELECT user_id, balance FROM economy WHERE guild_id=? ORDER BY balance DESC LIMIT 10", i.guild_id)
        if not rows:
            return await i.response.send_message("Ninguém tem moedas ainda.", ephemeral=True)
        desc = "\n".join(f"`{n + 1}.` <@{r['user_id']}> — {r['balance']:,} {COIN}" for n, r in enumerate(rows))
        await i.response.send_message(embed=embed("💰 Mais ricos", desc))


async def setup(bot):
    await bot.add_cog(Economy(bot))
