from asyncio import create_task, sleep, Task
from collections import Counter
from datetime import datetime as dt, timedelta as td
from itertools import chain
from typing import Dict, List, Optional, Sequence, Tuple, TypeVar

from discord import abc, Embed, TextChannel, Message, Reaction, User

from .util.cdn import get_avatar
from .checks import all_checks, Reactions


# Assemble all the emoji we need via hexadecimal values.
# I have trust issues when it comes to eclectic characters in my source code, so
#   this makes me feel slightly safer.
letters: Tuple[str, ...] = tuple(map(chr, range(0x1F1E6, 0x1F200)))
cancel: str = chr(0x1F6AB)
confirm: str = chr(0x2611)
# Alternatives:
#   Red X:          0x274C
#   Green X:        0x274E
#   Green Check:    0x2705
#   "Do Not Enter": 0x26D4

# Zodiac icons because why not
astro: Tuple[str, ...] = tuple(chr(n) for n in range(0x2648, 0x2654))
info: str = chr(0x2139)  # [i]
okay: str = chr(0x1F197)  # [OK]

clock: Tuple[str, ...] = (chr(0x1F55C), *(chr(n) for n in range(0x1F550, 0x1F55B)))


# List of all long-term Menu Operations, as Tasks. Before Shutdown, these can be
#   cancelled en masse to have the Messages get cleaned up.
live: List[Task] = []

T_ = TypeVar("T_")


def count_votes(allowed: Sequence[str], votes: Sequence[Reaction]) -> Counter:
    allowed: List[str] = [str(a).casefold() for a in allowed]
    return Counter(
        {
            str(vote.emoji): (vote.count - 1) if vote.me else vote.count
            for vote in votes
            if str(vote.emoji).casefold() in allowed
        }
    )


