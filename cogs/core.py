import discord

from discord import Embed
from discord.ext import commands
from helpers import checks, constants
from tinydb import Query


class Core(commands.Cog):
    """Core bot features. Such as the bot's basic configuration."""
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(aliases=("prefixes",), fallback="list")
    @commands.guild_only()
    async def prefix(self, ctx: commands.Context):
        """Check the bot's available prefixes"""
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == ctx.guild.id) or {}

        prefixes = guild.get("prefixes", [])

        embed = Embed(
            color=0x5865F2
        )

        embed.add_field(
            name="Available Prefixes",
            value="\n".join(f"{p}" for p in prefixes),
            inline=False
        )

        await ctx.send(embed=embed)

    @prefix.command()
    @commands.guild_only()
    @checks.is_manager()
    async def add(self, ctx: commands.Context, prefix: str):
        """Add a prefix in the custom prefix list. Manage Guild permission is needed to use this command.    """
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == ctx.guild.id) or {}

        prefixes = guild.get("prefixes", [])

        if prefix in prefixes:
            return await ctx.send(f"`{prefix}` has already been added!")

        prefixes.append(prefix)

        self.bot.database.guilds.upsert(
            {**guild, "id": ctx.guild.id, "prefixes": prefixes},
            Guild.id == ctx.guild.id
        )

        await ctx.send(f"`{prefix}` has been added to the custom prefix list.")

    @prefix.command()
    @commands.guild_only()
    @checks.is_manager()
    async def remove(self, ctx: commands.Context, prefix: str):
        """Remove a prefix in the custom prefix list. Manage Guild permission is needed to use this command."""
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == ctx.guild.id) or {}

        prefixes = guild.get("prefixes", [])

        if not (prefix in prefixes):
            return await ctx.send(f"`{prefix}` not found!")

        prefixes.remove(prefix)

        self.bot.database.guilds.upsert(
            {**guild, "id": ctx.guild.id, "prefixes": prefixes},
            Guild.id == ctx.guild.id
        )

        await ctx.send(f"`{prefix}` has been removed from the custom prefix list.")

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        """Bot latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! **{latency} ms**")


async def setup(bot):
    await bot.add_cog(Core(bot))