import re
from typing import Union, Tuple, Match, Pattern, Optional, Set, Dict, Any

import discord
from discord.ext import commands
import pymongo
from motor.motor_asyncio import AsyncIOMotorCursor

from bot import NRus
import utils

AUTHORS_PATTERN: Pattern = re.compile(r'( ?<@!?[0-9]+>)+$')
BASIC_INT_PATTERN: Pattern = re.compile(r'[0-9]')
GET_NUMBER_PATTERN: Pattern = re.compile(r' ?([0-9]+)$')


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
            if message.author.id == self.bot.user.id:
                return
            star_count = 0
            for reaction in message.reactions:
                if reaction.emoji in self.star_reactions:
                    star_count += reaction.count
            if star_count == 1:
                await self.quote_from_message(message, payload.user_id)

    @commands.group(aliases=['q'], invoke_without_command=True)
    async def quote(self, ctx: commands.Context, *, text) -> None:
        author_result = self.get_authors(text)
        if author_result is None:
            await ctx.send(f'{ctx.message.author.mention} No authors were found :(')
            return
        author_ids, quote = author_result
        embed = await self.store_quote(ctx.message, author_ids, quote=' '.join(quote))
        await ctx.send(f'{ctx.message.author.mention}', embed=embed)

    @quote.command()
    async def add(self, ctx: commands.Context, *, text: str):
        await self.quote(ctx, text=text)

    @quote.command(aliases=['s'])
    async def search(self, ctx: commands.Context, *, text: str):
        number, text = self.get_number_matches(text.strip())
        authors, phrase = self.get_authors(text.strip())
        if number > 6:  # TODO Make this configurable on a guild by guild basis
            await ctx.send(f'{ctx.message.author.mention} Sending > 6 quotes from a search not permitted.')
            return
        elif number < 1:
            number = 6
        query = {'$text': {'$search': phrase}}
        if authors:
            query.update({'author_id': authors})
        result: AsyncIOMotorCursor = self.bot.db[str(ctx.guild.id)].find(
            self.create_quote_query(query), {'score': {'$meta': 'textScore'}}, limit=number)
        result.sort([('score', {'$meta': 'textScore'})])
        e = discord.Embed()
        i = 0
        async for i, quote in utils.async_enumerate(result, start=1):
            e = self.create_quote_embed(quote, self.nth_number_str(i), e=e)
        if i == 0:
            await ctx.send(f'No matches for {phrase} found.')
            return
        elif i > 1:
            title = f'{ctx.author.mention} Best matches for {phrase}:'
        else:
            title = f'{ctx.author.mention} Best match for {phrase}:'
        await ctx.send(title, embed=e)

    @quote.command(name='list')  # TODO make async enumerate
    async def list_(self, ctx: commands.Context, *, text):
        n, authors = self.get_number_and_authors(text)
        if n > 6:
            await ctx.send(f'{ctx.author.mention} Sending > 6 quotes not permitted')
            return
        elif n < 1:
            n = 6  # Set to default if amount is unreasonable
        query = {}
        if authors is not None:
            query.update({'author_id': authors})  # Is formatted into correct MongoDB call by create_quote_query
        results = self.bot.db[str(ctx.guild.id)].find(self.create_quote_query(query), limit=n)
        results.sort('time', pymongo.DESCENDING)
        e = discord.Embed()
        title = f'{ctx.author.mention} Most recent quote{"s" if n > 1 else ""}'
        i = 1
        async for quote in results:
            self.create_quote_embed(quote, self.nth_number_str(i), e)
            i += 1
        await ctx.send(title, embed=e)

    @commands.check_any(commands.has_permissions(administrator=True),
                        commands.has_permissions(manage_messages=True),
                        commands.has_role(699765480566554645))
    @quote.command()
    async def delete(self, ctx: commands.Context):
        await ctx.send(f"{ctx.author.mention} Sorry haven't implemented that yet :(")

    @quote.command(aliases=['r'])
    async def random(self, ctx, *author: Optional[discord.Member]) -> None:
        pipeline = []
        if author:
            pipeline.append({'$match': {'author_id': author.id}})
        pipeline.append({'$sample': {'size': 1}})
        result = self.bot.db[str(ctx.guild.id)].aggregate(pipeline)
        quote_ = await result.to_list(1)
        e = self.create_quote_embed(quote_[0], 'Random Quote:')
        await ctx.send(ctx.author.mention, embed=e)

    @quote.command(aliases=['number', 'countquotes'])
    async def count(self, ctx: commands.Context, *, text: Optional = '') -> None:
        query = {}
        if text:
            authors = self.get_authors(text)
            if authors and authors[1].strip() == '':
                query['author_id'] = self.create_quote_query({'author_id': authors[0]})
            else:
                await ctx.send(f'Unexpected argument: {authors[1]}')
                return
        else:
            authors = []
        n = await self.bot.db[str(ctx.guild.id)].count_documents(query)
        if n == 1:
            response = f'{ctx.author.mention} there is 1 quote stored'
        else:
            response = f'{ctx.author.mention} there are {n} quotes stored'
        author_len = len(authors)
        author_str = 'by '
        if not author_len:
            await ctx.send(response)
            return
        elif author_len == 1:
            author_str += utils.create_mention(authors[0])
        elif author_len == 2:
            author_str += ' and '.join(map(utils.create_mention, authors))
        else:
            author_str += ', '.join(map(utils.create_mention, authors[:-1]))
            author_str += 'and ' + utils.create_mention(authors[-1])
        await ctx.send(response + author_str)

    def get_number_and_authors(self, text: str) -> Union[str, Tuple[int, Tuple[int]]]:
        number, text = self.get_number_matches(text)
        authors, text = self.get_authors(text.strip())
        text = text.strip()
        if text != '':
            return text
        return number, authors

    async def quote_from_message(self, message: discord.Message, quoter_id: int) -> None:
        e = await self.store_quote(message, message.author.id, quoter_id=quoter_id)
        await message.channel.send(f'<@!{quoter_id}>', embed=e)

    async def store_quote(self, message: discord.Message, author_ids: Tuple[int], quote: Optional[str] = None,
                          quoter_id: Optional[int] = None) -> discord.Embed:
        quote_object = {
            'author_id': author_ids,
            'quote': quote,
            'time': message.created_at,
            'quoter_id': quoter_id
        }
        if quoter_id is None:
            quote_object['quoter_id'] = message.author.id
        if quote is None:
            quote_object['quote'] = message.content
        collection_name = str(message.guild.id)
        if collection_name not in self.bot.indexed:
            await self.bot.db[collection_name].create_index([('quote', pymongo.TEXT)])
            self.bot.indexed.append(collection_name)
        else:
            query = self.create_quote_query(quote_object, ignore=['time', 'quoter_id'])
            find_result = await self.bot.db[collection_name].find_one(query)
            if find_result is not None:
                e = discord.Embed()
                e.add_field(name='Error:', value='Quote Already Exists', inline=False)
                return self.create_quote_embed(quote_object, field_name='Quote:', e=e)
        await self.bot.db[collection_name].insert_one(quote_object)
        return self.create_quote_embed(quote_object)

    @staticmethod
    def get_authors(text: str) -> Union[None, Tuple[Tuple[int], str]]:
        match: Match = AUTHORS_PATTERN.search(text)
        if not match:
            return None
        start = match.start()
        text, authors = text[:start], text[start:]
        author_ids: Set = set(BASIC_INT_PATTERN.findall(authors))
        return tuple(map(int, author_ids)), text

    @staticmethod
    def create_quote_query(query: Dict[str, Any], author_type='and', ignore=()):
        if author_type not in ['and', 'or']:
            raise ValueError('Author Type must equal "and" or "or"')
        out_query = {}
        authors: Tuple = query.pop('author_id', ())
        if authors:
            if author_type == 'and':
                out_query['author_id'] = {'$all': authors}
            else:
                out_query['$or'] = [{'author_id': a} for a in authors]
        for key, value in query:
            if key not in ignore:
                out_query[key] = value
        return out_query

    @staticmethod
    def get_number_matches(text: str) -> Tuple[int, str]:
        """Returns number from the end of string or -1 if no number is found, along with the remainder of string"""
        match: Match = GET_NUMBER_PATTERN.match(text)
        if match:
            return -1, text
        return int(match.group(1)), text[:match.start()]

    @staticmethod
    def nth_number_str(n: int) -> str:
        last_n = str(n)[-1]
        conversion_dict = {'1': 'st', '2': 'nd', '3': 'rd'}
        return f'{n}{conversion_dict.get(last_n, "th")}'

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
