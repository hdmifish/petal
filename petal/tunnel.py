"""Chat Tunneling module for Petal

Manage bridges between Messageables, such as two DMs, or a DM and a Channel.
"""

from asyncio import ensure_future as create_task

import discord


class Gateway:
    def __init__(self, m_id: int):
        self.id = m_id

        self.channel: discord.abc.Messageable = "TODO: Find channel object from ID"
        self.nicknames = []

    def decode(self, d, field):
        if d.get(field):
            for nick, real in self.nicknames:
                d[field] = d[field].replace(nick, real)

    def encode(self, d, field):
        if d.get(field):
            for nick, real in self.nicknames:
                d[field] = d[field].replace(real, nick)

    async def send(self, **kw):
        self.decode(kw, "content")
        await self.channel.send(**kw)


class Tunnel:
    def __init__(self, client, *gates, anonymous=False, timeout=600):
        self.anon = anonymous
        self.client = client
        self.gates = gates
        self.timeout = timeout

        self.active = False
        self.connected = []
        self.names_c = {}  # Channel aliases
        self.names_u = {}  # User aliases

        self.waiting = None

    async def activate(self):
        for c_id in self.gates:
            channel = self.client.get_channel(c_id)
            if channel:
                try:
                    await channel.send("Connecting to Messaging Tunnel...")
                except discord.Forbidden:
                    pass
                else:
                    self.connected.append(channel)
        if len(self.connected) < 2:
            self.connected = []
            await self.broadcast("Failed to establish Tunnel.")
        else:
            self.active = True
            create_task(self.run_tunnel())
            await self.broadcast(
                "Messaging Tunnel between {} channels established.".format(
                    len(self.connected)
                )
            )

    def convert(self, src):
        em = discord.Embed(
            description=src.content,
            timestamp=src.created_at,
            title="Message from `{}`".format(src.channel.name),
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

    async def drop(self, gate):
        if gate in self.connected:
            self.connected.remove(gate)

    async def kill(self, final=""):
        if final:
            await self.broadcast(final)
        self.active = False
        if self.waiting:
            # TODO: Learn how to cancel self.waiting or force an early timeout.
            pass

    async def receive(self, msg: discord.Message):
        await self.broadcast(exclude=[msg.channel.id], **self.convert(msg))

    async def run_tunnel(self):
        """Begin Tunnel operation loop."""
        while self.active:
            if len(self.connected) < 2:
                await self.kill("Connection closed: No other endpoints.")
                continue
            self.waiting = self.client.wait_for(
                "message",
                check=(
                    lambda m: m.channel in self.connected
                    and m.author.id != self.client.user.id
                ),
                timeout=self.timeout,
            )
            msg = await self.waiting
            self.waiting = None
            if msg is None:
                # Tunnel timed out.
                await self.kill("Connection closed due to inactivity.")
            else:
                await self.receive(msg)
        await self.close()
