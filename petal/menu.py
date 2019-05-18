from asyncio import ensure_future as create_task, sleep, TimeoutError

from discord import Embed, TextChannel, Message, User


# Assemble all the emoji we need via hexadecimal values.
# I have trust issues when it comes to eclectic characters in my source code, so
#   this makes me feel slightly safer, while also saving space.
letters = [chr(n) for n in range(0x1F1E6, 0x1F200)]
cancel = chr(0x274E)
confirm = chr(0x2705)

astro = [chr(n) for n in range(0x2648, 0x2654)]  # Zodiac icons because why not
info = chr(0x2139)  # [i]
okay = chr(0x1F197)  # [OK]

clock = [chr(n) for n in range(0x1F550, 0x1F55C)]
clock[0:0] = [clock.pop(-1)]  # Clock symbols: [12, 1, 2, ..., 11]


react_same_user = lambda user: lambda r, u: u == user
react_same_msg = lambda msg: lambda r, u: r.message.id == msg.id
react_same_user_and_msg = (
    lambda user, msg: lambda r, u: u.id == user.id and r.message.id == msg.id
)


def count_votes(allowed: list, votes: list):
    allowed = [str(a) for a in allowed]
    result = {}
    for vote in votes:
        key = str(vote.emoji)
        if key in allowed:
            result[key] = vote.count
            if vote.me:
                result[key] -= 1
    return result


class Menu:
    def __init__(
        self,
        client,
        channel: TextChannel,
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
        await self.msg.clear_reactions()

    async def close(self, text="[ Interaction Closed ]"):
        if text:
            self.em.description = text
            await self.post()
        await self.clear()

    async def post(self):
        if self.msg:
            await self.msg.edit(embed=self.em)
        else:
            self.msg: Message = await self.channel.send(embed=self.em)

    async def add_buttons(self, selection: list):
        await self.msg.clear_reactions()
        for opt in selection:
            await self.msg.add_reaction(opt)

    async def setup(self, text: str, selection: list):
        self.em.description = text
        await self.post()
        return create_task(self.add_buttons(selection))

    # ========---
    # Begin methods for actually running the interface
    # ========---

    async def get_one(self, opts: list, time=30, prompt="") -> str:
        """Ask the user to select ONE of a set of predefined options."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return ""
        selection = [cancel, *letters[:onum]]
        buttons = await self.setup(
            (prompt or "Select One:")
            + "\n"
            + "\n".join(["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]),
            selection,
        )

        try:
            choice, _ = await self.client.wait_for(
                "reaction_add",
                timeout=time,
                check=react_same_user_and_msg(self.master, self.msg),
            )
        except TimeoutError:
            choice = None

        if not choice or choice.emoji == cancel:
            result = ""
        else:
            result = opts[letters.index(choice.emoji)]

        await buttons
        await self.clear()
        return result

    async def get_multi(self, opts: list, time=30, prompt="") -> list:
        """Ask the user to select ONE OR MORE of a set of predefined options."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return []
        selection = [cancel, *letters[:onum], confirm]
        buttons = await self.setup(
            (prompt or "Select One or More and Confirm:")
            + "\n"
            + "\n".join(["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]),
            selection,
        )

        def check(react_, user):
            return react_same_user_and_msg(self.master, self.msg)(react_, user) and str(
                react_.emoji
            ) in [str(cancel), str(confirm)]

        try:
            choice, _ = await self.client.wait_for(
                "reaction_add", timeout=time, check=check
            )
        except TimeoutError:
            choice = None

        if not choice or choice.emoji == cancel:
            await self.clear()
            return []

        try:
            vm = await self.channel.fetch_message(self.msg.id)
        except:
            await self.clear()
            return []

        results = []
        for react in vm.reactions:
            if react.emoji in [r for r in selection[1:-1]] and self.master.id in [
                u.id for u in await react.users().flatten()
            ]:
                results.append(opts[letters.index(react.emoji)])

        await buttons
        await self.clear()
        return results

    async def get_bool(self, time=30, prompt=""):
        """Ask the user to click a simple YES or NO."""
        selection = [cancel, confirm]

        self.em.description = prompt or "Select Yes or No"
        await self.post()
        adding = create_task(self.add_buttons(selection))

        try:
            choice, _ = await self.client.wait_for(
                "reaction_add",
                timeout=time,
                check=react_same_user_and_msg(self.master, self.msg),
            )
        except TimeoutError:
            choice = None

        if not choice:
            result = None
        elif choice.emoji == confirm:
            result = True
        elif choice.emoji == cancel:
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

        try:
            vm = await self.channel.fetch_message(self.msg.id)
        except:
            return {}

        outcome = count_votes(selection, vm.reactions)
        await self.clear()

        self.em.description += "\n\n**__RESULTS:__**"
        for k, v in outcome.items():
            self.em.description += "\n**`{}`**: __`{}`__".format(
                opts[letters.index(k)], v
            )
        await self.post()

        return outcome

    async def get_vote(self, time=3600) -> dict:
        """Run a YES OR NO open vote that anyone can answer."""
        selection = [cancel, confirm]

        buttons = await self.setup("**Vote:** Yes or No", selection)

        await buttons
        await sleep(time)

        try:
            vm = await self.channel.fetch_message(self.msg.id)
        except:
            return {}

        outcome = count_votes(selection, vm.reactions)
        await self.clear()

        self.em.description += "\n\n**__RESULTS:__**"
        for k, v in outcome.items():
            self.em.description += "\n**`{}`**: __`{}`__".format(k, v)
        await self.post()

        return outcome
