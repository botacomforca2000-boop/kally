import discord

COLOR = 0xB388FF


def embed(title: str | None = None, description: str | None = None, color: int = COLOR) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)
