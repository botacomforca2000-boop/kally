import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from database import DB

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kally")

EXTENSIONS = [
    "cogs.general", "cogs.config", "cogs.moderation", "cogs.logs", "cogs.antiraid",
    "cogs.levels", "cogs.economy", "cogs.tickets", "cogs.vip", "cogs.insta",
]


class Kally(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # ative "Server Members Intent" no Developer Portal
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.db = DB()
        self.tree.on_error = self.on_tree_error

    async def setup_hook(self):
        await self.db.connect()
        for ext in EXTENSIONS:
            await self.load_extension(ext)
            log.info("Carregado: %s", ext)
        await self.tree.sync()

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/ajuda • kally.me"))
        log.info("Online como %s", self.user)

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "❌ Você não tem permissão para usar este comando."
        elif isinstance(error, app_commands.BotMissingPermissions):
            msg = "❌ Eu não tenho permissão suficiente para fazer isso."
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Calma! Tente de novo em **{error.retry_after:.0f}s**."
        else:
            log.exception("Erro no comando", exc_info=error)
            msg = "⚠️ Ocorreu um erro inesperado."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Defina DISCORD_TOKEN no arquivo .env")
    async with Kally() as bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
