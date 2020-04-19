import json

import discord
import discord.ext.commands as commands


class NRus(commands.Bot):
    def __init__(self, settings):
        super().__init__(command_prefix=_get_prefix)
        self.settings = settings
        # Temporary until I implement DB
        with open('prefixes.json') as f:
            self.guild_prefixes: dict = json.load(f)
        self.guild_prefixes = {int(key): val for key, val in self.guild_prefixes.items()}

    async def on_ready(self):
        print(f'Bot ready as {self.user}')

    async def on_message(self, message):
        print(message.guild.id)
        await self.process_commands(message)

    def run(self):
        super().run(self.settings['token'])


async def _get_prefix(bot: NRus, msg: discord.Message):
    return commands.when_mentioned_or(bot.guild_prefixes.get(msg.guild.id, ';'))(bot, msg)
