import discord

from discord.ext import commands
from helpers import checks
from tinydb import Query
from typing import Optional


class Notification(commands.Cog):
    """Notification for greeting people. Manage Guild permission is needed to use this category."""
    def __init__(self, bot):
        self.bot = bot

    def get_notification(self, guild_id):
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == guild_id) or {}
        
        greeting = guild.get("greeting_channel") or None
        farewelling = guild.get("farewelling_channel") or None
        
        return greeting, farewelling

    def set_greet(self, guild_id, channel_id):
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == guild_id) or {}
        self.bot.database.guilds.upsert(
            {**guild, "id": guild_id, "greeting_channel": channel_id},
            Guild.id == guild_id
        )
        
    def set_farewell(self, guild_id, channel_id):
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == guild_id) or {}
        self.bot.database.guilds.upsert(
            {**guild, "id": guild_id, "farewelling_channel": channel_id},
            Guild.id == guild_id
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        greeting, _ = self.get_notification(member.guild.id)
        channel = member.guild.get_channel(greeting)
        if channel:
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Greetings {member.mention} and welcome to the server!",
                color=0x5865F2
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Make sure to read the rules and enjoy your stay!")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        _, farewelling = self.get_notification(member.guild.id)
        channel = member.guild.get_channel(farewelling)
        if channel:
            embed = discord.Embed(
                title="Goodbye!",
                description=f"Goodbye {member.mention}, hope you had fun with the server!",
                color=0x5865F2
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            await channel.send(embed=embed)

    @commands.hybrid_group(fallback="channel")
    @commands.guild_only()
    @checks.is_manager()
    async def greeting(self, ctx: commands.Context):
        """View the greeting channel."""
        greeting, _ = self.get_notification(ctx.guild.id)
        await ctx.send(f"Greeting new people at <#{greeting}>!")

    @greeting.command()
    @commands.guild_only()
    @checks.is_manager()
    async def join(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Set the greeting channel."""
        if channel is None:
            channel = ctx.channel

        self.set_greet(ctx.guild.id, channel.id)
        await ctx.send(f"Greeting channel was set to <#{channel.id}>.")

    @greeting.command()
    @commands.guild_only()
    @checks.is_manager()
    async def reset(self, ctx: commands.Context):
        """Reset the greeting channel."""
        self.set_greet(ctx.guild.id, None)
        await ctx.send("Greeting channel was reset.")

    @commands.hybrid_group(fallback="channel")
    @commands.guild_only()
    @checks.is_manager()
    async def farewelling(self, ctx: commands.Context):
        """View the farewelling channel."""
        _, farewelling = self.get_notification(ctx.guild.id)
        await ctx.send(f"Farewelling people at <#{farewelling}>!")

    @farewelling.command()
    @commands.guild_only()
    @checks.is_manager()
    async def leave(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Set the farewelling channel."""
        if channel is None:
            channel = ctx.channel

        self.set_farewell(ctx.guild.id, channel.id)
        await ctx.send(f"Farewelling channel was set to <#{channel.id}>.")

    @farewelling.command()
    @commands.guild_only()
    @checks.is_manager()
    async def reset(self, ctx: commands.Context):
        """Reset the farewelling channel."""
        self.set_farewell(ctx.guild.id, None)
        await ctx.send("Farewelling channel was reset.")


async def setup(bot):
    await bot.add_cog(Notification(bot))