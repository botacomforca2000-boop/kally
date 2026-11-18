import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils import embed


class VIP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.expire_loop.start()

    async def cog_unload(self):
        self.expire_loop.cancel()

    vip = app_commands.Group(
        name="vip", description="Sistema de VIPs", guild_only=True,
        default_permissions=discord.Permissions(manage_roles=True))

    async def _role(self, guild):
        cfg = await self.bot.db.get_config(guild.id)
        return guild.get_role(cfg["vip_role"]) if cfg["vip_role"] else None

    @vip.command(name="dar", description="Dá VIP a um membro por X dias")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def dar(self, i: discord.Interaction, membro: discord.Member, dias: app_commands.Range[int, 1, 3650]):
        role = await self._role(i.guild)
        if not role:
            return await i.response.send_message("❌ Defina o cargo com `/config vip`.", ephemeral=True)
        row = await self.bot.db.fetchone("SELECT expires_at FROM vips WHERE guild_id=? AND user_id=?", i.guild_id, membro.id)
        base = max(row["expires_at"], int(time.time())) if row else int(time.time())
        expires = base + dias * 86400
        await self.bot.db.execute(
            "INSERT INTO vips(guild_id,user_id,expires_at) VALUES(?,?,?) "
            "ON CONFLICT(guild_id,user_id) DO UPDATE SET expires_at=excluded.expires_at",
            i.guild_id, membro.id, expires)
        try:
            await membro.add_roles(role, reason="VIP concedido")
        except discord.Forbidden:
            return await i.response.send_message("❌ Não consigo dar esse cargo (hierarquia).", ephemeral=True)
        await i.response.send_message(f"👑 {membro.mention} é VIP até <t:{expires}:F> (<t:{expires}:R>).")

    @vip.command(name="remover", description="Remove o VIP de um membro")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remover(self, i: discord.Interaction, membro: discord.Member):
        await self.bot.db.execute("DELETE FROM vips WHERE guild_id=? AND user_id=?", i.guild_id, membro.id)
        role = await self._role(i.guild)
        if role and role in membro.roles:
            await membro.remove_roles(role, reason="VIP removido")
        await i.response.send_message(f"✅ VIP removido de {membro.mention}.")

    @vip.command(name="lista", description="Lista os VIPs ativos")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def lista(self, i: discord.Interaction):
        rows = await self.bot.db.fetchall("SELECT user_id, expires_at FROM vips WHERE guild_id=? ORDER BY expires_at LIMIT 25", i.guild_id)
        if not rows:
            return await i.response.send_message("Nenhum VIP ativo.", ephemeral=True)
        desc = "\n".join(f"<@{r['user_id']}> — expira <t:{r['expires_at']}:R>" for r in rows)
        await i.response.send_message(embed=embed("👑 VIPs ativos", desc), ephemeral=True)

    @app_commands.command(name="vipinfo", description="Veja seu VIP")
    @app_commands.guild_only()
    async def vipinfo(self, i: discord.Interaction):
        row = await self.bot.db.fetchone("SELECT expires_at FROM vips WHERE guild_id=? AND user_id=?", i.guild_id, i.user.id)
        if not row:
            return await i.response.send_message("Você não é VIP.", ephemeral=True)
        await i.response.send_message(f"👑 Seu VIP expira <t:{row['expires_at']}:R>.", ephemeral=True)

    @tasks.loop(minutes=5)
    async def expire_loop(self):
        rows = await self.bot.db.fetchall("SELECT guild_id, user_id FROM vips WHERE expires_at<=?", int(time.time()))
        for r in rows:
            guild = self.bot.get_guild(r["guild_id"])
            if guild:
                role = await self._role(guild)
                member = guild.get_member(r["user_id"])
                if role and member and role in member.roles:
                    try:
                        await member.remove_roles(role, reason="VIP expirado")
                    except discord.HTTPException:
                        continue
            await self.bot.db.execute("DELETE FROM vips WHERE guild_id=? AND user_id=?", r["guild_id"], r["user_id"])

    @expire_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(VIP(bot))
