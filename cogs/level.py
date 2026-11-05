import discord
import random

from discord import Embed
from discord.ext import commands
from helpers import checks, paginator, trackers
from tinydb import Query
from typing import Optional

OPTION = {
    "cooldown": (int, "whole number (e.g. 60)"),
    "min_xp": (int, "whole number (e.g. 10)"),
    "max_xp": (int, "whole number (e.g. 25)"),
    "base_xp": (int, "whole number (e.g. 100)"),
    "growth_rate": (float, "decimal (e.g. 1.5)")
}
DEFAULT = {
    "cooldown": 60,
    "min_xp": 10,
    "max_xp": 20,
    "base_xp": 100,
    "growth_rate": 1.5
}


class Level(commands.Cog):
    """Level and Experience. Support server-wide leaderboard and level rewards."""
    def __init__(self, bot):
        self.bot = bot
        self.tracker = trackers.CooldownTracker()

    def get_stat(self, guild_id, user_id) -> tuple[int, int]:
        Member = Query()
        member = self.bot.database.members.get(
            (Member.guild_id == guild_id) &
            (Member.user_id == user_id)
        ) or {}

        return (member.get("level", 1), member.get("xp", 0))

    def set_stat(self, guild_id, user_id, stats):
        Member = Query()
        member = self.bot.database.members.get(
            (Member.guild_id == guild_id) &
            (Member.user_id == user_id)
        ) or {}
        
        level, xp = stats
        
        member.update({"level":level, "xp":xp})

        self.bot.database.members.upsert(
            {**member, "guild_id": guild_id, "user_id": user_id},
            (Member.guild_id == guild_id) &
            (Member.user_id == user_id)
        )

    def add_xp(self, guild_id, user_id, amount, configuration):
        leveled_up = False
        Member = Query()
        member = self.bot.database.members.get(
            (Member.guild_id == guild_id) &
            (Member.user_id == user_id)
        ) or {}

        member["xp"] = member.get("xp", 0) + amount
        
        required = configuration["base_xp"]*member.get("level", 1)**configuration["growth_rate"]
        if member["xp"] >= required:
            member["level"] = member.get("level", 1) + 1
            leveled_up = True

        self.bot.database.members.upsert(
            {**member, "guild_id": guild_id, "user_id": user_id},
            (Member.guild_id == guild_id) &
            (Member.user_id == user_id)
        )
        
        return leveled_up, member.get("xp", 0), member.get("level", 1)

    def get_configuration(self, guild_id) -> dict:
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == guild_id) or {}
        return guild.get("level_configuration") or DEFAULT

    def set_configuration(self, guild_id, setting, value):
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == guild_id) or {}
        level_configuration = guild.get("level_configuration", {})
        
        level_configuration.update({setting:value})
        
        self.bot.database.guilds.upsert(
            {**guild, "level_configuration": level_configuration, "id": guild_id},
            Guild.id == guild_id
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return

        level_configuration = self.get_configuration(message.guild.id)

        if self.tracker.is_on_cooldown(
            message.guild.id,
            message.author.id,
            level_configuration["cooldown"]
        ):
            return

        xp_gain = random.randint(
            level_configuration["min_xp"],
            level_configuration["max_xp"]
        )

        leveled_up, xp, level = self.add_xp(
            message.guild.id,
            message.author.id,
            xp_gain,
            level_configuration
        )

        if leveled_up:
            await message.channel.send(
                f"{message.author.mention} you have reached level {level}!"
            )

            Guild = Query()
            guild = self.bot.database.guilds.get(
                Guild.id == message.guild.id
            ) or {}

            level_roles = guild.get("level_roles", {})
            reward_roles = level_roles.get(str(level), [])

            for role_id in reward_roles:
                role = message.guild.get_role(role_id)

                if role and role not in message.author.roles:
                    await message.author.add_roles(
                        role,
                        reason=f"Reached level {level}"
                    )

                    await message.channel.send(
                        f"You have gained {role.mention}!",
                        allowed_mentions=discord.AllowedMentions.none()
                    )

    @commands.hybrid_group(aliases=("level", "experience",), fallback="get")
    @commands.guild_only()
    async def xp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Check your current experience. Mention a member to check theirs."""
        if user is None:
            user = ctx.author

        if user.bot:
            await ctx.send("The mentioned member is a bot!")
            return

        level, xp = self.get_stat(ctx.guild.id, user.id)
        level_configuration = self.get_configuration(ctx.guild.id)
        
        embed = Embed(
            color = 0x5865F2
        )
        
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        
        embed.add_field(
            name="Level",
            value=level,
            inline=True
        )
        embed.add_field(
            name="XP",
            value=f"{xp}/{round(level_configuration.get('base_xp')*level**level_configuration.get('growth_rate'))}",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @xp.command(aliases=("lb",))
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context, page: int = 1):
        """Show the server XP leaderboard."""
        Member = Query()
        members = self.bot.database.members.search(
            Member.guild_id == ctx.guild.id
        )

        members.sort(
            key=lambda m: (m.get("level", 1), m.get("xp", 0)),
            reverse=True
        )

        if not members:
            return await ctx.send("There are no members on the leaderboard yet.")

        pages = []

        for page_index in range(0, len(members), 10):
            embed = discord.Embed(
                title=f"XP Leaderboard in {ctx.guild.name}",
                color=0x5865F2
            )

            description = []

            for index, member in enumerate(
                members[page_index:page_index + 10],
                start=page_index + 1
            ):
                user = ctx.guild.get_member(member["user_id"])

                if user is None:
                    continue

                description.append(
                    f"**#{index}** {user.mention} — "
                    f"Level **{member.get('level', 1)}** "
                    f"({member.get('xp', 0):,} XP)"
                )

            embed.description = "\n".join(description) or "No members found."
            embed.set_footer(text=f"Page {len(pages) + 1}")

            pages.append(embed)

        if page < 1 or page > len(pages):
            return await ctx.send(
                f"Invalid page. Choose between 1 and {len(pages)}."
            )

        view = paginator.Paginator(pages)
        view.current_page = page - 1
        view.update_buttons()

        await ctx.send(
            embed=view.get_embed(),
            view=view
        )

    @xp.command()
    @commands.guild_only()
    async def rewards(self, ctx: commands.Context):
        """Check the server rewards for reaching certain levels."""
        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == ctx.guild.id) or {}
        level_roles = guild.get("level_roles", {})

        embed = discord.Embed(
            title="Level Rewards",
            color=0x5865F2
        )

        if not level_roles:
            embed.description = "No level rewards have been configured!"
        else:
            description = []

            for level, roles in sorted(level_roles.items(), key=lambda x: int(x[0])):
                for role_id in roles:
                    role = ctx.guild.get_role(role_id)

                    if role:
                        description.append(f"**Level {level}:** {role.mention}")

            embed.description = "\n".join(description) if description else "No valid level reward roles found!"

        await ctx.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @xp.command()
    @commands.guild_only()
    @checks.is_manager()
    async def set(self, ctx: commands.Context, user: discord.User, level: int, xp: int):
        """Set user experience to a desire amount. Manage Guild permission is needed to use this command."""
        self.set_stat(ctx.guild.id, user.id, (level, xp))
        await ctx.send(f"Set user level to {level} and xp to {xp}.")

    @xp.command()
    @commands.guild_only()
    @checks.is_manager()
    async def configuration(self, ctx: commands.Context):
        """Check the server level configuration. Manage Guild permission is needed to use this command."""
        configuration = self.get_configuration(ctx.guild.id)

        embed = discord.Embed(
            title="XP Configuration",
            color=0x5865F2
        )

        embed.add_field(
            name="Cooldown",
            value=f"`{configuration['cooldown']}s`",
            inline=True
        )

        embed.add_field(
            name="XP Range",
            value=f"`{configuration['min_xp']} - {configuration['max_xp']}`",
            inline=True
        )

        embed.add_field(
            name="Base XP",
            value=f"`{configuration['base_xp']}`",
            inline=True
        )

        embed.add_field(
            name="Growth Rate",
            value=f"`{configuration['growth_rate']}`",
            inline=True
        )

        await ctx.send(embed=embed)

    @xp.command()
    @commands.guild_only()
    @checks.is_manager()
    async def configure(self, ctx: commands.Context, setting: str, value: str):
        """Configure the level system settings. Manage Guild permission is needed to use this command."""
        if setting not in OPTION:
            await ctx.send("Setting does not exist! Please pick from `enabled`, `cooldown`, `min_xp`, `max_xp`, `base_xp`, or `growth_rate`!")
            return
       
        try:
            converter, expected = OPTION[setting]
            value = converter(value)
        except (ValueError, TypeError):
            await ctx.send(f"Invalid value! Expected {expected}!")
            return

        self.set_configuration(ctx.guild.id, setting, value)
        await ctx.send(f"{setting}'s value was updated to {value}")

    @xp.command(with_app_command=False)
    @commands.guild_only()
    @checks.is_manager()
    async def role(self, ctx: commands.Context, mode: str, level: int, role: discord.Role):
        """Add or Remove a role in level rewards.  Manage Guild permission is needed to use this command."""
        if mode not in ["add", "remove"]:
            await ctx.send("Mode only supports `add` and `remove`!")
            return

        Guild = Query()
        guild = self.bot.database.guilds.get(Guild.id == ctx.guild.id) or {}
        level_roles = guild.get("level_roles", {})

        if mode == "add":
            if any(role.id in ids for ids in level_roles.values()):
                await ctx.send("Role already exists!")
                return

            level_roles.setdefault(str(level), []).append(role.id)

            message = f"`{role.id}` has been added to the level {level} rewards."

        elif mode == "remove":
            roles = level_roles.get(str(level), [])

            if role.id not in roles:
                await ctx.send("Role is not assigned to that level!")
                return

            roles.remove(role.id)

            if not roles:
                del level_roles[str(level)]

            message = f"`{role.id}` has been removed from the level {level} rewards."

        self.bot.database.guilds.upsert(
            {**guild, "id": ctx.guild.id, "level_roles": level_roles},
            Guild.id == ctx.guild.id
        )

        await ctx.send(message)


async def setup(bot):
    await bot.add_cog(Level(bot)) 