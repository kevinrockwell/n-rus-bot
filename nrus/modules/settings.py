from typing import Optional

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
    async def set_prefix(self, ctx: commands.Context, prefix: Optional[str]):
        # Reset if no prefix is specified
        guild_id = ctx.guild.id
        if prefix is None or prefix == ';':
            if guild_id not in self.bot.guild_prefixes:
                await ctx.send('Guild prefix already `;`, the default.')
                return
            del self.bot.guild_prefixes[guild_id]
            self.bot.guild_settings.remove_one({'id': guild_id})
            prefix = ';'
        else:
            if prefix == self.bot.guild_prefixes[guild_id]:
                await ctx.send(f'Prefix already set to `{prefix}`')
            self.bot.guild_prefixes[guild_id] = prefix
            await self.bot.guild_settings.update_one(
                {'id': guild_id}, {'$set': {'prefix': prefix}}, upsert=True
            )
        await ctx.send(f'Set prefix to {prefix}')


def setup(bot: NRus) -> None:
    bot.add_cog(Settings(bot))
