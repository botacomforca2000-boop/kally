import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from utils import embed


class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="kally:ticket:close")
    async def close(self, i: discord.Interaction, button: discord.ui.Button):
        topic = i.channel.topic or ""
        owner_id = int(topic.split(":")[1]) if topic.startswith("ticket:") else None
        if i.user.id != owner_id and not i.user.guild_permissions.manage_channels:
            return await i.response.send_message("❌ Só quem abriu ou a staff pode fechar.", ephemeral=True)
        await i.response.send_message("🔒 Fechando em 5 segundos...")
        await asyncio.sleep(5)
        await i.channel.delete(reason=f"Ticket fechado por {i.user}")


class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir ticket", emoji="🎫", style=discord.ButtonStyle.primary, custom_id="kally:ticket:open")
    async def open(self, i: discord.Interaction, button: discord.ui.Button):
        guild = i.guild
        existing = discord.utils.get(guild.text_channels, topic=f"ticket:{i.user.id}")
        if existing:
            return await i.response.send_message(f"Você já tem um ticket: {existing.mention}", ephemeral=True)

        cfg = await i.client.db.get_config(guild.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        staff = guild.get_role(cfg["ticket_staff_role"]) if cfg["ticket_staff_role"] else None
        if staff:
            overwrites[staff] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        category = guild.get_channel(cfg["ticket_category"]) if cfg["ticket_category"] else None

        try:
            ch = await guild.create_text_channel(
                f"ticket-{i.user.name}"[:90], category=category, overwrites=overwrites, topic=f"ticket:{i.user.id}")
        except discord.Forbidden:
            return await i.response.send_message("❌ Não tenho permissão para criar canais.", ephemeral=True)

        await ch.send(
            content=f"{i.user.mention} {staff.mention if staff else ''}",
            embed=embed("🎫 Ticket aberto", "Descreva seu problema e aguarde a staff."),
            view=TicketControls(),
        )
        await i.response.send_message(f"✅ Ticket criado: {ch.mention}", ephemeral=True)


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketPanel())
        self.bot.add_view(TicketControls())

    ticket = app_commands.Group(
        name="ticket", description="Sistema de tickets", guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True))

    @ticket.command(name="painel", description="Envia o painel de tickets neste canal")
    async def painel(self, i: discord.Interaction):
        await i.channel.send(
            embed=embed("🎫 Suporte", "Clique no botão abaixo para abrir um ticket."), view=TicketPanel())
        await i.response.send_message("✅ Painel enviado.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
