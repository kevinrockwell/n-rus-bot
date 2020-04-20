import discord
from discord.ext import commands

from bot import NRus


class QuoteCog(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot


def setup(bot: NRus):
    bot.add_cog(QuoteCog(bot))
