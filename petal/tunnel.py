"""Chat Tunneling module for Petal.

Manage bridges between Messageables, such as two DMs, or a DM and a Channel.
"""

from asyncio import ensure_future as create_task, CancelledError, Task, TimeoutError
from typing import List, Optional, Set

import discord

from petal.exceptions import TunnelSetupError
from petal.types import TunnelABC


def mkembed(src: discord.Message):
    """Build a Discord Embed representing the passed Message."""
    em = discord.Embed(
        colour=src.author.colour,
        description=src.content,
        timestamp=src.created_at,
        title=f"Message from `#{src.channel.name}`"
        if hasattr(src.channel, "name")
        else "Message via DM",
    ).set_author(name=src.author.display_name, icon_url=src.author.avatar_url)
    return {"embed": em}


class Tunnel(TunnelABC):
    def __init__(
        self,
        client,
        origin: discord.TextChannel,
        *gates: int,
        anonymous: bool = False,
        timeout: int = 600
    ):
        self.anon: bool = anonymous
        self.client = client
        self.gates: Set[int] = {origin.id, *gates}
        self.timeout: int = timeout

        self.active: bool = False
        self.connected: List[discord.TextChannel] = []
        # self.names_c = {}  # Channel aliases
        # self.names_u = {}  # User aliases

        self.origin: discord.TextChannel = origin
        self.waiting: Optional[Task] = None

    async def activate(self):
        """Resolve all Channel IDs into usable Channel Objects, and store them
            in memory in a List.
        """
        for c_id in self.gates:
            channel: discord.TextChannel = self.client.get_channel(c_id)
            user: discord.User = self.client.get_user(c_id)
            if user and not channel:
                channel: discord.DMChannel = user.dm_channel or await user.create_dm()

            if channel:
                if not self.client.get_tunnel(channel):
                    try:
                        await channel.send("Connecting to Messaging Tunnel...")
                    except discord.Forbidden as e:
                        await self.origin.send(
                            f"Failed to connect to `{channel.id}`: {e}"
                        )
                    else:
                        self.connected.append(channel)
                else:
                    await self.origin.send(
                        f"Failed to connect to `{channel.id}`: Channel is"
                        f" already Tunneling."
                    )
            else:
                await self.origin.send(
                    f"Failed to connect to `{c_id}`: Channel or User not found."
                )
        if len(self.connected) < 2:
            await self.broadcast("Failed to establish Tunnel.")
            self.connected.clear()
            raise TunnelSetupError()
        else:
            self.active = True
            tunnel_coro = create_task(self.run_tunnel())
            await self.broadcast(
                f"Messaging Tunnel established. This Channel is now connected"
                f" directly to {len(self.connected)} other Channels."
            )
            return tunnel_coro

    async def broadcast(
        self,
        content: str = None,
        embed: discord.Embed = None,
        file=None,
        exclude: List[int] = None,
    ):
        """Post a Message with the supplied values to all connected Channels."""
        exclude = exclude or []
        to_drop = []
        if content or embed or file:
            for gate in self.connected:
                if gate.id not in exclude:
                    try:
                        await gate.send(content=content, embed=embed, file=file)
                    except:
                        to_drop.append(gate)
            for gate in to_drop:
                await self.drop(gate)

    async def close(self):
        """Remove all connected Gateways, and remove self from the Tunnels field
            in the Client. If the interface has been used correctly, this will
            cause the Garbage Collector to delete the Tunnel fully.
        """
        for gate in self.connected:
            await self.drop(gate)
        self.client.remove_tunnel(self)

    async def drop(self, gate):
        """Remove a connected Channel from the connected Channels."""
        while gate in self.connected:
            self.connected.remove(gate)
        if self.active:
            await self.broadcast("One endpoint has disconnected.")
        if len(self.connected) < 2:
            await self.kill("Connection closed: No active endpoints.")

    async def kill(self, final=""):
        """Induce this Tunnel to close."""
        if final:
            await self.broadcast(final)
        self.active = False
        if self.waiting:
            self.waiting.cancel()

    async def receive(self, msg: discord.Message):
        """Forward a received Message to all connected Channels."""
        await self.broadcast(exclude=[msg.channel.id], **mkembed(msg))

    async def run_tunnel(self):
        """Begin Tunnel operation loop."""
        while self.active:
            if len(self.connected) < 2:
                await self.kill("Connection closed: No active endpoints.")
                continue
            self.waiting = create_task(
                self.client.wait_for(
                    "message",
                    check=(
                        lambda m: m.channel in self.connected
                        and m.author.id != self.client.user.id
                        and not m.content.startswith(self.client.config.prefix)
                    ),
                    timeout=self.timeout,
                )
            )
            try:
                msg = await self.waiting
            except CancelledError:
                # Tunnel was killed.
                if self.active:
                    await self.broadcast("Connection closed: Coroutine cancelled.")
            except TimeoutError:
                # Tunnel timed out.
                await self.kill("Connection closed due to inactivity.")
            else:
                await self.receive(msg)
            finally:
                self.waiting = None
        await self.close()
