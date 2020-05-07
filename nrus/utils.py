"""Stores utility functions"""
from typing import AsyncIterable


async def async_enumerate(iterable: AsyncIterable, start: int = 0):
    async for i in iterable:
        yield start, i
        start += 1
