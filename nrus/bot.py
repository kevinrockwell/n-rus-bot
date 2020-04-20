import asyncio
import time

import discord
import discord.ext.commands as commands
import motor.motor_asyncio as motor

EXTENSIONS = [
    'modules.settings',
    'modules.quote'
]


class NRus(commands.Bot):
    def __init__(self, settings):
        super().__init__(command_prefix=_get_prefix)
        self.settings = settings
        self.start_time = time.time()
        self.db: motor.AsyncIOMotorDatabase = motor.AsyncIOMotorClient().NRus
        self.guild_settings: motor.AsyncIOMotorCollection = self.db.guilds
        self.guild_prefixes: dict = {}
        for ext in EXTENSIONS:
            self.load_extension(ext)

    async def on_ready(self):
        self.guild_prefixes = await self._get_prefixes()
        print(f'Bot ready as {self.user}')

    def run(self):
        super().run(self.settings['token'])

    async def _get_prefixes(self) -> dict:
        prefixes = {}
        async for guild in self.guild_settings.find():
            prefixes[guild['id']] = guild.get('prefix', ';')
        return prefixes


async def _get_prefix(bot: NRus, msg: discord.Message):
    prefix = bot.guild_prefixes.get(msg.guild.id, ';')
    return commands.when_mentioned_or(prefix, f'{prefix} ')(bot, msg)
