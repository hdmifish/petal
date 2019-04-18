from asyncio import ensure_future as create_task, sleep

from discord import Embed, Channel, Message, User


# Assemble all the emoji we need via hexadecimal values.
# I have trust issues when it comes to eclectic characters in my source code, so
#   this makes me feel slightly safer, while also saving space.
letters = [chr(n) for n in range(0x1F1E6, 0x1F200)]
cancel = chr(0x274E)
confirm = chr(0x2705)


def count_votes(allowed: list, votes: list):
    result = {}
    for vote in votes:
        if not vote.me and vote.emoji in allowed:
            key = str(vote.emoji)
            result[key] += 1
    return result


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
        self.master = user

    def add_result(self, result: str, title: str = "Results", overwrite: int = None):
        if overwrite is not None:
            self.em.set_field_at(overwrite, name=title, value=str(result), inline=False)
        else:
            self.em.add_field(name=title, value=str(result), inline=False)
        return self.post()

    async def clear(self):
        await self.client.clear_reactions(self.msg)

    async def close(self, text="[ Interaction Closed ]"):
        if text:
            self.em.description = text
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

    async def setup(self, text: str, selection: list):
        self.em.description = text
        await self.post()
        return create_task(self.add_buttons(selection))

    # ========---
    # Begin methods for actually running the interface
    # ========---

    async def get_one(self, opts: list, time=30) -> str:
        """Ask the user to select ONE of a set of predefined options."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return ""
        selection = [cancel, *letters[:onum]]
        buttons = await self.setup(
            "Select One:\n"
            + "\n".join(["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]),
            selection,
        )

        choice = await self.client.wait_for_reaction(
            selection, user=self.master, timeout=time, message=self.msg
        )
        if not choice or choice.reaction.emoji == cancel:
            result = ""
        else:
            result = opts[letters.index(choice.reaction.emoji)]

        await buttons
        await self.clear()
        return result

    async def get_multi(self, opts: list, time=30) -> list:
        """Ask the user to select ONE OR MORE of a set of predefined options."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return []
        selection = [cancel, *letters[:onum], confirm]
        buttons = await self.setup(
            "Select Multiple and Confirm:\n"
            + "\n".join(["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]),
            selection,
        )

        results = set()
        while True:
            choice = await self.client.wait_for_reaction(
                selection, user=self.master, timeout=time, message=self.msg
            )
            if not choice or choice.reaction.emoji == cancel:
                await buttons
                await self.clear()
                return []
            elif choice.reaction.emoji == confirm:
                break
            else:  # TODO: Check reactions AFTER, do not count during
                results.add(opts[letters.index(choice.reaction.emoji)])

        await buttons
        await self.clear()
        return list(results)

    async def get_bool(self, time=30):
        """Ask the user to click a simple YES or NO."""
        selection = [cancel, confirm]

        self.em.description = "Select Yes or No"
        await self.post()
        adding = create_task(self.add_buttons(selection))

        choice = await self.client.wait_for_reaction(
            selection, user=self.master, timeout=time, message=self.msg
        )
        if not choice:
            result = None
        elif choice.reaction.emoji == confirm:
            result = True
        elif choice.reaction.emoji == cancel:
            result = False
        else:
            result = None

        await adding
        await self.clear()
        return result

    async def get_poll(self, opts: list, time=3600) -> dict:
        """Run a MULTIPLE CHOICE open poll that anyone can answer."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return {}
        selection = letters[:onum]

        buttons = await self.setup(
            "**Poll:** Multiple Choice:\n"
            + "\n".join(["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]),
            selection,
        )

        await buttons
        await sleep(time)

        outcome = count_votes(selection, self.msg.reactions)
        await self.clear()

        # TODO: Dont do this
        self.em.description += "\n\n**__RESULTS:__**"
        for k, v in outcome.items():
            self.em.description += "\n**`{}`**: __`{}`__".format(k, v)
        await self.post()

        return outcome

    async def get_vote(self, time=3600) -> dict:
        """Run a YES OR NO open vote that anyone can answer."""
        selection = [cancel, confirm]

        buttons = await self.setup("**Vote:** Yes or No", selection)

        await buttons
        await sleep(time)

        outcome = count_votes(selection, self.msg.reactions)
        await self.clear()

        # TODO: Dont do this
        self.em.description += "\n\n**__RESULTS:__**"
        for k, v in outcome.items():
            self.em.description += "\n**`{}`**: __`{}`__".format(k, v)
        await self.post()

        return outcome
