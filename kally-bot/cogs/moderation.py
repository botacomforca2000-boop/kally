import datetime
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import embed


def can_act(i: discord.Interaction, target: discord.Member) -> bool:
    if target == i.guild.owner or target.id == i.user.id:
        return False
    if i.user == i.guild.owner:
        return True
    return target.top_role < i.user.top_role


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _deny(self, i):
        await i.response.send_message("❌ Você não pode punir esse membro (hierarquia).", ephemeral=True)

    @app_commands.command(name="ban", description="Bane um membro")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    async def ban(self, i: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
        if not can_act(i, membro):
            return await self._deny(i)
        try:
            await membro.ban(reason=f"{i.user}: {motivo}", delete_message_days=0)
        except discord.Forbidden:
            return await self._deny(i)
        await i.response.send_message(embed=embed("🔨 Banido", f"{membro} foi banido.\n**Motivo:** {motivo}"))

    @app_commands.command(name="kick", description="Expulsa um membro")
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    async def kick(self, i: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
        if not can_act(i, membro):
            return await self._deny(i)
        try:
            await membro.kick(reason=f"{i.user}: {motivo}")
        except discord.Forbidden:
            return await self._deny(i)
        await i.response.send_message(embed=embed("👢 Expulso", f"{membro} foi expulso.\n**Motivo:** {motivo}"))

    @app_commands.command(name="timeout", description="Silencia um membro por X minutos")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def timeout(self, i: discord.Interaction, membro: discord.Member,
                      minutos: app_commands.Range[int, 1, 40320], motivo: str = "Sem motivo"):
        if not can_act(i, membro):
            return await self._deny(i)
        try:
            await membro.timeout(datetime.timedelta(minutes=minutos), reason=f"{i.user}: {motivo}")
        except discord.Forbidden:
            return await self._deny(i)
        await i.response.send_message(embed=embed("🔇 Timeout", f"{membro.mention} silenciado por **{minutos} min**.\n**Motivo:** {motivo}"))

    @app_commands.command(name="untimeout", description="Remove o timeout de um membro")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    async def untimeout(self, i: discord.Interaction, membro: discord.Member):
        await membro.timeout(None)
        await i.response.send_message(f"🔊 {membro.mention} não está mais silenciado.")

    @app_commands.command(name="clear", description="Apaga mensagens do canal")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    async def clear(self, i: discord.Interaction, quantidade: app_commands.Range[int, 1, 100]):
        await i.response.defer(ephemeral=True)
        deleted = await i.channel.purge(limit=quantidade)
        await i.followup.send(f"🧹 {len(deleted)} mensagens apagadas.", ephemeral=True)

    @app_commands.command(name="slowmode", description="Define o modo lento do canal (0 desliga)")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.bot_has_permissions(manage_channels=True)
    async def slowmode(self, i: discord.Interaction, segundos: app_commands.Range[int, 0, 21600]):
        await i.channel.edit(slowmode_delay=segundos)
        await i.response.send_message(f"🐢 Modo lento: **{segundos}s**")

    @app_commands.command(name="warn", description="Dá um aviso a um membro")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, i: discord.Interaction, membro: discord.Member, motivo: str):
        if not can_act(i, membro):
            return await self._deny(i)
        await self.bot.db.execute(
            "INSERT INTO warns(guild_id,user_id,mod_id,reason,created_at) VALUES(?,?,?,?,?)",
            i.guild_id, membro.id, i.user.id, motivo, int(time.time()))
        await i.response.send_message(embed=embed("⚠️ Aviso", f"{membro.mention} foi avisado.\n**Motivo:** {motivo}"))

    @app_commands.command(name="warns", description="Lista os avisos de um membro")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warns(self, i: discord.Interaction, membro: discord.Member):
        rows = await self.bot.db.fetchall(
            "SELECT * FROM warns WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 15", i.guild_id, membro.id)
        if not rows:
            return await i.response.send_message("✅ Esse membro não tem avisos.", ephemeral=True)
        desc = "\n".join(f"`#{r['id']}` <t:{r['created_at']}:d> — {r['reason']} (por <@{r['mod_id']}>)" for r in rows)
        await i.response.send_message(embed=embed(f"Avisos de {membro.display_name}", desc), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
