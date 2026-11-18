import discord
from discord.ext import commands

from utils import embed


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, guild: discord.Guild, e: discord.Embed):
        cfg = await self.bot.db.get_config(guild.id)
        if not cfg["log_channel"]:
            return
        ch = guild.get_channel(cfg["log_channel"])
        if ch:
            try:
                await ch.send(embed=e)
            except discord.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, m: discord.Member):
        e = embed("📥 Membro entrou", f"{m.mention} (`{m.id}`)\nConta criada {discord.utils.format_dt(m.created_at, 'R')}", 0x57F287)
        await self.send(m.guild, e)

    @commands.Cog.listener()
    async def on_member_remove(self, m: discord.Member):
        await self.send(m.guild, embed("📤 Membro saiu", f"{m} (`{m.id}`)", 0xED4245))

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self.send(guild, embed("🔨 Banimento", f"{user} (`{user.id}`)", 0xED4245))

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self.send(guild, embed("♻️ Desbanimento", f"{user} (`{user.id}`)", 0x57F287))

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if not msg.guild or msg.author.bot:
            return
        e = embed("🗑️ Mensagem apagada", f"**Autor:** {msg.author.mention}\n**Canal:** {msg.channel.mention}", 0xFEE75C)
        if msg.content:
            e.add_field(name="Conteúdo", value=msg.content[:1000], inline=False)
        await self.send(msg.guild, e)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        e = embed("✏️ Mensagem editada", f"**Autor:** {before.author.mention}\n**Canal:** {before.channel.mention}\n[Ir para a mensagem]({after.jump_url})", 0x5865F2)
        e.add_field(name="Antes", value=(before.content or "—")[:1000], inline=False)
        e.add_field(name="Depois", value=(after.content or "—")[:1000], inline=False)
        await self.send(before.guild, e)


async def setup(bot):
    await bot.add_cog(Logs(bot))
