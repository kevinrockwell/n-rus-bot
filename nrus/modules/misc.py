from random import randint

from discord.ext import commands

from bot import NRus
import utils


class Misc(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send(f'Pong! {self.bot.latency * 1000:2.3f} ms :ping_pong:')

    @commands.command(usage='<term> [pings...]', help=f'https://lmgtfy.com/?q=lmgtfy')
    async def lmgtfy(self, ctx: commands.Context, *, term: str):
        pings, term = utils.get_ending_tags(term)
        query = term.replace(' ', '+')
        url = f'https://lmgtfy.com/?q={query}'
        if pings:
            await ctx.send(f"{' '.join(map(utils.create_mention, pings))} {url}")
        else:
            await ctx.send(url)

    @commands.command(usage='', help='The Agile Manifesto')
    async def agile(self, ctx: commands.Context):
        await ctx.send('https://agilemanifesto.org/')

    @commands.command(usage='man', help='RTFM')
    async def rtfm(self, ctx: commands.Context):
        await ctx.send('https://xkcd.com/293/')

    @commands.command(usage='1d6')
    async def roll(self, ctx: commands.Context, dice):
        nums = dice.split('d')
        if len(nums) != 2 or not all(map(lambda a: a.isdigit(), nums)):
            await ctx.send(f'Input must be formatted like `1d6`, not `{dice}`')
            return
        total = 0
        for i in range(int(nums[0])):
            total += randint(1, int(nums[1]))
        await ctx.send(f'{ctx.message.author.mention} {total}')


def setup(bot: NRus):
    bot.add_cog(Misc(bot))
