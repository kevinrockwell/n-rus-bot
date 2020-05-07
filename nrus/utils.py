"""Stores utility functions"""
from typing import AsyncIterable, Union


async def async_enumerate(iterable: AsyncIterable, start: int = 0):
    async for i in iterable:
        yield start, i
        start += 1


def create_mention(id_: Union[str, int]) -> str:
    return f'<@!{id_}>'
