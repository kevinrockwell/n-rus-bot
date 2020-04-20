import datetime
import re
import shlex

import discord
from discord.ext import commands

from bot import NRus

MENTION_PATTERN: re.Pattern = re.compile(r'<@!([0-9]+)>')


class QuoteCog(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    @commands.group(aliases=['q'], invoke_without_command=True)
    async def quote(self, ctx: commands.Context, *, text: str) -> None:
        split = shlex.split(text)
        if len(split) >= 2:
            last_match: re.Match = MENTION_PATTERN.fullmatch(split[-1])
            first_match: re.Match = MENTION_PATTERN.fullmatch(split[0])
        else:
            await ctx.send(f'{ctx.message.author.mention} Missing author or quote text')
            return
        quote = ''
        if len(split) >= 3:
            if split[-2] == '-' and last_match:
                quote: str = ' '.join(split[:-2])
                author_id_str: str = last_match.group(1)
            elif split[1] == '-' and first_match:
                quote: str = ' '.join(split[2:])
                author_id_str: str = first_match.group(1)
        print(quote)
        print(*map(bool, (first_match, last_match)))
        if len(split) < 3 or not quote:
            if all([first_match, last_match]) or not any([first_match, last_match]):
                await ctx.send(f'{ctx.message.author.mention} Could not determine quote author')
                return
            if first_match:
                quote: str = ' '.join(split[1:])
                author_id_str: str = first_match.group(1)
            else:
                quote: str = ' '.join(split[:-1])
                author_id_str: str = last_match.group(1)
        print(author_id_str)
        await self.store_quote(ctx, int(author_id_str), quote)

    async def store_quote(self, ctx: commands.Context, author_id: int, quote: str) -> None:
        quote_object = {
            'time': ctx.message.created_at,
            'quoter_id': ctx.message.author.id,
            'author_id': author_id ,
            'quote': quote
        }
        await self.bot.db[str(ctx.guild.id)].insert_one(quote_object)

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
