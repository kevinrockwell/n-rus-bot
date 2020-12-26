import asyncio
from collections import defaultdict
import concurrent
import time
from typing import DefaultDict, Optional

from discord.ext import commands

# from bot import NRus
import utils


class BFError(Exception):
    pass


class BFTimeoutError(BFError):
    pass


class WrappingInt(int):
    def __new__(cls, value: int, min_: int = 0, max_: int = 1, *args, **kwargs):
        if min_ > max_:
            raise ValueError('Minimum must be less than or equal to maximum')
        if not min_ <= value <= max_:
            range_ = max_ - min_ + 1
            if value < min_:
                effective_distance = (min_ - value) % range_
                value = max_ - effective_distance + 1
            else:
                effective_distance = (value - max_) % range_
                value = min_ + effective_distance - 1
        return_val: WrappingInt = super(cls, cls).__new__(cls, value, **kwargs)
        return_val.min: int = min_
        return_val.max: int = max_
        return return_val

    def __add__(self, other):
        return self.__class__(super().__add__(other), self.min, self.max)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__add__(-other)

    def __rsub__(self, other):
        return self.__add__(-other)

    def __mul__(self, other):
        return self.__class__(super().__mul__(other), self.min, self.max)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return self.__class__(super().__truediv__(other), self.min, self.max)

    def __rtruediv__(self, other):
        return self.__class__(super().__rtruediv__(other), self.min, self.max)

    def __floordiv__(self, other):
        return self.__class__(super().__floordiv__(other), self.min, self.max)

    def __rfloordiv__(self, other):
        return self.__class__(super().__rfloordiv__(other), self.min, self.max)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, super().__repr__())


class BFCells:

    CELL_MIN = 0
    CELL_MAX = 255
    CELL_DEFAULT_VALUE = 0
    DEFAULT_CELL = WrappingInt(CELL_DEFAULT_VALUE, CELL_MIN, CELL_MAX)

    def __init__(self):
        self.pointer = WrappingInt(0, 0, 30000)
        self._cells: DefaultDict[WrappingInt, WrappingInt] = defaultdict(self.bf_cell_factory)

    @classmethod
    def bf_cell_factory(cls):
        return cls.DEFAULT_CELL

    def increment(self):
        self.cell += 1

    def decrement(self):
        self.cell -= 1

    def increment_pointer(self):
        self.pointer += 1

    def decrement_pointer(self):
        self.pointer -= 1

    @property
    def cell(self):
        return self._cells[self.pointer]

    @cell.setter
    def cell(self, value: int):
        self._cells[self.pointer] = WrappingInt(value, self.CELL_MIN, self.CELL_MAX)


class BFInstance(BFCells):

    CHECK_TIMEOUT_INTERVAL = 50  # Number of instructions between timeout checks

    def __init__(self, program: str, input_: str = ''):
        super().__init__()
        self.program = [c for c in program if c in '<>+-,.[]']
        self.len = len(program)
        self.input = input_
        self.output = []
        self.validate_program()
        self.program_pointer = 0  # Tracks location in program
        self.loops = []  # Track where loops start to easily jump to them

    def validate_program(self):
        """Program is invalid if not all loops are closed"""
        if self.program.count('[') != self.program.count(']'):
            raise BFError('Invalid Program: `[` and `]` count not equal')

    @property
    def instruction(self):
        return self.program[self.program_pointer]

    def start_loop(self):
        """Executed on '['. Adds current pointer to loops"""
        self.loops.append(self.program_pointer)

    def end_loop(self):
        """Executed on ']'. Checks if jump to start of loop should be made or not"""
        if self.cell:
            self.program_pointer = self.loops[-1]
        else:
            self.loops.pop()

    def get_chr(self):
        self.output.append(chr(self.cell))

    def set_chr(self, value: str):
        for c in self.input:
            self.cell = c
            yield
        raise BFError('Error: Not Enough Input Provided')

    def run(self, timeout):
        commands = {
            '>': self.increment_pointer,
            '<': self.decrement_pointer,
            '+': self.increment,
            '-': self.decrement,
            '.': self.get_chr,
            ',': self.set_chr,
            '[': self.start_loop,
            ']': self.end_loop,
        }

        instructions_since_last_check = 0
        start_time = time.time()
        while self.program_pointer < self.len:
            command = commands[self.instruction]
            command()
            self.program_pointer += 1
            if timeout > 0:
                instructions_since_last_check += 1
                if instructions_since_last_check > self.CHECK_TIMEOUT_INTERVAL:
                    instructions_since_last_check = 0
                    if time.time() > start_time + timeout:
                        raise BFTimeoutError(f'Error: Excecution time ({timeout}s) exceeded')

        return ''.join(self.output)


class BF(commands.Cog):

    MAXIMUM_PROCESSES = 2
    TIMEOUT = 10.0  # Timeout in seconds

    def __init__(self, bot):
        self.bot = bot
        self.executor = concurrent.futures.ProcessPoolExecutor(self.MAXIMUM_PROCESSES)

    def cog_unload(self):
        """Need to close the process pool"""
        self.executor.shutdown(cancel_futures=True)

    @commands.group(name='bf', invoke_without_command=True)
    async def bf(self, ctx: commands.Context, program: str):
        # TODO FIGURE OUT CLEAN WAY TO DO INPUT
        try:
            instance = BFInstance(program)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(self.executor, instance.run, self.TIMEOUT)
        except BFError as e:
            await ctx.send(f'{ctx.author.mention} {e}')
        except Exception:
            await ctx.send(f'{ctx.author.mention} Sorry! An internal error occured')
            raise
        await ctx.send(f'{ctx.author.mention} Output:```{result}```')


def setup(bot):
    bot.add_cog(BF(bot))
