from asyncio import ensure_future as create_task #, sleep
from typing import Optional

from discord import Embed, TextChannel, Message, User

from petal.checks import all_checks, Reactions


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
        desc: str,
        user: User = None,
        colour=0x0ACDFF,
    ):
        self.client = client
        self.channel = channel
        self.em = Embed(title=title, description=desc, colour=colour)
        self.msg = None
        self.master = user

    def add_section(self, result: str, title: str = "Results", overwrite: int = None):
        if overwrite is not None:
            self.em.set_field_at(overwrite, name=title, value=str(result), inline=False)
        else:
            self.em.add_field(name=title, value=str(result), inline=False)

    async def clear(self):
        await self.msg.clear_reactions()

    async def close(self, text=""):
        if text:
            self.em.description = text
            await self.post()
        await self.clear()

    async def post(self):
        if self.msg:
            await self.msg.edit(embed=self.em)
        else:
            self.msg: Message = await self.channel.send(embed=self.em)

    async def _add_buttons(self, selection: list):
        await self.msg.clear_reactions()
        for opt in selection:
            await self.msg.add_reaction(opt)

    async def add_buttons(self, selection: list):
        if not self.msg:
            await self.post()
        return create_task(self._add_buttons(selection))

    # ========---
    # Begin methods for actually running the interface
    # ========---

    ### PRIVATE interfaces; Only one person may respond.

    async def get_one(
        self, opts: list, time=30, prompt="Select One:", title="Choice"
    ) -> str:
        """Ask the user to select ONE of a set of predefined options."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return ""
        selection = [cancel, *letters[:onum]]
        self.add_section(
            "\n".join(
                [prompt] + ["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]
            ),
            title,
        )
        buttons = await self.add_buttons(selection)
        await self.post()

        choice = (
            await Reactions.waitfor(
                self.client,
                all_checks(
                    Reactions.by_user(self.master), Reactions.on_message(self.msg)
                ),
                timeout=time,
            )
        )[0]

        if not choice or choice.emoji == cancel:
            result = ""
        else:
            result = opts[letters.index(choice.emoji)]

        await buttons
        await self.clear()
        return result

    async def get_multi(
        self,
        opts: list,
        time=30,
        prompt="Select One or More and Confirm:",
        title="Multiple Choice",
    ) -> list:
        """Ask the user to select ONE OR MORE of a set of predefined options."""
        onum = len(opts)
        if not 1 <= onum <= len(letters):
            return []
        selection = [cancel, *letters[:onum], confirm]
        self.add_section(
            "\n".join(
                [prompt] + ["{}: `{}`".format(letters[i], opts[i]) for i in range(onum)]
            ),
            title,
        )
        buttons = await self.add_buttons(selection)
        await self.post()

        def check(react_, user):
            return all_checks(
                Reactions.by_user(self.master), Reactions.on_message(self.msg)
            )(react_, user) and str(react_.emoji) in [str(cancel), str(confirm)]

        choice = (await Reactions.waitfor(self.client, check, timeout=time))[0]

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

    async def get_bool(
        self, time=30, prompt="Select Yes or No", title="Boolean Choice"
    ) -> Optional[bool]:
        """Ask the user to click a simple YES or NO."""
        selection = [cancel, confirm]

        # self.em.description = prompt or "Select Yes or No"
        # await self.post()
        # adding = create_task(self.add_buttons(selection))
        self.add_section(prompt, title)
        adding = await self.add_buttons(selection)
        await self.post()

        choice = (
            await Reactions.waitfor(
                self.client,
                all_checks(
                    Reactions.by_user(self.master), Reactions.on_message(self.msg)
                ),
                timeout=time,
            )
        )[0]
        print(choice)

        await adding
        await self.clear()

        if not choice:
            return None
        elif choice.emoji == confirm:
            return True
        elif choice.emoji == cancel:
            return False
        else:
            return None

    ### PUBLIC interfaces; ANYONE may respond.

    # async def get_poll(self, opts: list, time=3600) -> dict:
    #     """Run a MULTIPLE CHOICE open poll that anyone can answer."""
    #     onum = len(opts)
    #     if not 1 <= onum <= len(letters):
    #         return {}
    #     selection = letters[:onum]
    #
    #     buttons = await self.add_buttons(
    #         "**Poll:** Multiple Choice:\n"
    #         + "\n".join((f"{letters[i]}: `{opts[i]}`" for i in range(onum))),
    #         selection,
    #     )
    #
    #     await buttons
    #     await sleep(time)
    #
    #     try:
    #         vm = await self.channel.fetch_message(self.msg.id)
    #     except:
    #         return {}
    #
    #     outcome = count_votes(selection, vm.reactions)
    #     await self.clear()
    #
    #     self.em.description += "\n\n**__RESULTS:__**"
    #     for k, v in outcome.items():
    #         self.em.description += "\n**`{}`**: __`{}`__".format(
    #             opts[letters.index(k)], v
    #         )
    #     await self.post()
    #
    #     return outcome

    # async def get_vote(self, time=3600) -> dict:
    #     """Run a YES OR NO open vote that anyone can answer."""
    #     selection = [cancel, confirm]
    #
    #     buttons = await self.add_buttons("**Vote:** Yes or No", selection)
    #
    #     await buttons
    #     await sleep(time)
    #
    #     try:
    #         vm = await self.channel.fetch_message(self.msg.id)
    #     except:
    #         return {}
    #
    #     outcome = count_votes(selection, vm.reactions)
    #     await self.clear()
    #
    #     self.em.description += "\n\n**__RESULTS:__**"
    #     for k, v in outcome.items():
    #         self.em.description += "\n**`{}`**: __`{}`__".format(k, v)
    #     await self.post()
    #
    #     return outcome


async def confirm_action(
    client,
    src: Message,
    title: str,
    desc: str,
    prompt: str = "Select Yes or No",
    section_title: str = "Boolean Choice",
    timeout: int = 30
) -> Optional[bool]:
    author: User = src.author
    channel: TextChannel = src.channel

    m = Menu(client, channel, title, desc, author)
    return await m.get_bool(timeout, prompt, section_title)
