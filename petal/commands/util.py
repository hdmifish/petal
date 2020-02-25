"""Commands module for BOT-RELATED UTILITIES.
Access: Public"""

from collections import OrderedDict
from datetime import datetime as dt
from functools import partial
from re import compile
from string import punctuation
from typing import get_type_hints, List, Tuple

import dateparser
import discord
import pytz

from petal.commands import core
from petal.exceptions import (
    CommandArgsError,
    CommandAuthError,
    CommandInputError,
    CommandOperationError,
)
from petal.util import cdn, fmt
from petal.util.bits import bytes_to_braille, chunk
from petal.util.embeds import Color
from petal.util.messages import member_message_history


# Reference: strftime.org
tstring = "**`%H:%M`** %Z on %A, %B %d, %Y"
helptext = [
    """An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.""",
    """While spaces separate Arguments, sometimes an Argument is desired to be multiple words. In these cases, one can simply enclose the argument in quotes; For example:```{p}command "asdf qwert" zxcv```This would pass only *two* arguments to the command: `"asdf qwert"` and `"zxcv"`.""",
    """An __Option__ is an additional Argument passed to a command, prefixed by either `-` or `--`, which is optional. An Option prefixed by `-` is a "Short" Option, while an Option prefixed by `--` is a "Long" Option. A Long Option may also have its value specified with a `=` instead of a space and a string, and additionally, only needs enough of the word to be uniquely identified. For example:```{p}command --option asdf\n{p}command --option=asdf\n{p}command --opt asdf```If you were to run one of these, you would pass the Long Option, `option`, into the command with the value of `"asdf"`. It is up to the `cmd_command()` method to accept and use this value somehow.""",
    """A __Flag__ is an Option passed without an explicit value, such as in:```{p}command --verbose```In this example, `verbose` is passed into the command with a **boolean** value of `True`, rather than any string value. This is often used by commands that may optionally return more or less information if requested.""",
    """Short Options may be grouped together as a single prefixed word, or cluster. This can save time when typing a command with a series of Flags, but it is less useful when values need to be passed, because only the final Short Option in a cluster will be assigned the value specified. For example:```{p}command -abc 23 --long1 xyz --long2```In this command, while `c` is passed with a value of `"23"`, `a` and `b` are simply passed with values of `True`. This is the same difference by which the Long Option `long1` is passed with the value `"xyz"` while `long2` is passed with the value `True`.""",
]


us_cap = partial(compile(r"\b[Uu]s\b").sub, "US")
zip_zag = lambda sequence, tuple_size=2: (
    (
        first,
        *(sequence[tuple_size * idx + offset + 1] for offset in range(tuple_size - 1)),
    )
    for idx, first in enumerate(sequence[::tuple_size])
)


