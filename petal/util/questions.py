from abc import ABC, abstractmethod
from asyncio import TimeoutError
from dataclasses import dataclass
from typing import Optional

import discord

from petal.menu import Menu
from petal.types import PetalClientABC


@dataclass(frozen=True)
class Question(ABC):
    @abstractmethod
    async def ask(
        self, client: PetalClientABC, channel: discord.TextChannel, user: discord.User
    ):
        raise NotImplementedError


@dataclass(frozen=True)
class ChatReply(Question):
    text: str
    timeout: float = 30

    async def ask(self, client, channel, user) -> Optional[str]:
        await channel.send(self.text)

        try:
            reply: discord.Message = await client.wait_for(
                "message",
                check=(
                    lambda msg: msg.author.id == user.id
                    and msg.channel.id == channel.id
                ),
                timeout=self.timeout,
            )
        except TimeoutError:
            return None
        else:
            return reply.content


@dataclass(frozen=True)
class ConfirmMenu(Question):
    title: str = "Confirm"
    desc: str = ""
    timeout: float = 30

    async def ask(self, client, channel, user) -> Optional[bool]:
        m = Menu(client, channel, self.title, self.desc, user)
        result = await m.get_bool(self.timeout)

        m.add_section(repr(result))
        await m.post()
        return result
