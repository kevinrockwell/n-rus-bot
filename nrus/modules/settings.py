from discord.ext import commands

from bot import NRus


class Settings(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    @commands.guild_only()
    @commands.command(usage='prefix', help='Returns the prefix for this server')
    async def prefix(self, ctx: commands.Context):
        await ctx.send(f'Current prefix: `{self.bot.guild_prefixes.get(ctx.guild.id, ";")}`')

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(aliases=['setprefix'], help='Set the prefix for this server. Admin Only.')
    async def set_prefix(self, ctx: commands.Context, prefix: str):
        self.bot.guild_prefixes[ctx.guild.id] = prefix
        await self.bot.guild_settings.update_one({'id': ctx.guild.id}, {'$set': {'prefix': prefix}}, upsert=True)
        await ctx.send(f'Set prefix to {prefix}')


def setup(bot: NRus) -> None:
    bot.add_cog(Settings(bot))