def zone(tz: str):
    try:
        return pytz.timezone(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return None


def get_tz(tz: str):
    # The POSIX Standard dictates that timezones relative to GMT are written
    #   GMT+X going west, and GMT-X going east, contrary to general use.
    #   PyTZ takes input assuming it to follow this standard, but then it
    #   outputs in the form of general use. This is stupid. Therefore,
    #   change input if necessary.
    if tz.lower().startswith("gmt+"):
        tz = tz.replace("+", "-", 1)
    elif tz.lower().startswith("gmt-"):
        tz = tz.replace("-", "+", 1)

    # Try a bunch of different possibilities for what the user might have
    #     meant. Use the first one found, if any. First, check it plain.
    #     Then, check it in title case, all caps and capitalized. Then, look
    #     for the same, but in 'Etc/*'.
    return (
        zone(us_cap(tz))
        or zone(us_cap(tz.upper()))
        or zone(us_cap(tz.title()))
        or zone(us_cap(tz.capitalize()))
        or zone("Etc/" + tz)
        or zone("Etc/" + tz.upper())
        or zone("Etc/" + tz.title())
        or zone("Etc/" + tz.capitalize())
    )


class CommandsUtil(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.help_cache = {}

    async def cmd_help(
        self,
        args: List[str],
        src: discord.Message,
        _short: bool = False,
        _s: bool = False,
        _extreme: bool = False,
        **_,
    ):
        """Print information regarding command usage.

        Help text is drawn from the docstring of a command method, which should be formatted into four sections: Summary, Details, Syntax, and Options.
        The __Summary__ section provides cursory information about a command, and is typically all one needs to understand it on a basic level.
        The __Details__ section contains more involved information about how the command works, possibly including technical information.
        The __Syntax__ section describes exactly how the command should be invoked. Angle brackets indicate a parameter to be filled, square brackets indicate an optional segment, and parentheses indicate choices, separated by pipes. If the Syntax section is missing, it indicates that the command takes no arguments.
        The __Options__ section details Options and Flags that may be passed to the command. These may significantly alter the function of a command.

        For advanced/exhaustive help with Arguments and Options, invoke `{p}help --extreme`.

        See also: `{p}commands` and `{p}info`.

        Syntax: `{p}help [OPTIONS] [<str>]`

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        args : List[str]
            List of Positional Arguments supplied after Command.
        src : discord.Message
            The Discord Message that invoked this Command.
        _short, _s : bool
            Exclude the Details segment.
        _extreme : bool
            Forego normal output and give tutorial.

        Returns
        -------
        discord.Embed
            Embed Object to be embedded into a reply Message.
        """
        if _extreme:
            # for line in helptext:
            #     await self.client.send_message(
            #         src.author, src.channel, line.format(p=self.config.prefix)
            #     )
            return ((line.format(p=self.config.prefix), True) for line in helptext)

        if not args:
            # With no specified command, show help for "help".
            args = ["help"]
            # raise CommandExit("`<Default helptext goes here>`\n`#BlameIso`")

        mod, cmd = self.router.find_command(args[0], src)
        if cmd.__doc__:
            if cmd.__name__ in self.help_cache:
                return self.help_cache[cmd.__name__]
            else:
                # Grab the docstring and insert the correct prefix wherever needed
                doc0 = cmd.__doc__.format(p=self.config.prefix)

                # Ensure that there are no triple-newlines. Make them doubles.
                while "\n\n\n" in doc0:
                    doc0 = doc0.replace("\n\n\n", "\n\n")

                # Split the docstring up by double-newlines, into a List of
                #   Lists which are themselves split by single-newlines.
                doc: List[List[str]] = [doc1.split("\n") for doc1 in doc0.split("\n\n")]

                # First paragraph is Summary.
                summary = "\n".join(line.strip() for line in doc[0])
                em = discord.Embed(
                    title=f"`{self.config.prefix}{cmd.__name__[4:]}`",
                    description=summary,
                    colour=Color.info,
                )
                details: List[Tuple[str]] = []
                syntax: str = ""
                opts: str = ""

                # while doc:
                #     paragraph = doc.pop(0)
                for paragraph in doc[1:]:
                    if paragraph[0].lower().strip().startswith("syntax:"):
                        # Paragraph is the Syntax block.
                        paragraph[0] = paragraph[0].strip()[7:]
                        syntax = "\n".join(x.strip() for x in paragraph if x.strip())

                    elif paragraph[0].lower().strip().startswith("options:"):
                        # Paragraph is the manual-style Options block.
                        if opts:
                            continue

                        paragraph[0] = paragraph[0].strip()[8:]
                        opts = "\n".join(x.strip() for x in paragraph if x.strip())

                    elif [l.strip() for l in paragraph[0:2]] == [
                        "Parameters",
                        "----------",
                    ]:
                        # Paragraph is a NumPy Parameters block; Derive Options.
                        if opts:
                            continue

                        opts_list = []
                        for dat, descrip in zip_zag(
                            # l.strip() for l in paragraph[2:] if l.strip()
                            tuple(filter(None, map(str.strip, paragraph[2:])))
                        ):
                            onames, otype = (
                                dat.replace(" ", "").split(":")
                                if ":" in dat
                                else (dat.replace(" ", ""), "")
                            )
                            onames = [
                                "{}{}{}".format(
                                    ("`-" if len(name) == 2 else "`--"),
                                    name[1:].replace("_", "-"),
                                    ("`" if otype == "bool" else f" <{otype}>`"),
                                )
                                for name in onames.split(",")
                                if name.startswith("_") and len(name) > 1
                            ]
                            if onames:
                                opts_list.append(
                                    " :: ".join(
                                        (
                                            "FLAG" if otype == "bool" else "OPT",
                                            ", ".join(onames),
                                            descrip,
                                        )
                                    )
                                )
                        opts = "\n".join(opts_list)

                    elif len(paragraph) < 2 or paragraph[1].strip("- "):
                        # Safe to conclude this is not a NumPy block.
                        details.append(tuple(filter(None, map(str.strip, paragraph))))
                        # details.append([x.strip() for x in paragraph if x.strip()])

                if details and not (_short or _s):
                    em.add_field(
                        name="Details:",
                        value="\n\n".join("\n".join(p) for p in details)[:1024],
                        inline=False,
                    )
                if syntax:
                    em.add_field(name="Syntax:", value=syntax[:1024], inline=False)
                if opts:
                    em.add_field(name="Options:", value=opts[:1024], inline=False)

                em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
                self.help_cache[cmd.__name__] = em
                return em
        else:
            if cmd:
                raise CommandOperationError(
                    f"No help for `{self.config.prefix}{cmd.__name__[4:]}` available."
                )
            else:
                raise CommandInputError("Command not found.")

    async def cmd_info(self, args, src, **_):
        """Print technical information regarding command implementation.

        Return information about a command, including its restriction settings, its parent module, and, if applicable, its typed parameters. Can only be used on commands to which you have access. See also `{p}help` and `{p}commands`.

        Syntax: `{p}info [<command>]`
        """
        if not args:
            em = discord.Embed(
                title="General Information",
                description="This is Petal, the Patch Gaming Discord Bot.\n"
                "For a list of commands, invoke `{0}commands`.\n"
                "For help with a specific command, invoke `{0}help <command>`.".format(
                    self.config.prefix
                ),
                colour=Color.info,
                timestamp=self.client.startup,
            )
            em.add_field(name="Version", value=self.router.version)
            em.add_field(name="Uptime", value=self.router.uptime)
            em.set_author(
                name="Source on GitHub",
                url="https://www.github.com/hdmifish/petal",
                icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
            )
            em.set_footer(text="Startup Time")

            await self.client.embed(src.channel, em)
            return

        mod, cmd = self.router.find_command(args[0], src)
        if cmd:
            if cmd.__doc__:
                # Grab the docstring and insert the correct prefix wherever needed
                doc0 = cmd.__doc__.format(p=self.config.prefix)
                # Split the docstring up by double-newlines
                doc = [doc1.strip() for doc1 in doc0.split("\n\n")]

                summary = doc.pop(0)
            else:
                summary = "Command summary unavailable."

            em = discord.Embed(
                title=f"`{self.config.prefix}{cmd.__name__[4:]}`",
                description=summary or "Command summary unavailable.",
                colour=Color.tech,
            )

            em.add_field(
                name="Restriction:",
                value=f"Role: `{self.config.get(mod.role)}`"
                f"\nOperator Level: `{mod.op if 0 <= mod.op <= 4 else None}`"
                f"\nWhitelist: `{mod.whitelist or None}`",
            )
            em.add_field(name="Auth Module:", value=f"`{mod.__module__}`")

            hints = get_type_hints(cmd)
            if hints:
                params: str = "\n".join(
                    [f"`{k}`: `{v}`" for k, v in hints.items() if k.startswith("_")]
                )
                if params:
                    em.add_field(
                        name="Typed Parameters:",
                        # value=str(hints) + str(cmd.__annotations__)
                        value=params,
                    )

            em.set_author(name="Petal Info", icon_url=self.client.user.avatar_url)
            return em
        else:
            return "Command not found."

    async def cmd_commands(
        self,
        args,
        src,
        _all: bool = False,
        _a: bool = False,
        _custom: bool = False,
        _c: bool = False,
        _custom_only: bool = False,
        _C: bool = False,
        _sort: bool = False,
        _s: bool = False,
        **_,
    ):
        """List, or search, available commands.

        Syntax: `{p}commands [OPTIONS] [<search>]`

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        args : List[str]
            List of Positional Arguments supplied after Command.
        src : discord.Message
            The Discord Message that invoked this Command.
        _all, _a : bool
            List **__all__** built-in commands, even ones you cannot use.
        _custom, _c : bool
            Include custom commands in the list, created via `{p}new`.
        _custom_only, _C : bool
            Include **__only__** custom commands in the list. Overrides `--all`, `-a`.
        _sort, _s : bool
            Alphabetize the command list; Commands will, by default, be ordered by module priority, and then by position in source code.
        """
        # Send through OrderedDict to remove duplicates while maintaining order.
        cmd_list = (
            list(
                OrderedDict.fromkeys(
                    method.__name__[4:]
                    for method in self.router.get_all(src=None if _all or _a else src)
                )
            )
            if not (_custom_only or _C)
            else []
        )

        if _custom or _custom_only or _c or _C:
            line_2 = "" if _custom_only or _C else ", including custom commands"
            cmd_list.extend(sorted(self.config.get("commands")))
        else:
            line_2 = ""

        if not cmd_list:
            return "Sorry, I do not seem to have any commands available."

        if _sort or _s:
            cmd_list.sort()

        if args:
            line_2 = " matching your search" + line_2
            cmd_list = [
                cmd
                for cmd in cmd_list
                if any(
                    cmd.lower() in term.lower() or term.lower() in cmd.lower()
                    for term in args
                )
            ]
            if not cmd_list:
                return "Sorry, I could not find any commands that match your search."

        cl2 = []
        for cmd in cmd_list:
            if _all or _a:
                mod, func = self.router.find_command(kword=cmd, src=None)
            else:
                # Unless --all or -a, remove any restricted commands.
                try:
                    mod, func = self.router.find_command(kword=cmd, src=src)
                except CommandAuthError:
                    continue

            if mod:
                cl2.append(
                    f"{self.config.prefix}{cmd}"
                    f" :: {mod.__module__.split('.')[-1].replace('_', ' ')}"
                    + ("  *[!]*" if not func.__doc__ else "")
                )

        if not cl2:
            raise CommandOperationError(
                "Sorry, no commands matched your search."
                if args
                else "Sorry, no valid commands found."
            )
        elif _custom_only or _C:
            line_1 = "List of custom commands"
        elif _all or _a:
            line_1 = "List of all commands"
        else:
            line_1 = "List of commands you can access"

        return (f"{line_1}{line_2}:```asciidoc\n" + "\n".join(cl2))[:1997] + "```"

    async def cmd_avatar(self, args, src, **_):
        """Given a User ID, post their Avatar."""
        if not args:
            user = src.author
        else:
            uid = args[0].strip(punctuation)
            if not uid.isdigit():
                raise CommandInputError("User IDs are Integers.")
            uid = int(uid)
            user = self.client.get_user(uid)

        if not user:
            raise CommandOperationError("Cannot find user.")

        em = discord.Embed(
            colour=Color.info,
            description=f"`{fmt.userline(user)}` / {user.mention}",
            title=f"Avatar of Member: {user.display_name}",
        ).set_image(url=cdn.get_avatar(user))

        return em

    async def cmd_ping(self, src, **_):
        """Show the round trip time from this bot to Discord and back.

        Additionally, this command will Tag the User who invokes it. This can be
            used for testing notifications.
        """
        msg: discord.Message = await src.channel.send(
            fmt.italic(f"hugs {src.author.mention}")
        )
        delta = int((dt.now() - msg.created_at).microseconds / 1000)
        self.config.stats["pingScore"] += delta
        self.config.stats["pingCount"] += 1

        self.config.save(vb=0)
        truedelta = int(
            self.config.stats["pingScore"] / (self.config.stats["pingCount"] or 1)
        )

        yield (
            f"Current Ping: {delta}ms",
            f"Average Ping: {truedelta}ms of {self.config.stats['pingCount']} pings",
        )

    async def cmd_time(self, args, **_):
        """Show the current time and date in a specific time zone or location.

        This command will accept either a region/location pair, such as `US/Pacific`, or a time zone code, like `UTC` or `CET` or even ones such as `GMT-5`. Great efforts are taken to hopefully ensure that capitalization is not a concern. With no given input, default output is in UTC.
        The time zones are defined by way of the PyTZ library, and can be found here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

        Syntax:
        `{p}time` - Show date/time in UTC.
        `{p}time <tz code>` - Show d/t in the specified time zone.
        `{p}time <region>/<location>` - Show d/t somewhere specific, such as `Europe/Rome`.
        `{p}time <location>` - Show d/t somewhere specific that lacks a "region", such as `GB`.
        """
        tzstr = args[0] if args else "UTC"
        tzone = get_tz(tzstr)

        if tzone:
            return f"Current time is {dt.now(tzone).strftime(tstring)}."
        else:
            raise CommandInputError(f"Could not find the `{tzstr}` timezone.")

    async def cmd_utc(self, **_):
        """Print the current time and date in UTC. This is equivalent to `{p}time "UTC"`."""
        return await self.cmd_time(args=["UTC"])

    async def cmd_when(self, args, _from: str = None, _to: str = None, **_):
        """Take a given time and convert it to another time zone (Default UTC).

        Syntax: `{p}when [OPTIONS] <Description of some time>` - Parse the description of a time and print the same time in another time zone.

        Parameters
        ----------
        _ : dict
            Dict of additional Keyword Args.
        args : List[str]
            List of Positional Arguments supplied after Command.
        _from : str
            Provide the original time zone of the time description you want to convert. Defaults to UTC.
        _to : str
            Provide the target time zone to which you want to convert the given time description. Defaults to UTC.
        """
        # Arguments make up a human-written time description.
        source_time: str = " ".join(args) if args else "now"

        if _from:
            # Determine the time zone of the time provided by the user.
            tz_from = get_tz(_from)
            if not tz_from:
                raise CommandInputError(f"Cannot find the `{_from}` timezone.")
        else:
            tz_from = pytz.UTC

        if _to:
            # Determine the time zone the user wants to receive.
            tz_to = get_tz(_to)
            if not tz_to:
                raise CommandInputError(f"Cannot find the `{_to}` timezone.")
        else:
            tz_to = pytz.UTC

        when: dt = dateparser.parse(
            source_time,
            settings={"TIMEZONE": str(tz_from), "RETURN_AS_TIMEZONE_AWARE": True},
        )

        if not when:
            # Cannot parse the input.
            raise CommandArgsError(
                f"Sorry, I can't understand when you mean by {source_time!r}."
            )

        yield (
            "Current time:"
            if source_time.lower() == "now"
            else f"Time described by `{source_time!r}`:"
        )
        yield when.strftime(tstring)

        if tz_to != tz_from:
            yield when.astimezone(tz_to).strftime(tstring)

    async def cmd_stats(self, **_):
        """Display detailed technical statistics."""
        truedelta = int(self.config.stats["pingScore"] / self.config.stats["pingCount"])

        em = discord.Embed(title="Stats", colour=Color.info)
        em.add_field(name="Version", value=self.router.version, inline=False)
        em.add_field(name="Uptime", value=self.router.uptime, inline=False)
        # em.add_field(name="Void Count", value=str(self.db.void.count()), inline=False)
        em.add_field(name="Servers", value=str(len(self.client.guilds)), inline=False)
        em.add_field(
            name="Total Number of Commands run",
            value=str(self.config.get("stats")["comCount"]),
            inline=False,
        )
        em.add_field(name="Average Ping", value=str(truedelta), inline=False)
        mc = sum(1 for _ in self.client.get_all_members())
        em.add_field(name="Total Members", value=str(mc), inline=False)
        role = discord.utils.get(
            self.client.get_guild(self.config.get("mainServer")).roles,
            name=self.config.get("mainRole"),
        )
        if role is None:
            c = 0
        else:
            c = sum(1 for m in self.client.get_all_members() if role in m.roles)

        em.add_field(name="Total Validated Members", value=str(c), inline=False)
        return em

    async def cmd_animalcrossing(self, src, **_):
        """Toggle AnimalCrossing mode for your user.

        This is more or less an easter egg.
        All responses will end in an animal crossing styled ending.

        Syntax: `{p}animalcrossing`
        """
        if not self.db.useDB:
            raise CommandOperationError("Sorry, database is not enabled.")

        if self.db.get_attribute(src.author, "ac") is None:
            self.db.update_member(src.author, {"ac": True}, 2)
            return "Enabled Animal Crossing Endings."
        elif self.db.get_attribute(src.author, "ac"):
            self.db.update_member(src.author, {"ac": False}, 2)
            return "Disabled Animal Crossing Endings."
        else:
            self.db.update_member(src.author, {"ac": True}, 2)
            return "Re-Enabled Animal Crossing Endings."

    async def cmd_argtest(
        self,
        args,
        msg,
        src,
        _boolean: bool = False,
        _b: bool = False,
        _string: str = None,
        _s: str = None,
        _digit: int = None,
        _d: int = None,
        _number: float = None,
        _n: float = None,
        _dashed_long_opt: str = None,
        **opts,
    ):
        """Display details on how the command was parsed.

        Used for testing, or personal experimentation to help you to understand Arguments, Options and Flags.

        When a command is run, all text typed after the command is sent to the command as a series of words.

        An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.

        Syntax: `{p}argtest [OPTIONS] [<arguments>...]`

        Parameters
        ----------
        opts : dict
            Dict of additional Keyword Args.
        args : List[str]
            List of Positional Arguments supplied after Command.
        msg : str
            The TEXT of the Message that invoked this Command, minux the Prefix.
        src : discord.Message
            The Discord Message that invoked this Command.
        _boolean, _b : bool
            Set the Boolean Flag to display `True`.
        _string, _s, _dashed_long_opt : str
            Define this Option to be displayed.
        _digit, _d : int
            Define this Option to be displayed.
        _number, _n : float
            Define this Option to be displayed.
        """
        print(args, opts, src)
        yield "ARGS:", args, "OPTS:"

        yield (
            f"{opt} = `{repr(val)}` ({type(val).__name__})"
            for opt, val in (
                ("`--boolean`, `-b`", _boolean or _b),
                ("`--string`, `-s`", _string or _s),
                ("`--dashed-long-opt`", _dashed_long_opt),
                ("`--digit`, `-d`", _digit or _d),
                ("`--number`, `-n`", _number or _n),
            )
            if val is not None
        )

        yield f"MSG: {msg}"

    async def cmd_history(self, src, _n: int = 10, **_):
        """Print your Message History.

        Useful for Debugging and not much else. Can tell you whether Petal is
            able to see a certain Message.
        """
        history = member_message_history(src.author, limit=_n)
        now = dt.utcnow()
        s = 0

        async for m in history:
            if s > 30:
                break
            else:
                s += 1
                yield (
                    f"{m.channel.mention}, `{str(now - m.created_at)[:-7]}` ago:"
                    f"{fmt.mono_block(fmt.escape(m.content))}"
                )

        yield f"Showing last __{s}__ Messages."

    def cmd_bytes(
        self,
        args,
        _encoding: str = "utf-16",
        _binary: bool = False,
        _hex: bool = False,
        **_,
    ):
        """Encode the message provided into a Bytes object. Then, print it.

        Debug utility to sanity check **__exactly__** what is received over Discord.

        Syntax: `{p}bytes <literally anything>...`
        """
        # raw: bytes = src.content[7:].encode(_encoding)
        txt: str = " ".join(args)
        raw: bytes = txt.encode(_encoding)

        __bin: List[str] = [format(b, "0>8b") for b in raw]
        __hex: List[str] = [format(b, "0>2X") for b in raw]

        txt_ = txt + "                "
        em = discord.Embed(
            title="Detailed String Analysis",
            description=fmt.bold(fmt.escape(repr(raw)[2:-1])),
            colour=Color.tech,
        )

        if _binary or not _hex:
            em.add_field(
                name="Binary",
                value="\n".join(
                    fmt.mono(
                        " :: ".join(
                            (
                                # f"{i*4:0>2}-{min((i*4+3,len(__bin)-1)):0>2}",
                                f"{txt_[i * 4 : i * 4 + 4]}",
                                " ".join(c for c in ch if c is not None),
                            )
                        )
                    )
                    for i, ch in enumerate(chunk(__bin, 4))
                ),
                inline=False,
            )

        if _hex:
            em.add_field(
                name="Hexadecimal",
                value="\n".join(
                    fmt.mono(
                        " :: ".join(
                            (
                                f"{i*16:0>2}-{min((i*16+15,len(__hex)-1)):0>2}",
                                # f"'`{txt[i*16:i*16+16]}`'",
                                " ".join(c for c in ch if c is not None),
                            )
                        )
                    )
                    for i, ch in enumerate(chunk(__hex, 16))
                ),
                inline=False,
            )

        return em.add_field(
            name="Raw Bits",
            value=fmt.bold(fmt.mono(bytes_to_braille(raw))),
            inline=False,
        )


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsUtil
