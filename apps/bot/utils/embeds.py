import discord

def error_embed(description: str, *, title: str = "Error") -> discord.Embed:
	embed = discord.Embed(title=title, description=description, color=discord.Color.red())
	return embed

def success_embed(description: str, *, title: str = "Success") -> discord.Embed:
	embed = discord.Embed(title=title, description=description, color=discord.Color.green())
	return embed

def info_embed(description: str, *, title: str = "Info") -> discord.Embed:
	embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
	return embed
