"""Module dedicated to utilities concerning Discord Messages."""

from typing import Dict, List, AsyncIterator

import discord


async def member_message_history(
    member: discord.Member,
    *,
    limit: int = 0,
    before=None,
    after=None,
    around=None,
    oldest_first=None,
) -> AsyncIterator[discord.Message]:
    limited: bool = limit > 0
    key = lambda o: o.created_at

    guild: discord.Guild = member.guild
    chans = guild.text_channels

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

    while not limited or limit > 0:
        recents = sorted(lasts.values(), key=key, reverse=True)
        msg: discord.Message = recents[0]
        yield msg
        await used(msg)
