"""Module dedicated to utilities concerning Discord Messages."""

from typing import AsyncGenerator, Dict, List

import discord

from ..checks import Messages


async def member_message_history(
    member: discord.Member,
    *,
    limit: int = 0,
    before=None,
    after=None,
    around=None,
    oldest_first=None,
) -> AsyncGenerator[discord.Message]:
    limited: bool = limit > 0
    key = lambda o: o.created_at

    guild: discord.Guild = member.guild
    chans: List[discord.TextChannel] = guild.text_channels

    # Associate Channels with the Iterators of their Histories.
    iters: Dict[discord.TextChannel, discord.abc.HistoryIterator] = {
        channel: (
            msg
            async for msg in channel.history(
                before=before, after=after, around=around, oldest_first=oldest_first
            )
            if msg.author == member
        )
        for channel in chans
    }

    # Associate Iterators with their most recent Yields.
    lasts: Dict[discord.abc.HistoryIterator, discord.Message] = {}

    for ITER in iters.values():
        try:
            last: discord.Message = await ITER.__anext__()
        except StopAsyncIteration:
            pass
        else:
            lasts[ITER] = last

    async def used(message: discord.Message) -> None:
        channel: discord.TextChannel = message.channel
        iterator: discord.abc.HistoryIterator = iters[channel]

        try:
            lasts[iterator] = await iterator.__anext__()
        except:
            del lasts[iterator]
            del iters[channel]

    while lasts and (not limited or limit > 0):
        recents = sorted(lasts.values(), key=key, reverse=True)
        msg: discord.Message = recents[0]
        yield msg
        await used(msg)


async def read_messages(
    client, channel: discord.TextChannel, limit: int = 0
) -> AsyncGenerator[discord.Message]:
    """Return an Asynchronous Generator yielding Discord Messages from a Channel
        as they are received.
    """
    check = Messages.in_channel(channel)
    limited = limit > 0
    while not limited or limit > 0:
        yield await client.wait_for("message", check=check)
        limit -= 1
