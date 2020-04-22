import asyncio
import re
import shlex
from typing import Union, Tuple, Match, Pattern, Optional

import discord
from discord.ext import commands
import pymongo
from motor.motor_asyncio import AsyncIOMotorCursor

from bot import NRus

MENTION_PATTERN: Pattern = re.compile(r'<@!?([0-9]+)>')


class Quote(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot
        self.delete_queue = {}
        self.star_reactions = ['⭐', '🌟']

    def cog_check(self, ctx):
        return bool(ctx.guild)

    @commands.Cog.listener('on_raw_reaction_add')
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name in self.star_reactions:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            star_count = 0
            for reaction in message.reactions:
                if reaction.emoji in self.star_reactions:
                    star_count += reaction.count
            if star_count == 1:
                await self.quote_from_message(message, payload.user_id)

    @commands.group(aliases=['q'], invoke_without_command=True)
    async def quote(self, ctx: commands.Context, *, text: str) -> None:
        author_result = self.get_author(text)
        if isinstance(author_result, str):
            await ctx.send(f'{ctx.message.author.mention} {author_result}')
            return
        author_id_str, quote = author_result
        embed = await self.store_quote(ctx.message, int(author_id_str), quote=quote)
        await ctx.send(f'{ctx.message.author.mention}', embed=embed)

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

    @quote.command(aliases=['s'])
    async def search(self, ctx: commands.Context, *, text):  # TODO just use *args lmao
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
        i = 0
        async for quote in result:
            e = self.create_quote_embed(quote, self.nth_number_str(i := i + 1), e=e)
        if number > 1:
            title = f'{ctx.author.mention} Best {number} matches for {phrase}:'
        else:
            title = f'{ctx.author.mention} Best matches for {phrase}:'
        await ctx.send(title, embed=e)

    @quote.command(name='list')  # TODO make async enumerate
    async def list_(self, ctx: commands.Context, *args):
        n = 0
        authors = []
        for arg in args:
            if arg.isdigit():
                if n == 0:
                    n = int(arg)
                else:
                    await ctx.send(f'{ctx.author.mention} Please supply only _one_ `number` argument.')
                    return
            else:
                if match := MENTION_PATTERN.fullmatch(arg):
                    authors.append(int(match.group(1)))
        if n <= 0:
            n = 1
        elif n > 5:
            await ctx.send(f'{ctx.author.mention} Sending > 5 quotes not permitted')
            return
        query = {}
        if authors:
            query.update({'author_id': {'$in': authors}})
        results = self.bot.db[str(ctx.guild.id)].find(query, limit=n)
        results.sort('time', pymongo.DESCENDING)
        e = discord.Embed()
        title = f'{ctx.author.mention} Most recent quote{"s" if n > 1 else ""}'
        i = 0
        async for quote in results:
            self.create_quote_embed(quote, self.nth_number_str(i := i + 1), e)
        await ctx.send(title, embed=e)

    @commands.check_any(commands.has_permissions(administrator=True),
                        commands.has_permissions(manage_messages=True),
                        commands.has_role(699765480566554645))
    @quote.command()
    async def delete(self, ctx: commands.Context):
        await ctx.send(f"{ctx.author.mention} Sorry haven't implemented that yet :(")

    @quote.command()
    async def random(self, ctx, author: Optional[discord.Member] = None) -> None:
        pipeline = []
        if author:
            pipeline.append({'$match': {'author_id': author.id}})
        pipeline.append({'$sample': {'size': 1}})
        result = self.bot.db[str(ctx.guild.id)].aggregate(pipeline)
        quote_ = await result.to_list(1)
        e = self.create_quote_embed(quote_[0], 'Random Quote:')
        await ctx.send(ctx.author.mention, embed=e)

    @quote.command(aliases=['number', 'countquotes'])
    async def count(self, ctx: commands.Context, author: Optional[discord.Member] = None) -> None:
        query = {}
        if author:
            query['author_id'] = ctx.author.id
        n = await self.bot.db[str(ctx.guild.id)].count_documents(query)
        if n == 1:
            response = f'{ctx.author.mention} there is 1 quote stored'
        else:
            response = f'{ctx.author.mention} there are {n} quotes stored'
        if author:
            response += f'by {author.mention}'
        await ctx.send(response)

    async def quote_from_message(self, message: discord.Message, quoter_id: int) -> None:
        e = await self.store_quote(message, message.author.id, quoter_id=quoter_id)
        await message.channel.send(f'<@!{quoter_id}>', embed=e)

    async def store_quote(self, message: discord.Message, author_id: int, quote: Optional[str] = None,
                          quoter_id: Optional[int] = None) -> discord.Embed:
        if quoter_id is None:
            quoter_id = message.author.id
        if quote is None:
            quote = message.content
        quote_object = {
            'author_id': author_id,
            'quote': quote
        }
        non_quote_dependent = {
            'time': message.created_at,
            'quoter_id': quoter_id
        }
        collection_name = str(message.guild.id)
        if collection_name not in self.bot.indexed:
            await self.bot.db[collection_name].create_index([('quote', pymongo.TEXT)])
            self.bot.indexed.append(collection_name)
            quote_object.update(non_quote_dependent)
        else:
            find_result = await self.bot.db[collection_name].find_one(quote_object)
            quote_object.update(non_quote_dependent)
            if find_result is not None: # TODO extract to separate check function for cleanness
                e = discord.Embed()
                e.add_field(name='title', value='Error:')
                e.add_field(name='description', value='Quote Already Exists')
                return self.create_quote_embed(quote_object, field_name='Quote:', e=e)
        await self.bot.db[collection_name].insert_one(quote_object)
        return self.create_quote_embed(quote_object)

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
        e.add_field(name=field_name, value=f'"{quote["quote"]}"\n{attribution}')
        return e  # TODO add check to see if embed is too long


def setup(bot: NRus):
    bot.add_cog(Quote(bot))
