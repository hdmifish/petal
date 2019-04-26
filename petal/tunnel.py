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

    def activate(self):
        self.active = True
        create_task(self.run_tunnel())

    def convert(self, src):
        pass

    async def broadcast(
        self,
        content: str = None,
        embed: discord.Embed = None,
        file=None,
        exclude: list = None,
    ):
        if content or embed or file:
            for gate in self.connected:
                if gate not in exclude:
                    gate.send(content=content, embed=embed, file=file)

    async def close(self):
        pass

    async def drop(self, gateway):
        pass

    async def kill(self):
        self.active = False
        if self.waiting:
            # TODO: Learn how to cancel self.waiting or force an early timeout.
            pass

    async def receive(self, msg: discord.Message):
        content = msg.content
        embeds = msg.embeds
        files = msg.attachments
        await self.broadcast(content, embeds, files, [msg.channel])  # TODO

    async def run_tunnel(self):
        while self.active:
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
                await self.kill()
            else:
                await self.receive(msg)
        await self.close()
