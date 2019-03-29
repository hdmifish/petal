from discord import Embed, Channel, Message, User


buttons = [
    "🇦",
    "🇧",
    "🇨",
    "🇩",
    "🇪",
    "🇫",
    "🇬",
    "🇭",
    "🇮",
    "🇯",
    "🇰",
    "🇱",
    "🇲",
    "🇳",
    "🇴",
    "🇵",
    "🇶",
    "🇷",
    "🇸",
    "🇹",
    "🇺",
    "🇻",
    "🇼",
    "🇽",
    "🇾",
    "🇿",
]
stop = "🛑"


class Menu:
    def __init__(
        self,
        client,
        channel: Channel,
        user: User,
        title: str,
        desc: str = None,
        color=0x0ACDFF,
    ):
        self.client = client
        self.channel = channel
        self.em = Embed(title=title, description=desc, colour=color)
        self.msg = None
        self.user = user

    async def close(self):
        self.em.description = "[ Interaction Closed ]"
        await self.post()
        await self.client.clear_reactions(self.msg)

    async def post(self):
        if self.msg:
            self.msg: Message = await self.client.edit_message(self.msg, embed=self.em)
        else:
            self.msg: Message = await self.client.embed(self.channel, self.em)

    async def add_buttons(self, selection: list):
        await self.client.clear_reactions(self.msg)
        for opt in selection:
            await self.client.add_reaction(self.msg, opt)

    async def get_option(self, opts: list, time=30) -> str:
        onum = len(opts)
        if not self.msg or not 1 <= onum <= len(buttons):
            return ""
        selection = buttons[:onum]

        self.em.description = "\n".join(
            ["{}: `{}`".format(buttons[i], opts[i]) for i in range(onum)]
        )
        await self.post()
        await self.add_buttons(selection)

        result = await self.client.wait_for_reaction(
            selection, user=self.user, timeout=time, message=self.msg
        )
        if not result:
            return ""
        result = opts[buttons.index(result.reaction.emoji)]

        await self.client.clear_reactions(self.msg)
        return result
