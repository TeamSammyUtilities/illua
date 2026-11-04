import discord

from discord.ext import commands
from helpers import paginator
from typing import Optional

HIDDEN_CATEGORY = ["Help", "Jishaku"]

class Help(commands.Cog):
    """For help command."""
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def help(self, ctx: commands.Context, *, query: Optional[str] = None):
        """Shows all available commands."""
        if query is None:
            fields = []

            for cog_name, cog in self.bot.cogs.items():
                if cog_name in HIDDEN_CATEGORY:
                    continue

                command_list = [
                    command
                    for command in cog.get_commands()
                    if not command.hidden
                ]

                if not command_list:
                    continue

                formatted_list = " ".join(
                    f"`{command.name}`"
                    for command in command_list
                )

                fields.append({
                    "name": cog_name,
                    "value": (
                        f"{cog.description or 'No description.'}\n"
                        f"{formatted_list}"
                    ),
                    "inline": False
                })

            if not fields:
                await ctx.send("Nothing found!")
                return

            pages = []

            for i in range(0, len(fields), 3):
                embed = discord.Embed(
                    title="Help",
                    description=(
                        "Use `help <command>` for more info on a command.\n"
                        "Use `help <category>` for more info on a category."
                    ),
                    color=0x5865F2
                )

                for field in fields[i:i + 3]:
                    embed.add_field(**field)

                pages.append(embed)

            view = paginator.Paginator(pages)

            return await ctx.send(
                embed=view.get_embed(),
                view=view
            )

        cog = self.bot.get_cog(query)

        if cog:
            command_list = [
                command
                for command in cog.get_commands()
                if not command.hidden
            ]

            embed = discord.Embed(
                title=cog.qualified_name,
                description=cog.description or "No description.",
                color=0x5865F2
            )

            for command in command_list:
                embed.add_field(
                    name=command.name,
                    value=command.help or "No description",
                    inline=False
                )

            return await ctx.send(embed=embed)

        command = None
        parts = query.split()
        current = self.bot

        for part in parts:
            command = current.get_command(part)

            if command is None:
                break

            current = command

        if command:
            embed = discord.Embed(
                title=f"Help: {command.qualified_name}",
                description=command.help or "No description provided.",
                color=0x5865F2
            )

            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(command.aliases),
                    inline=False
                )

            embed.add_field(
                name="Usage",
                value=f"{command.qualified_name} {command.signature}",
                inline=False
            )

            if isinstance(command, commands.Group):
                subcommands = [
                    subcommand
                    for subcommand in command.commands
                    if not subcommand.hidden
                ]

                if subcommands:
                    embed.add_field(
                        name="Subcommands",
                        value="\n".join(
                            f"`{subcommand.qualified_name}` - "
                            f"{subcommand.help or 'No description'}"
                            for subcommand in subcommands
                        ),
                        inline=False
                    )

            return await ctx.send(embed=embed)

        await ctx.send("Nothing found!")


async def setup(bot):
    await bot.add_cog(Help(bot))