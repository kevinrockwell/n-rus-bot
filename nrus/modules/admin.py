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
import utils


# Matches one or more spaces because git output contains extra spaces to line up output
GIT_CHANGED_FILE: Pattern = re.compile(r'nrus/(.+?).py +\| +[1-9] +\+*-*')
MODULE_PATH_MATCH: Pattern = re.compile(r'nrus/modules/[^/]+')


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
        e: discord.Embed = utils.embed()
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
        output = await self.run_commands('git pull origin master')
        if (git_output_embed := self.format_process_output(output)) is None:
            await ctx.send('No git output...')
        else:
            await ctx.send('Checkout Complete.', embed=git_output_embed)
        if output.returncode != 0:
            await ctx.send(
                f'Git checkout failed with return code {output.returncode}, not reloading extensions'
            )
            return
        await ctx.send('Reloading extensions...')
        try:
            self.bot.reload_extensions()
        except Exception as e:
            await ctx.send(f'Error loading extensions: {e.__class__.__name__}: {e}')
        else:
            await ctx.send('Reload successful')
        # Reload python files that are not extensions because these files will not be reloaded
        # Start by getting list of changed files from git output
        changed_modules = self.find_changed_modules(output.stdout)
        if {'bot', 'main'}.intersection(changed_modules):
            await ctx.send('`nrus/bot.py` or `nrus/main.py` was changed. Restarting NRus...')
            await self.bot.logout()
        for name in changed_modules:
            if MODULE_PATH_MATCH.fullmatch(name):
                await ctx.send(
                    f'Warning: {name} is in `nrus/modules/` but is not in `{self.bot.extension_file}`'
                )
            if (module := sys.modules.get(name)) is None:
                await ctx.send(f'Warning: Module {name} was changed but is not loaded')
                continue
            try:
                importlib.reload(module)
            except Exception as e:
                await ctx.send(f'Error loading {name}: {e.__class__.__name__}: {e}')
        await ctx.send('Checkout Successful')

    @commands.command(aliases=['sh'])
    async def shell(self, ctx: commands.context, *, command: str):
        output = await self.run_commands(command)
        if (results_embed := self.format_process_output(output)) is None:
            await ctx.send('No output')
        else:
            await ctx.send('Command Output:', embed=results_embed)

    @commands.command(aliases=['setstatus'])
    async def set_status(self, ctx: commands.Context, *, status: str):
        await self.bot.change_presence(activity=discord.Game(status))
        self.bot.settings['status'] = status

    @commands.command()
    async def logout(self, ctx: commands.Context):
        await ctx.send('Logging out...')
        await self.bot.logout()

    @staticmethod
    async def run_commands(command: str) -> subprocess.CompletedProcess:
        loop = asyncio.get_running_loop()
        run = functools.partial(
            subprocess.run, command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        return await loop.run_in_executor(None, run)

    # TODO see if changing this is required
    @staticmethod
    def format_process_output(output: subprocess.CompletedProcess):
        """Puts stdout and stderr into an embed, max 2048 characters per."""
        e = utils.embed()
        if output.stdout:
            stdout = output.stdout.decode()
            if len(stdout) > 2048:
                # Subtract 15: 6 for label, 6 for codeblocks, and 3 for `...`
                stdout = stdout[: 2048 - 15] + '...'
            e.description = f'stdout```{stdout}```'
        if output.stderr:
            stderr = output.stderr.decode()
            if len(stderr) > 2048:
                # See stdout for subtracting 15 explanation
                stderr = stderr[: 2048 - 15] + '...'
            e.set_footer(text=f'stderr```{stderr}```')
        if len(e):
            return e
        return None

    def find_changed_modules(self, git_output: bytes) -> list:
        changed_files = []
        for line in git_output.decode().split('\n'):
            match: Match = GIT_CHANGED_FILE.search(line)
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
