import discord


class Menu:
    def __init__(self, client: discord.Client, title: str, desc: str=None, colour=0x0ACDFF):
        self.client = client
        self.embed = discord.Embed(
                title=title,
                description=desc,
                colour=colour,
            )

    async def post(self, channel: discord.Channel):
        await self.client.embed(channel, self.embed)