class Menu:
    def __init__(
        self,
        client,
        channel: TextChannel,
        title: str,
        desc: str = None,
        user: User = None,
        colour: int = 0x_0A_CD_FF,
    ):
        self.client = client
        self.channel: abc.Messageable = channel
        self.em: Embed = Embed(title=title, description=desc, colour=colour)
        self.em.set_author(name=user.display_name, icon_url=get_avatar(user))
        self.msg: Optional[Message] = None
        self.master: User = user

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
        if self.msg and self.em not in self.msg.embeds:
            await self.msg.edit(embed=self.em)
        else:
            self.msg: Message = await self.channel.send(embed=self.em)

    async def _add_buttons(self, selection: Sequence):
        await self.msg.clear_reactions()
        for opt in selection:
            await self.msg.add_reaction(opt)

    async def add_buttons(self, selection: Sequence) -> Task:
        if not self.msg:
            await self.post()
        return create_task(self._add_buttons(selection))

    # ========---
    # Begin methods for actually running the interface
    # ========---

    ### PRIVATE interfaces; Only one person may respond.

    async def get_one(
        self, opts: Sequence[T_], time: float = 30, title: str = "Select One"
    ) -> Optional[T_]:
        """Ask the user to select ONE of a set of predefined options."""
        if not 1 <= len(opts) <= len(letters):
            return None

        letopt = dict(zip(letters, opts))
        selection = [cancel, *letopt]
        self.add_section(
            "\n".join(f"{letter}: `{opt}`" for letter, opt in letopt.items()), title
        )
        await self.post()
        buttons: Task = await self.add_buttons(selection)

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
            result = None
        else:
            result = letopt.get(choice.emoji)

        await buttons
        await self.clear()
        return result

    async def get_multi(
        self,
        opts: Sequence[T_],
        time: float = 30,
        prompt: str = "Select One or More and Confirm:",
        title: str = "Multiple Choice",
    ) -> Tuple[T_, ...]:
        """Ask the user to select ONE OR MORE of a set of predefined options."""
        if not 1 <= len(opts) <= len(letters):
            return ()

        letopt = dict(zip(letters, opts))
        selection = [cancel, *letopt, confirm]
        self.add_section(
            "\n".join(
                chain(
                    [prompt], (f"{letter}: `{opt}`" for letter, opt in letopt.items())
                )
            ),
            title,
        )
        await self.post()
        buttons: Task = await self.add_buttons(selection)

        ok = (str(cancel), str(confirm))
        pre = all_checks(Reactions.by_user(self.master), Reactions.on_message(self.msg))

        def check(react_: Reaction, user: User) -> bool:
            return pre(react_, user) and str(react_.emoji) in ok

        choice = (await Reactions.waitfor(self.client, check, timeout=time))[0]

        if not choice or choice.emoji == cancel:
            await self.clear()
            return ()

        try:
            vm: Message = await self.channel.fetch_message(self.msg.id)
        except:
            await self.clear()
            return ()

        results: Tuple[T_, ...] = tuple(
            [
                letopt.get(react.emoji)
                for react in vm.reactions
                if (
                    react.emoji in selection[1:-1]
                    and self.master in await react.users().flatten()
                )
            ]
        )

        await buttons
        await self.clear()
        return results

    async def get_bool(
        self,
        time: float = 30,
        # prompt: str = "Select Yes or No",
        # title: str = "Boolean Choice",
    ) -> Optional[bool]:
        """Ask the user to click a simple YES or NO."""
        selection = (confirm, cancel)

        # self.em.description = prompt or "Select Yes or No"
        # await self.post()
        # adding = create_task(self.add_buttons(selection))
        # self.add_section(prompt, title)
        # await self.post()
        adding: Task = await self.add_buttons(selection)

        choice = (
            await Reactions.waitfor(
                self.client,
                all_checks(
                    Reactions.by_user(self.master), Reactions.on_message(self.msg)
                ),
                timeout=time,
            )
        )[0]

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

    async def get_poll(
        self,
        opts: Sequence[T_],
        time: int = 3600,
        prompt: str = "Select One or More:",
        title: str = "Poll",
    ) -> Dict[T_, int]:
        """Run a MULTIPLE CHOICE open poll that anyone can answer."""
        if not 1 <= len(opts) <= len(letters):
            return {}

        letopt = dict(zip(letters, opts))
        selection = list(letopt)
        do_footer = not self.em.footer and not self.em.timestamp

        self.add_section(
            "\n".join(
                chain(
                    [prompt], (f"{letter}: `{opt}`" for letter, opt in letopt.items())
                )
            ),
            title,
        )
        if do_footer:
            self.em.set_footer(text="Poll Ends").timestamp = dt.utcnow() + td(
                seconds=time
            )

        await self.post()
        await (await self.add_buttons(selection))
        await sleep(time)

        try:
            vm = await self.channel.fetch_message(self.msg.id)
        except:
            return {}

        outcome = count_votes(selection, vm.reactions)
        await self.clear()

        self.add_section(
            "\n".join("{}: **{}**".format(letopt.get(k), v) for k, v in outcome.items())
        )
        if do_footer:
            self.em.set_footer(text="").timestamp = Embed.Empty

        await self.post()

        return outcome

    async def get_vote(self, time: int = 3600) -> Dict[bool, int]:
        """Run a YES OR NO open vote that anyone can answer."""
        selection = (confirm, cancel)
        do_footer = not self.em.footer and not self.em.timestamp

        if do_footer:
            self.em.set_footer(text="Vote Ends").timestamp = dt.utcnow() + td(
                seconds=time
            )

        await self.post()
        await (await self.add_buttons(selection))
        await sleep(time)

        try:
            vm = await self.channel.fetch_message(self.msg.id)
        except:
            return {}

        outcome = count_votes(selection, vm.reactions)
        await self.clear()

        real = {True: outcome.get(confirm, 0), False: outcome.get(cancel, 0)}

        self.add_section(
            "\n".join(
                "**{}**: **{}**".format("Yes" if k else "No", v)
                for k, v in real.items()
            )
        )
        if do_footer:
            self.em.set_footer(text="").timestamp = Embed.Empty

        await self.post()

        return real


async def confirm_action(
    client, src: Message, title: str, desc: str, timeout: int = 30
) -> Optional[bool]:
    author: User = src.author
    channel: TextChannel = src.channel

    m = Menu(client, channel, title, desc, author)
    return await m.get_bool(timeout)
