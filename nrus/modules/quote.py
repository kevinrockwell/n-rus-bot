import re
import shlex
from typing import Union, Tuple, Match, Pattern, Optional

import discord
from discord.ext import commands
import pymongo
from motor.motor_asyncio import AsyncIOMotorCursor

from bot import NRus

MENTION_PATTERN: Pattern = re.compile(r'<@!([0-9]+)>')


class QuoteCog(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    @commands.group(aliases=['q'], invoke_without_command=True)
    async def quote(self, ctx: commands.Context, *, text: str) -> None:
        author_result = self.get_author(text)
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
            await self.bot.db[collection_name].create_index([('quote', pymongo.TEXT)])
            self.bot.indexed.append(collection_name)
        await self.bot.db[collection_name].insert_one(quote_object)
        return self.create_quote_embed(quote_object)

    @staticmethod
    def get_author(text: str) -> Union[str, Tuple[str, str]]:
        split = shlex.split(text)
        if len(split) >= 2:
            last_match: Match = MENTION_PATTERN.fullmatch(split[-1])
            first_match: Match = MENTION_PATTERN.fullmatch(split[0])
        else:
            return 'Missing author or quote text'
        if len(split) >= 3:
            if split[-2] == '-' and last_match:
                return last_match.group(1), shlex.join(split[:-2])
            elif split[1] == '-' and first_match:
                return first_match.group(1), shlex.join(split[2:])
        if all([first_match, last_match]) or not any([first_match, last_match]):
            return 'Could not determine quote author'
        if first_match:
            quote: str = shlex.join(split[1:])
            author_id_str: str = first_match.group(1)
        else:
            quote: str = shlex.join(split[:-1])
            author_id_str: str = last_match.group(1)
        return author_id_str, quote

    @quote.command()
    async def add(self, ctx: commands.Context, author: discord.Member, *, text: str):
        await self.quote(ctx, author, text=text)

    @quote.command()
    async def search(self, ctx: commands.Context, *, text):
        author_id_str = ''
        if isinstance(author := self.get_author(text), str):
            number, phrase = self.get_number_matches(text)
            author = self.get_author(phrase)
            if not isinstance(author, str):
                author_id_str, phrase = author
        else:
            author_id_str, phrase = author
            number, phrase = self.get_number_matches(phrase)
        if number > 5:  # TODO Make this configurable on a guild by guild basis
            await ctx.send(f'{ctx.message.author.mention} Sending > 5 quotes from a search not permitted.')
            return
        elif number < 1:
            await ctx.send(f'{ctx.message.author.mention} Cannot send less than 1 quote')
            return
        query = {'$text': {'$search': phrase}}
        if author_id_str:
            query.update({'author_id': int(author_id_str)})
        result: AsyncIOMotorCursor = self.bot.db[str(ctx.guild.id)].find(
            query, {'score': {'$meta': 'textScore'}}, limit=number)
        result.sort([('score', {'$meta': 'textScore'})])
        e = discord.Embed()
        i = 1
        async for quote in result:
            e = self.create_quote_embed(quote, self.nth_number_str(i), e=e)
            i += 1
        if number > 1:
            title = f'{ctx.author.mention} Best {number} matches for {phrase}:'
        else:
            title = f'{ctx.author.mention} Best matches for {phrase}:'
        await ctx.send(title, embed=e)

    @quote.command(name='list')
    async def list_(self, ctx: commands.Context):
        await ctx.send('List not implemented yet :(')

    @staticmethod
    def get_number_matches(text: str) -> Tuple[int, str]:
        split = shlex.split(text)
        if len(split) < 2:
            number = 1
            phrase = text
        elif split[-1].isdigit():
            number = int(split[-1])
            phrase = shlex.join(split[:-1])
        elif split[0].isdigit():
            number = int(split[0])
            phrase = shlex.join(split[0:])
        else:
            number = 1
            phrase = text
        return number, phrase

    @staticmethod
    def nth_number_str(n: int) -> str:
        str_n = str(n)
        if str_n.endswith('1'):
            return f'{n}st'
        elif str_n.endswith('2'):
            return f'{n}nd'
        else:
            return f'{n}th'

    @staticmethod
    def create_quote_embed(quote: dict, field_name: Optional[str] = 'Quote Stored:',
                           e: Optional[discord.Embed] = None) -> discord.Embed:
        if e is None:
            e: discord.Embed = discord.Embed()
        attribution = f'- <@!{quote["author_id"]}>\nQuoted by <@!{quote["quoter_id"]}>'
        e.add_field(name=field_name, value=f'```{quote["quote"]}```{attribution}')
        return e  # TODO add check to see if embed is too long


def setup(bot: NRus):
    bot.add_cog(QuoteCog(bot))
