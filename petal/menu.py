from asyncio import sleep

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
cancel = "❎"
done = "✅"


class Menu:
    def __init__(
        self,
        client,
        channel: Channel,
        title: str,
        desc: str = None,
        user: User = None,
        color=0x0ACDFF,
    ):
        self.client = client
        self.channel = channel
        self.em = Embed(title=title, description=desc, colour=color)
        self.msg = None
        self.user = user

    async def clear(self):
        await self.client.clear_reactions(self.msg)

    async def close(self):
        self.em.description = "[ Interaction Closed ]"
        await self.post()
        await self.clear()

    async def post(self):
        if self.msg:
            self.msg: Message = await self.client.edit_message(self.msg, embed=self.em)
        else:
            self.msg: Message = await self.client.embed(self.channel, self.em)

    async def add_buttons(self, selection: list):
        await self.client.clear_reactions(self.msg)
        for opt in selection:
            await self.client.add_reaction(self.msg, opt)

    async def get_choice(self, opts: list, time=30) -> str:
        onum = len(opts)
        if not 1 <= onum <= len(buttons):
            return ""
        selection = [cancel, *buttons[:onum]]

        self.em.description = "Select One:\n" + "\n".join(
            ["{}: `{}`".format(buttons[i], opts[i]) for i in range(onum)]
        )
        await self.post()
        await self.add_buttons(selection)

        choice = await self.client.wait_for_reaction(
            selection, user=self.user, timeout=time, message=self.msg
        )
        if not choice or choice.reaction.emoji == cancel:
            result = ""
        else:
            result = opts[buttons.index(choice.reaction.emoji)]

        await self.client.clear_reactions(self.msg)
        return result

    async def get_multi(self, opts: list, time=30) -> list:
        onum = len(opts)
        if not 1 <= onum <= len(buttons):
            return []
        selection = [cancel, *buttons[:onum], done]

        self.em.description = "Select Multiple and Confirm:\n" + "\n".join(
            ["{}: `{}`".format(buttons[i], opts[i]) for i in range(onum)]
        )
        await self.post()
        await self.add_buttons(selection)

        results = set()
        while True:
            choice = await self.client.wait_for_reaction(
                selection, user=self.user, timeout=time, message=self.msg
            )
            if not choice or choice.reaction.emoji == cancel:
                return []
            elif choice.reaction.emoji == done:
                break
            else:
                results.add(opts[buttons.index(choice.reaction.emoji)])

        await self.client.clear_reactions(self.msg)
        return list(results)

    async def get_poll(self, opts: list, time=3600) -> dict:
        onum = len(opts)
        if not 1 <= onum <= len(buttons):
            return {}
        selection = buttons[:onum]
        outcome = {key: 0 for key in opts}

        self.em.description = "\n".join(
            ["{}: `{}`".format(buttons[i], opts[i]) for i in range(onum)]
        )
        await self.post()
        await self.add_buttons(selection)

        await sleep(time)

        votes = self.msg.reactions
        for vote in votes:
            if not vote.me and vote.emoji in opts:
                key = opts[buttons.index(vote.emoji)]
                outcome[key] += 1
        await self.client.clear_reactions(self.msg)

        self.em.description += "\n\n**__RESULTS:__**"
        for k, v in outcome.items():
            self.em.description += "\n**`{}`**: __`{}`__".format(k, v)
        await self.post()

        return outcome
