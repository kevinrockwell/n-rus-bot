import asyncio
import functools
import importlib
import json
import re
import subprocess
import sys
from typing import Match, Optional, Pattern

import discord
from discord.ext import commands

from bot import NRus


GIT_CHANGED_FILE: Pattern = re.compile(r'nrus/(.+?).py \| [1-9] \+*-*')


class Admin(commands.Cog):
    def __init__(self, bot: NRus):
        self.bot = bot

    def cog_check(self, ctx):
        return self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    async def reload(self, ctx: commands.Context, name: Optional[str] = None) -> None:
        if name:
            ext_name = f'modules.{name}'
            await ctx.send(f'Reloading {ext_name}')
            self.bot.reload_extension(ext_name)
        else:
            await ctx.send('Reloading all modules...')
            self.bot.reload_extensions()

    @commands.command(hidden=True)
    async def load(self, ctx: commands.Context, name: str) -> None:
        ext_name = f'modules.{name}'
        await ctx.send(f'Loading {ext_name}')
        self.bot.load_extension(ext_name)

    @commands.command(hidden=True)
    async def unload(self, ctx: commands.Context, name: str) -> None:
        ext_name = f'modules.{name}'
        await ctx.send(f'Unloading {ext_name}')
        self.bot.unload_extension(ext_name)

    @commands.command(hidden=True)
    async def loaded(self, ctx: commands.Context) -> None:
        e: discord.Embed = discord.Embed()
        e.add_field(name='Cogs Loaded:', value='\n'.join(self.bot.cogs))
        await ctx.send(embed=e)

    @commands.command(hidden=True, name='exec')
    async def exec_(self, ctx: commands.Context, *, text) -> None:
        text = text.strip('```python').strip('`').split('\n')
        out = ['async def f():']
        for line in text:
            out.append('\t' + line)
        vars_ = {'bot': self.bot, 'ctx': ctx}
        vars_.update(globals())
        try:
            exec("\n".join(out), vars_)
            f = vars_['f']
            result = await f()
        except Exception as e:
            await ctx.send(f'{e.__class__}: {e}')
            return
        if result is not None:
            await ctx.send(result)

    @commands.command(name='gitreload', hidden=True, aliases=['reloadgit'])
    async def git_reload(self, ctx: commands.Context):
        await ctx.send('Checking out from git...')
        loop = asyncio.get_running_loop()
        run = functools.partial(subprocess.run, ['git', 'pull', 'origin', 'master'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output: subprocess.CompletedProcess = await loop.run_in_executor(None, run)
        e = discord.Embed()
        if output.stdout:
            e.add_field(name='Git output', value=output.stdout.decode())
        if output.stderr:
            e.add_field(name='Git stderr', value=output.stderr.decode())
        if len(e):
            await ctx.send('Checkout Complete.', embed=e)
        else:
            await ctx.send('No git output...')
        if output.returncode == 0:
            await ctx.send('Reloading extensions...')
            try:
                self.bot.reload_extensions()
            except Exception as e:
                await ctx.send(f'Error loading extensions: {e.__class__.__name__}: {e}')
            await ctx.send('Reload successful')
            # Reload python files that are not extensions because these files will not be reloaded
            # Start by getting list of changed files from git output
            changed_modules = self.find_changed_modules(output.stdout)
            if 'bot' in changed_modules:
                await ctx.send('nrus/bot.py was changed. Restarting NRus...')
                await self.bot.logout()
            for name in changed_modules:
                if name.startswith('modules.'):
                    await ctx.send(f'Warning: {name} is in nrus/modules/ but is not in {self.bot.extension_file}')
                module = sys.modules.get(name)
                if module is None:
                    await ctx.send(f'Warning: Module {name} was changed but is not loaded')
                    continue
                try:
                    importlib.reload(module)
                except Exception as e:
                    await ctx.send(f'Error loading {name}: {e.__class__.__name__}: {e}')
            await ctx.send('Checkout Successful')
        else:
            await ctx.send('Git checkout failed, not reloading extensions')

    def find_changed_modules(self, git_output: bytes) -> list:
        changed_files = []
        for line in git_output.decode().split('\n'):
            match: Match = GIT_CHANGED_FILE.match(line)
            if match:
                relative_path = match.group(1)
                module_name = '.'.join(relative_path.split('/'))
                changed_files.append(module_name)
        # Remove files that are in the extensions file
        with open(self.bot.extension_file) as f:
            extensions = json.load(f)
        return [file for file in changed_files if file not in extensions]


def setup(bot: NRus):
    bot.add_cog(Admin(bot))
