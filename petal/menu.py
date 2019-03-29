from discord import Embed, Channel, Message


class Menu:
    def __init__(
        self, client, channel: Channel, title: str, desc: str = None, color=0x0ACDFF
    ):
        self.client = client
        self.channel = channel
        self.em = Embed(title=title, description=desc, colour=color)
        self.msg = None

    async def post(self):
        if self.msg:
            self.msg: Message = await self.client.edit_message(self.msg, embed=self.em)
        else:
            self.msg: Message = await self.client.embed(self.channel, self.em)

    def retitle(self, title):
        self.em.title = title
