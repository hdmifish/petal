"""Module dedicated to utilities concerning Discord Messages."""

from typing import Any, AsyncIterator, Callable, Dict, Iterator, NamedTuple, TypeVar

import discord

from ..checks import Messages


T = TypeVar("T")


class Pair(NamedTuple):
    iterator: AsyncIterator
    last: T


async def aitermux(
    *iters: AsyncIterator[T],
    key: Callable[[T], Any],
    limit: int = 0,
    reverse: bool = False,
    shortest: bool = False,
) -> AsyncIterator[T]:
    """Return a Generator to "multiplex" Asynchronous Iterators, with their
        outputs sorted by some Key Function.

    The only caveat with this is that each Iterator must yield at least one
        value before the Generator can yield any at all.
    """
    limited: bool = limit > 0

    # Associate Iterators with their most recent Yields.
    lasts: Dict[AsyncIterator, Pair] = {}

    for ITER in iters:
        try:
            p: Pair = Pair(ITER, await ITER.__anext__())
        except StopAsyncIteration:
            pass
        else:
            lasts[ITER] = p

    async def increment(iterator: AsyncIterator) -> None:
        try:
            lasts[iterator] = Pair(iterator, await iterator.__anext__())
        except StopAsyncIteration:
            if shortest:
                # We have been told to stop once the shortest is exhausted.
                raise
            else:
                # Everything must go.
                del lasts[iterator]

    def key_true(o: Pair) -> Any:
        return key(o.last)

    while lasts and (not limited or limit > 0):
        item: Pair = (
            max(lasts.values(), key=key_true)
            if reverse
            else min(lasts.values(), key=key_true)
        )
        yield item.last

        try:
            await increment(item.iterator)
        except StopAsyncIteration:
            break
        else:
            limit -= 1


def member_message_history(
    member: discord.Member,
    *,
    limit: int = 0,
    before=None,
    after=None,
    around=None,
    oldest_first: bool = None,
) -> AsyncIterator[discord.Message]:
    iters: Iterator[Iterator[discord.Message]] = (
        (
            msg
            async for msg in channel.history(
                before=before, after=after, around=around, oldest_first=oldest_first
            )
            if msg.author == member
        )
        for channel in member.guild.text_channels
    )
    return aitermux(*iters, key=(lambda o: o.created_at), limit=limit, reverse=True)


async def read_messages(
    client, channel: discord.TextChannel, limit: int = 0
) -> AsyncIterator[discord.Message]:
    """Return an Asynchronous Generator yielding Discord Messages from a Channel
        as they are received.
    """
    check = Messages.in_channel(channel)
    limited = limit > 0
    while not limited or limit > 0:
        yield await client.wait_for("message", check=check)
        limit -= 1
