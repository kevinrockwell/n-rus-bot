from datetime import timedelta
from random import randint
import re
import subprocess
import time

from discord.ext import commands
import discord

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
        total = []
        for _ in range(int(nums[0])):
            total.append(randint(1, int(nums[1])))
        e = utils.embed()
        e.add_field(name=dice, value=",".join(f"`{x}`" for x in total))
        e.add_field(name="Total", value=str(sum(total)))
        await ctx.send(ctx.message.author.mention, embed=e)

    @commands.command(usage='1d6', name='solumroll')
    async def solum_roll(self, ctx: commands.Context, dice):
        nums = dice.split('d')
        if len(nums) != 2 or not all(map(lambda a: a.isdigit(), nums)):
            await ctx.send(f'Input must be formatted like `1d6`, not `{dice}`')
            return
        await ctx.send(f'{ctx.message.author.mention} {1 * nums[0]}')

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        seconds = time.time() - self.bot.start_time
        d = timedelta(seconds=seconds)
        discord.Color
        e = utils.embed()
        e.add_field(name='Bot', value=timedelta(days=d.days, minutes=(int(d.seconds) // 60)))
        host = subprocess.run(['uptime'], stdout=subprocess.PIPE)
        match = re.search(r'.*up (.*\d{1,2}:\d{2}),', str(host.stdout, 'utf-8'))
        if match:
            e.add_field(name='Host', value=match.group(1))
        await ctx.send(embed=e)


def setup(bot: NRus):
    bot.add_cog(Misc(bot))
