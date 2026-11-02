import dotenv
import discord
import os

from discord.ext import commands    
from helpers import constants
from tinydb import Query

dotenv.load_dotenv(".env")


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            case_insensitive=True,
            command_prefix=self.get_prefixes,
            help_command=None,
            intents=discord.Intents.all()
        )

    async def get_prefixes(self, bot, message):
        if message.guild is None:
            return constants.DEFAULT_PREFIXES

        Guild = Query()
        guild = self.database.guilds.get(Guild.id == message.guild.id) or {}

        custom = guild.get("prefixes", [])

        return constants.DEFAULT_PREFIXES + custom

    async def is_owner(self, user):
        if user.id in constants.DEVELOPER:
            return True
        return await super().is_owner(user)

    async def setup_hook(self):
        await self.load_extension("jishaku")
        for cog in constants.COGS:
            await self.load_extension(f"cogs.{cog}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send(str(error))
            return

        if isinstance(error, commands.CommandNotFound):
            return

        print(str(error))

    @property
    def database(self):
        cog = self.get_cog("Database")
        if cog is None:
            raise RuntimeError("Database cog is not loaded yet.")
        return cog

    async def dm_user(self, user, message):
        try:
            await user.send(message)
        except discord.Forbidden:
            pass


if __name__ == "__main__":
    bot = Bot()
    bot.run(os.environ["TOKEN"])    