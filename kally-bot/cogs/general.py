from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import embed


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Mostra a latência da Kally")
    async def ping(self, i: discord.Interaction):
        await i.response.send_message(f"🏓 Pong! `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command(name="avatar", description="Mostra o avatar de um membro")
    async def avatar(self, i: discord.Interaction, membro: Optional[discord.Member] = None):
        membro = membro or i.user
        e = embed(f"Avatar de {membro.display_name}")
        e.set_image(url=membro.display_avatar.url)
        await i.response.send_message(embed=e)

    @app_commands.command(name="userinfo", description="Informações de um membro")
    @app_commands.guild_only()
    async def userinfo(self, i: discord.Interaction, membro: Optional[discord.Member] = None):
        m = membro or i.user
        e = embed(str(m))
        e.set_thumbnail(url=m.display_avatar.url)
        e.add_field(name="ID", value=m.id)
        e.add_field(name="Conta criada", value=discord.utils.format_dt(m.created_at, "R"))
        e.add_field(name="Entrou no servidor", value=discord.utils.format_dt(m.joined_at, "R") if m.joined_at else "?")
        roles = [r.mention for r in reversed(m.roles) if r != i.guild.default_role][:10]
        e.add_field(name="Cargos", value=" ".join(roles) or "Nenhum", inline=False)
        await i.response.send_message(embed=e)

    @app_commands.command(name="serverinfo", description="Informações do servidor")
    @app_commands.guild_only()
    async def serverinfo(self, i: discord.Interaction):
        g = i.guild
        e = embed(g.name)
        if g.icon:
            e.set_thumbnail(url=g.icon.url)
        e.add_field(name="Dono", value=g.owner.mention if g.owner else "?")
        e.add_field(name="Membros", value=g.member_count)
        e.add_field(name="Canais", value=len(g.channels))
        e.add_field(name="Cargos", value=len(g.roles))
        e.add_field(name="Criado", value=discord.utils.format_dt(g.created_at, "R"))
        await i.response.send_message(embed=e)

    @app_commands.command(name="ajuda", description="Lista todos os comandos da Kally")
    async def ajuda(self, i: discord.Interaction):
        e = embed("💜 Kally — Comandos", "Configure tudo com `/config`.")
        e.add_field(name="🔧 Geral", value="`/ping` `/avatar` `/userinfo` `/serverinfo`", inline=False)
        e.add_field(name="🛡️ Moderação", value="`/ban` `/kick` `/timeout` `/untimeout` `/clear` `/warn` `/warns` `/slowmode`", inline=False)
        e.add_field(name="📈 Níveis", value="`/rank` `/top`", inline=False)
        e.add_field(name="💰 Economia", value="`/saldo` `/daily` `/trabalhar` `/apostar` `/pagar` `/ricos`", inline=False)
        e.add_field(name="🎫 Tickets", value="`/ticket painel`", inline=False)
        e.add_field(name="👑 VIP", value="`/vip dar` `/vip remover` `/vip lista` `/vip ver`", inline=False)
        e.add_field(name="📸 Instagram", value="`/insta postar` `/insta perfil`", inline=False)
        e.add_field(name="🚨 Anti-raid & Logs", value="`/config antiraid` `/config logs`", inline=False)
        e.add_field(name="⚙️ Configuração (admin)", value="`/config ver` `/config logs` `/config niveis` `/config vip` `/config insta` `/config ticket` `/config antiraid`", inline=False)
        await i.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(General(bot))
