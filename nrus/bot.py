import asyncio
import time

import discord
import discord.ext.commands as commands
import motor.motor_asyncio as motor

EXTENSIONS = [
    'modules.settings',
    'modules.quote',
    'modules.admin'
]


class NRus(commands.Bot):
    def __init__(self, settings):
        super().__init__(command_prefix=_get_prefix)
        self.settings = settings
        self.start_time = time.time()
        if self.settings['release'] == 'production':
            self.db: motor.AsyncIOMotorDatabase = motor.AsyncIOMotorClient().NRus
        else:
            self.db: motor.AsyncIOMotorCollection = motor.AsyncIOMotorClient().NRusTesting
        self.guild_settings: motor.AsyncIOMotorCollection = self.db.guilds
        self.guild_prefixes: dict = {}
        self.indexed: list = []
        for ext in EXTENSIONS:
            self.load_extension(ext)

    async def on_ready(self) -> None:
        self.guild_prefixes = await self._get_prefixes()
        self.indexed = await self.db.list_collection_names()
        print(f'Bot ready as {self.user}')

    def run(self):
        super().run(self.settings['token'])

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.db.drop_collection(str(guild.id))
        await self.db.guilds.remove_one({'id': guild.id})

    async def _get_prefixes(self) -> dict:
        prefixes = {}
        async for guild in self.guild_settings.find():
            prefixes[guild['id']] = guild.get('prefix', ';')
        return prefixes

    def load_extension(self, name):
        super().load_extension(name)
        print(f'Loaded {name}')

    def unload_extension(self, name):
        super().unload_extension(name)
        print(f'Loaded {name}')

    def reload_extension(self, name):
        super().reload_extension(name)
        print(f'Reloaded {name}')


async def _get_prefix(bot: NRus, msg: discord.Message):
    prefix = bot.guild_prefixes.get(msg.guild.id, ';')
    return commands.when_mentioned_or(prefix, f'{prefix} ')(bot, msg)
