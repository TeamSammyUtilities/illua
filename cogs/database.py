from discord.ext import commands
from tinydb import TinyDB


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.database = TinyDB("database.json")
        self.members = self.database.table("members")
        self.users = self.database.table("users")
        self.guilds = self.database.table("guilds")
        self.channels = self.database.table("channels")

    async def cog_unload(self):
        self.db.close()


async def setup(bot):
    await bot.add_cog(Database(bot))