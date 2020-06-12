"""Stores utility functions"""
import re
from typing import AsyncIterable, Match, Optional, Pattern, Tuple, Union

AUTHORS_PATTERN: Pattern = re.compile(r'( ?<@!?[0-9]+>)+$')
BASIC_INT_PATTERN: Pattern = re.compile(r'[0-9]+')
GET_NUMBER_PATTERN: Pattern = re.compile(r' ?([0-9]+)$')


async def async_enumerate(iterable: AsyncIterable, start: int = 0):
    async for i in iterable:
        yield start, i
        start += 1


def create_mention(id_: Union[str, int]) -> str:
    return f'<@!{id_}>'


def get_ending_tags(text: str) -> Tuple[Optional[Tuple[int]], str]:
    match: Match = AUTHORS_PATTERN.search(text)
    if not match:
        return None, text
    start = match.start()
    text, authors = text[:start], text[start:]
    author_ids: Set = set(BASIC_INT_PATTERN.findall(authors))
    return tuple(map(int, author_ids)), text.strip()


def get_number_matches(text: str) -> Tuple[Optional[int], str]:
    """Returns number from the end of string or None if no number is found, along with the remainder of string"""
    match: Match = GET_NUMBER_PATTERN.match(text)
    if match is None:
        return None, text
    return int(match.group(1)), text[:match.start()].strip()
