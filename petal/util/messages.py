"""Module dedicated to utilities concerning Discord Messages."""

from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Generator, List, TypeVar

import discord

from ..checks import Messages


T = TypeVar("T")


@dataclass
class Pair:
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

    # To make the Multiplexer transparent, we must wrap the Key Function so that
    #   it will operate on a Pair containing a value, not the value itself.
    def key_true(pair: Pair) -> Any:
        return key(pair.last)

    # Associate Iterators with their most recent Yields.
    lasts: List[Pair] = []
    for ITER in iters:
        try:
            # Get the first Value from each Iterator.
            p = await ITER.__anext__()
        except StopAsyncIteration:
            continue
        else:
            # Store it in a Dataclass next to the Iterator from whence it came.
            lasts.append(Pair(ITER, p))

    # Evaluate Reversal outside the Loop.
    cmp: Callable[..., T] = max if reverse else min
    while lasts and (not limited or limit > 0):
        next_: Pair = cmp(lasts, key=key_true)
        yield next_.last

        try:
            next_.last = await next_.iterator.__anext__()
        except StopAsyncIteration:
            if shortest:
                # We have been told to stop once the shortest is exhausted.
                break
            else:
                # Everything must go.
                lasts.remove(next_)
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
    iters: Generator[Generator[discord.Message]] = (
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
