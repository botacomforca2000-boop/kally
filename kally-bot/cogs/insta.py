import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import embed


class LikeView(discord.ui.View):
    def __init__(self, likes: int = 0):
        super().__init__(timeout=None)
        self.like.label = str(likes)

    @discord.ui.button(emoji="❤️", label="0", style=discord.ButtonStyle.secondary, custom_id="kally:insta:like")
    async def like(self, i: discord.Interaction, button: discord.ui.Button):
        db = i.client.db
        mid = i.message.id
        if not await db.fetchone("SELECT 1 FROM insta_posts WHERE message_id=?", mid):
            return await i.response.send_message("Post não encontrado.", ephemeral=True)
        liked = await db.fetchone("SELECT 1 FROM insta_likes WHERE message_id=? AND user_id=?", mid, i.user.id)
        if liked:
            await db.execute("DELETE FROM insta_likes WHERE message_id=? AND user_id=?", mid, i.user.id)
        else:
            await db.execute("INSERT INTO insta_likes(message_id,user_id) VALUES(?,?)", mid, i.user.id)
        count = (await db.fetchone("SELECT COUNT(*) c FROM insta_likes WHERE message_id=?", mid))["c"]
        await i.response.edit_message(view=LikeView(count))


class Insta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(LikeView())

    insta = app_commands.Group(name="insta", description="Instagram do servidor", guild_only=True)

    @insta.command(name="postar", description="Publica uma foto no feed do servidor")
    @app_commands.describe(foto="A imagem", legenda="Legenda do post")
    @app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def postar(self, i: discord.Interaction, foto: discord.Attachment, legenda: Optional[str] = None):
        if not (foto.content_type or "").startswith("image/"):
            return await i.response.send_message("❌ Envie uma imagem.", ephemeral=True)
        cfg = await self.bot.db.get_config(i.guild_id)
        channel = i.guild.get_channel(cfg["insta_channel"]) if cfg["insta_channel"] else i.channel

        await i.response.defer(ephemeral=True)
        file = await foto.to_file()
        e = embed(description=legenda or "")
        e.set_author(name=f"@{i.user.name}", icon_url=i.user.display_avatar.url)
        e.set_image(url=f"attachment://{file.filename}")
        e.timestamp = discord.utils.utcnow()
        msg = await channel.send(embed=e, file=file, view=LikeView(0))
        await self.bot.db.execute(
            "INSERT INTO insta_posts(message_id,guild_id,user_id,created_at) VALUES(?,?,?,?)",
            msg.id, i.guild_id, i.user.id, int(time.time()))
        await i.followup.send(f"✅ Publicado: {msg.jump_url}", ephemeral=True)

    @insta.command(name="perfil", description="Mostra o perfil de Instagram de um membro")
    async def perfil(self, i: discord.Interaction, membro: Optional[discord.Member] = None):
        m = membro or i.user
        posts = await self.bot.db.fetchone(
            "SELECT COUNT(*) c FROM insta_posts WHERE guild_id=? AND user_id=?", i.guild_id, m.id)
        likes = await self.bot.db.fetchone(
            "SELECT COUNT(*) c FROM insta_likes WHERE message_id IN "
            "(SELECT message_id FROM insta_posts WHERE guild_id=? AND user_id=?)", i.guild_id, m.id)
        e = embed(f"📸 @{m.name}")
        e.set_thumbnail(url=m.display_avatar.url)
        e.add_field(name="Posts", value=posts["c"])
        e.add_field(name="Curtidas recebidas", value=likes["c"])
        await i.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(Insta(bot))
