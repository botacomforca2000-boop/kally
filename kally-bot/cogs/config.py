import discord
from discord import app_commands
from discord.ext import commands

from utils import embed


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    config = app_commands.Group(
        name="config", description="Configura a Kally no servidor",
        guild_only=True, default_permissions=discord.Permissions(administrator=True),
    )

    async def _set(self, i, key, value, text):
        await self.bot.db.set_config(i.guild_id, key, value)
        await i.response.send_message(f"✅ {text}", ephemeral=True)

    @config.command(name="logs", description="Define o canal de logs")
    async def logs(self, i: discord.Interaction, canal: discord.TextChannel):
        await self._set(i, "log_channel", canal.id, f"Canal de logs: {canal.mention}")

    @config.command(name="niveis", description="Define o canal dos avisos de level up")
    async def niveis(self, i: discord.Interaction, canal: discord.TextChannel):
        await self._set(i, "level_channel", canal.id, f"Canal de level up: {canal.mention}")

    @config.command(name="vip", description="Define o cargo VIP")
    async def vip(self, i: discord.Interaction, cargo: discord.Role):
        await self._set(i, "vip_role", cargo.id, f"Cargo VIP: {cargo.mention}")

    @config.command(name="insta", description="Define o canal do Instagram")
    async def insta(self, i: discord.Interaction, canal: discord.TextChannel):
        await self._set(i, "insta_channel", canal.id, f"Canal do Instagram: {canal.mention}")

    @config.command(name="ticket", description="Define categoria e cargo de staff dos tickets")
    async def ticket(self, i: discord.Interaction, categoria: discord.CategoryChannel, staff: discord.Role):
        await self.bot.db.set_config(i.guild_id, "ticket_category", categoria.id)
        await self.bot.db.set_config(i.guild_id, "ticket_staff_role", staff.id)
        await i.response.send_message(f"✅ Tickets em **{categoria.name}**, staff: {staff.mention}", ephemeral=True)

    @config.command(name="antiraid", description="Liga/desliga o anti-raid")
    @app_commands.describe(ativo="Ativar?", limite="Entradas em 10s para disparar (padrão 5)")
    async def antiraid(self, i: discord.Interaction, ativo: bool, limite: app_commands.Range[int, 2, 50] = 5):
        await self.bot.db.set_config(i.guild_id, "antiraid_enabled", int(ativo))
        await self.bot.db.set_config(i.guild_id, "antiraid_threshold", limite)
        await i.response.send_message(f"✅ Anti-raid {'**ativado**' if ativo else '**desativado**'} (limite: {limite} entradas/10s)", ephemeral=True)

    @config.command(name="ver", description="Mostra a configuração atual")
    async def ver(self, i: discord.Interaction):
        c = await self.bot.db.get_config(i.guild_id)

        def ch(v): return f"<#{v}>" if v else "—"
        def ro(v): return f"<@&{v}>" if v else "—"

        e = embed("⚙️ Configuração da Kally")
        e.add_field(name="Logs", value=ch(c["log_channel"]))
        e.add_field(name="Level up", value=ch(c["level_channel"]))
        e.add_field(name="Instagram", value=ch(c["insta_channel"]))
        e.add_field(name="Cargo VIP", value=ro(c["vip_role"]))
        e.add_field(name="Tickets (categoria)", value=ch(c["ticket_category"]))
        e.add_field(name="Tickets (staff)", value=ro(c["ticket_staff_role"]))
        e.add_field(name="Anti-raid", value=f"{'ON' if c['antiraid_enabled'] else 'OFF'} • limite {c['antiraid_threshold']}")
        await i.response.send_message(embed=e, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Config(bot))
