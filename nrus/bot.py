import json
import time

import discord
import discord.ext.commands as commands

EXTENSIONS = [
    'modules.misc'
]


class NRus(commands.Bot):
    def __init__(self, settings):
        super().__init__(command_prefix=_get_prefix)
        self.settings = settings
        self.start_time = time.time()
        for ext in EXTENSIONS:
            self.load_extension(ext)
        # Temporary until I implement DB
        with open('prefixes.json') as f:
            self.guild_prefixes: dict = json.load(f)
        self.guild_prefixes: dict = {int(key): val for key, val in self.guild_prefixes.items()}

    async def on_ready(self):
        print(f'Bot ready as {self.user}')

    def run(self):
        super().run(self.settings['token'])


async def _get_prefix(bot: NRus, msg: discord.Message):
    return commands.when_mentioned_or(bot.guild_prefixes.get(msg.guild.id, ';'))(bot, msg)
