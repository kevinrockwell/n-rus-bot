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


def setup(bot: NRus):
    bot.add_cog(Misc(bot))
