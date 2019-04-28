"""Chat Tunneling module for Petal

Manage bridges between Messageables, such as two DMs, or a DM and a Channel.
"""

from asyncio import ensure_future as create_task, CancelledError, TimeoutError

import discord

from petal.exceptions import TunnelSetupError


class Tunnel:
    def __init__(self, client, origin, *gates, anonymous=False, timeout=600):
        self.anon = anonymous
        self.client = client
        self.gates = {origin.id, *gates}
        self.timeout = timeout

        self.active = False
        self.connected = []
        # self.names_c = {}  # Channel aliases
        # self.names_u = {}  # User aliases

        self.origin = origin
        self.waiting = None

    async def activate(self):
        for c_id in [i for i in self.gates if type(i) == int]:
            channel = self.client.get_channel(c_id)
            user = self.client.get_user(c_id)
            if user and not channel:
                channel = user.dm_channel or await user.create_dm()

            if channel:
                if not self.client.get_tunnel(channel):
                    try:
                        await channel.send("Connecting to Messaging Tunnel...")
                    except discord.Forbidden as e:
                        await self.origin.send(
                            "Failed to connect to `{}`: {}".format(channel.id, e)
                        )
                    else:
                        self.connected.append(channel)
                else:
                    await self.origin.send(
                        "Failed to connect to {}: "
                        "Channel is already Tunneling.".format(channel.mention)
                    )
            else:
                await self.origin.send(
                    "Failed to connect to `{}`: "
                    "Channel or User not found.".format(c_id)
                )
        if len(self.connected) < 2:
            await self.broadcast("Failed to establish Tunnel.")
            self.connected = []
            raise TunnelSetupError()
        else:
            self.active = True
            create_task(self.run_tunnel())
            await self.broadcast(
                "Messaging Tunnel between {} channels established. "
                "Invoke `{}disconnect` to disconnect from the Tunnel.".format(
                    len(self.connected), self.client.config.prefix
                )
            )

    def convert(self, src):
        em = discord.Embed(
            description=src.content,
            timestamp=src.created_at,
            title="Message from `#{}`".format(src.channel.name)
            if hasattr(src.channel, "name")
            else "Message via DM",
        ).set_author(name=src.author.display_name, icon_url=src.author.avatar_url)
        return {"embed": em}

    async def broadcast(
        self,
        content: str = None,
        embed: discord.Embed = None,
        file=None,
        exclude: list = None,
    ):
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
        for gate in self.connected:
            await self.drop(gate)
        self.client.remove_tunnel(self)

    async def drop(self, gate):
        while gate in self.connected:
            self.connected.remove(gate)
        if self.active:
            await self.broadcast("One endpoint has disconnected.")

    async def kill(self, final=""):
        if final:
            await self.broadcast(final)
        self.active = False
        if self.waiting:
            self.waiting.cancel()

    async def receive(self, msg: discord.Message):
        await self.broadcast(exclude=[msg.channel.id], **self.convert(msg))

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
                await self.broadcast("Connection closed: Coroutine cancelled.")
            except TimeoutError:
                # Tunnel timed out.
                await self.kill("Connection closed due to inactivity.")
            else:
                await self.receive(msg)
            finally:
                self.waiting = None
        await self.close()
