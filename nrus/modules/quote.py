import discord
from discord.ext import commands

from bot import NRus


class QuoteCog(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    @commands.group(aliases=['q'], invoke_without_command=True)
    async def quote(self, ctx: commands.Context, author: discord.Member, *, text: str):
        print(author)
        print(text)

    @quote.command()
    async def add(self, ctx: commands.Context, author: discord.Member, *, text: str):
        await self.quote(ctx, author, text=text)

    @quote.command()
    async def search(self, ctx: commands.Context):
        await ctx.send('Search not implemented yet :(')

    @quote.command(name='list')
    async def list_(self, ctx: commands.Context):
        await ctx.send('List not implemented yet :(')


def setup(bot: NRus):
    bot.add_cog(QuoteCog(bot))
