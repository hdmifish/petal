from abc import abstractmethod
from asyncio import Future
from datetime import timedelta
from typing import (
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    Generator,
    List,
    Optional,
    NewType,
    TypeVar,
    Union,
)

import discord


kwopt: type = NewType("Keyword Option", Union[bool, float, int, str])
T1 = TypeVar("T1")
T2 = TypeVar("T2")
Args = NewType("Arguments", List[str])
Response = NewType(
    "Command Return",
    Union[AsyncGenerator, Coroutine, dict, Generator, list, str, tuple],
)
Src = NewType("Discord Message", discord.Message)
Printer = NewType(
    "Reply Method", Callable[[Src, Response, Optional[discord.Message]], None]
)


class TunnelABC(object):
    @abstractmethod
    async def activate(self) -> Future:
        ...

    @abstractmethod
    async def broadcast(
        self,
        content: str = None,
        embed: discord.Embed = None,
        file: discord.File = None,
        exclude: List[int] = None,
    ) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def drop(self, gate: discord.TextChannel) -> None:
        ...

    @abstractmethod
    async def kill(self, final: str = "") -> None:
        ...

    @abstractmethod
    async def receive(self, msg: discord.Message) -> None:
        ...

    @abstractmethod
    async def run_tunnel(self) -> None:
        ...


class PetalClientABC(discord.Client):
    @property
    @abstractmethod
    def uptime(self) -> timedelta:
        ...

    @staticmethod
    @abstractmethod
    def is_pm(message: discord.Message) -> bool:
        ...

    @staticmethod
    @abstractmethod
    def remove_prefix(content: str) -> str:
        ...

    @property
    @abstractmethod
    def main_guild(self) -> discord.Guild:
        ...

    @abstractmethod
    async def status_loop(self) -> None:
        ...

    @abstractmethod
    async def save_loop(self) -> None:
        ...

    @abstractmethod
    async def ask_patch_loop(self) -> None:
        ...

    @abstractmethod
    async def ban_loop(self) -> None:
        ...

    @abstractmethod
    async def close_tunnels_to(self, channel: int) -> None:
        ...

    @abstractmethod
    async def dig_tunnel(
        self, origin: discord.abc.Messageable, *channels: List[int], anon: bool = False
    ) -> Coroutine:
        ...

    @abstractmethod
    def get_tunnel(self, channel: discord.abc.Messageable) -> TunnelABC:
        ...

    @abstractmethod
    async def kill_tunnel(self, t: TunnelABC) -> None:
        ...

    @abstractmethod
    def remove_tunnel(self, t: TunnelABC) -> None:
        ...

    @abstractmethod
    async def on_member_ban(self, member: discord.Member) -> None:
        ...

    @abstractmethod
    async def on_ready(self) -> None:
        ...

    @abstractmethod
    async def print_response(
        self, message: discord.Message, response: Response, to_edit: discord.Message = None
    ) -> None:
        ...

    @abstractmethod
    async def execute_command(self, message: Src) -> bool:
        ...

    @abstractmethod
    async def send_message(
        self,
        author: discord.Member = None,
        channel: discord.abc.Messageable = None,
        message: str = None,
        *,
        embed: discord.Embed = None,
        **_
    ) -> Optional[discord.Message]:
        ...

    @abstractmethod
    async def log_membership(
        self, content: str = None, *, embed: discord.Embed = None
    ) -> Optional[discord.Message]:
        ...

    @abstractmethod
    async def log_moderation(
        self, content: str = None, *, embed: discord.Embed = None
    ) -> Optional[discord.Message]:
        ...

    @abstractmethod
    async def embed(
        self,
        channel: discord.abc.Messageable,
        embedded: discord.Embed,
        content: str = None,
    ) -> discord.Message:
        ...

    @abstractmethod
    async def on_member_join(self, member: discord.Member) -> None:
        ...

    @abstractmethod
    async def on_member_remove(self, member: discord.Member) -> None:
        ...

    @abstractmethod
    async def on_message_delete(self, message: discord.Message) -> None:
        ...

    @abstractmethod
    async def on_message_edit(
        self, before: Src, after: Src
    ) -> None:
        ...

    @abstractmethod
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        ...

    @abstractmethod
    async def on_message(self, message: discord.Message) -> None:
        ...
