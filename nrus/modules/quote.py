import datetime
import re
import shlex
from typing import Union, Tuple, Match, Pattern, List

import discord
from discord.ext import commands

from bot import NRus

MENTION_PATTERN: Pattern = re.compile(r'<@!([0-9]+)>')


class QuoteCog(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    @commands.group(aliases=['q'], invoke_without_command=True)
    async def quote(self, ctx: commands.Context, *, text: str) -> None:
        split = shlex.split(text)
        author_result = self.get_author(split)
        if isinstance(author_result, str):
            await ctx.send(f'{ctx.message.author.mention} {author_result}')
            return
        author_id_str, quote = author_result
        embed = await self.store_quote(ctx, int(author_id_str), quote)
        await ctx.send(f'{ctx.message.author.mention}', embed=embed)

    async def store_quote(self, ctx: commands.Context, author_id: int, quote: str) -> discord.Embed:
        quote_object = {
            'time': ctx.message.created_at,
            'quoter_id': ctx.message.author.id,
            'author_id': author_id,
            'quote': quote
        }
        collection_name = str(ctx.guild.id)
        if collection_name not in self.bot.indexed:
            self.bot.db[collection_name].create_index({'quote': 'text'})
            self.bot.indexed.append(collection_name)
        await self.bot.db[collection_name].insert_one(quote_object)
        return self.create_quote_embed(quote, author_id)

    @staticmethod
    def get_author(split: List[str]) -> Union[str, Tuple[str, str]]:
        if len(split) >= 2:
            last_match: Match = MENTION_PATTERN.fullmatch(split[-1])
            first_match: Match = MENTION_PATTERN.fullmatch(split[0])
        else:
            return 'Missing author or quote text'
        if len(split) >= 3:
            if split[-2] == '-' and last_match:
                return last_match.group(1), ' '.join(split[:-2])
            elif split[1] == '-' and first_match:
                return first_match.group(1), ' '.join(split[2:])
        if all([first_match, last_match]) or not any([first_match, last_match]):
            return 'Could not determine quote author'
        if first_match:
            quote: str = ' '.join(split[1:])
            author_id_str: str = first_match.group(1)
        else:
            quote: str = ' '.join(split[:-1])
            author_id_str: str = last_match.group(1)
        return author_id_str, quote

    @quote.command()
    async def add(self, ctx: commands.Context, author: discord.Member, *, text: str):
        await self.quote(ctx, author, text=text)

    @quote.command()
    async def search(self, ctx: commands.Context):
        await ctx.send('Search not implemented yet :(')

    @quote.command(name='list')
    async def list_(self, ctx: commands.Context):
        await ctx.send('List not implemented yet :(')

    @staticmethod
    def create_quote_embed(quote: str, author_id: Union[int, str], field_name='Quote Stored:') -> discord.Embed:
        e: discord.Embed = discord.Embed()
        e.add_field(name=field_name, value=f'```{quote}```- <@!{author_id}>')
        return e


def setup(bot: NRus):
    bot.add_cog(QuoteCog(bot))
    print(f'{__name__} Loaded')
