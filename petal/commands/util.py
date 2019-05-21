"""Commands module for BOT-RELATED UTILITIES.
Access: Public"""

from collections import OrderedDict
from datetime import datetime as dt
from typing import get_type_hints, List

import discord
import pytz

from petal.commands import core
from petal.exceptions import CommandAuthError, CommandInputError, CommandOperationError


# Reference: strftime.org
tstring = "Current time is **`%H:%M`** %Z on %A, %B %d, %Y."
helptext = [
    """An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.""",
    """While spaces separate Arguments, sometimes an Argument is desired to be multiple words. In these cases, one can simply enclose the argument in quotes; For example:```{p}command "asdf qwert" zxcv```This would pass only *two* arguments to the command: `"asdf qwert"` and `"zxcv"`.""",
    """An __Option__ is an additional Argument passed to a command, prefixed by either `-` or `--`, which is optional. An Option prefixed by `-` is a "Short" Option, while an Option prefixed by `--` is a "Long" Option. A Long Option may also have its value specified with a `=` instead of a space and a string, and additionally, only needs enough of the word to be uniquely identified. For example:```{p}command --option asdf\n{p}command --option=asdf\n{p}command --opt asdf```If you were to run one of these, you would pass the Long Option, `option`, into the command with the value of `"asdf"`. It is up to the `cmd_command()` method to accept and use this value somehow.""",
    """A __Flag__ is an Option passed without an explicit value, such as in:```{p}command --verbose```In this example, `verbose` is passed into the command with a **boolean** value of `True`, rather than any string value. This is often used by commands that may optionally return more or less information if requested.""",
    """Short Options may be grouped together as a single prefixed word, or cluster. This can save time when typing a command with a series of Flags, but it is less useful when values need to be passed, because only the final Short Option in a cluster will be assigned the value specified. For example:```{p}command -abc 23 --long1 xyz --long2```In this command, while `c` is passed with a value of `"23"`, `a` and `b` are simply passed with values of `True`. This is the same difference by which the Long Option `long1` is passed with the value `"xyz"` while `long2` is passed with the value `True`.""",
]


zip_zag = lambda sequence, tuple_size=2: [
    (
        first,
        *[sequence[tuple_size * idx + offset + 1] for offset in range(tuple_size - 1)],
    )
    for idx, first in enumerate(sequence[::tuple_size])
]


def zone(tz: str):
    try:
        return pytz.timezone(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return None


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
        **_
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
            for line in helptext:
                await self.client.send_message(
                    src.author, src.channel, line.format(p=self.config.prefix)
                )
            return

        if not args:
            # With no specified command, show help for "help".
            args = ["help"]
            # raise CommandExit("`<Default helptext goes here>`\n`#BlameIso`")

        mod, cmd, denied = self.router.find_command(args[0], src)
        if denied:
            raise CommandOperationError("Cannot show help: " + denied)
        elif cmd.__doc__:
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
                summary = "\n".join([line.strip() for line in doc.pop(0)])
                em = discord.Embed(
                    title="`" + self.config.prefix + cmd.__name__[4:] + "`",
                    description=summary,
                    colour=0x0ACDFF,
                )
                details: List[List[str]] = []
                syntax: str = ""
                opts: str = ""

                # while doc:
                #     paragraph = doc.pop(0)
                for paragraph in doc:
                    if paragraph[0].lower().strip().startswith("syntax:"):
                        # Paragraph is the Syntax block.
                        paragraph[0] = paragraph[0].strip()[7:]
                        syntax = "\n".join([x.strip() for x in paragraph if x.strip()])

                    elif paragraph[0].lower().strip().startswith("options:"):
                        # Paragraph is the manual-style Options block.
                        if opts:
                            continue

                        paragraph[0] = paragraph[0].strip()[8:]
                        opts = "\n".join([x.strip() for x in paragraph if x.strip()])

                    elif [l.strip() for l in paragraph[0:2]] == [
                        "Parameters",
                        "----------",
                    ]:
                        # Paragraph is a NumPy Parameters block; Derive Options.
                        if opts:
                            continue

                        opts_list = []
                        for dat, descrip in zip_zag(
                            [l.strip() for l in paragraph[2:] if l.strip()]
                        ):
                            onames, otype = (
                                dat.replace(" ", "").split(":")
                                if ":" in dat
                                else (dat.replace(" ", ""), "")
                            )
                            onames = [
                                ("`-" if len(name) == 2 else "`--")
                                + name[1:].replace("_", "-")
                                + ("`" if otype == "bool" else " <{}>`".format(otype))
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
                        details.append([x.strip() for x in paragraph if x.strip()])

                if details and not (_short or _s):
                    em.add_field(
                        name="Details:",
                        value="\n\n".join(["\n".join(p) for p in details])[:1024],
                    )
                if syntax:
                    em.add_field(name="Syntax:", value=syntax[:1024])
                if opts:
                    em.add_field(name="Options:", value=opts[:1024])

                em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
                self.help_cache[cmd.__name__] = em
                return em
        else:
            if cmd:
                raise CommandOperationError(
                    "No help for `{}` available.".format(
                        self.config.prefix + cmd.__name__[4:]
                    )
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
                colour=0x0ACDFF,
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

        mod, cmd, denied = self.router.find_command(args[0], src)
        if denied:
            return "Cannot show info: " + denied
        elif cmd:
            if cmd.__doc__:
                # Grab the docstring and insert the correct prefix wherever needed
                doc0 = cmd.__doc__.format(p=self.config.prefix)
                # Split the docstring up by double-newlines
                doc = [doc1.strip() for doc1 in doc0.split("\n\n")]

                summary = doc.pop(0)
            else:
                summary = "Command summary unavailable."

            em = discord.Embed(
                title="`" + self.config.prefix + cmd.__name__[4:] + "`",
                description=summary,
                colour=0xFFCD0A,
            )

            em.add_field(
                name="Restriction:",
                value="Role: `{}`\nOperator Level: `{}`\nWhitelist: `{}`".format(
                    self.config.get(mod.role),
                    mod.op if 0 <= mod.op <= 4 else None,
                    mod.whitelist,
                ),
            )
            em.add_field(name="Auth Module:", value="`{}`".format(mod.__module__))

            hints = get_type_hints(cmd)
            if hints:
                em.add_field(
                    name="Typed Parameters:",
                    # value=str(hints) + str(cmd.__annotations__)
                    value="\n".join(
                        [
                            "`{}`: `{}`".format(k, v)
                            for k, v in hints.items()
                            if k.startswith("_")
                        ]
                    ),
                )

            em.set_author(name="Petal Info", icon_url=self.client.user.avatar_url)
            await self.client.embed(src.channel, em)
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
        **_
    ):
        """List all commands.

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
                    [
                        method.__name__[4:]
                        for method in self.router.get_all(
                            src=None if _all or _a else src
                        )
                    ]
                )
            )
            if not (_custom_only or _C)
            else []
        )

        if _custom or _custom_only or _c or _C:
            line_2 = "" if _custom_only or _C else ", including custom commands"
            cmd_list += list(sorted(self.config.get("commands"))) or []
        else:
            line_2 = ""

        if _sort or _s:
            cmd_list.sort()

        if args:
            line_2 = " matching your search" + line_2
            cmd_list = [
                cmd
                for cmd in cmd_list
                if any(
                    [
                        cmd.lower() in term.lower() or term.lower() in cmd.lower()
                        for term in args
                    ]
                )
            ]

        cl2 = []
        for cmd in cmd_list:
            if _all or _a:
                mod, func, denied = self.router.find_command(kword=cmd, src=None)
            else:
                # Unless --all or -a, remove any restricted commands.
                try:
                    mod, func, denied = self.router.find_command(kword=cmd, src=src)
                except CommandAuthError:
                    continue
            cl2.append(
                "{} - {}".format(
                    self.config.prefix + cmd, mod.__module__.split(".")[-1]
                )
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

        return (line_1 + line_2 + ":```" + "\n".join(cl2))[:1997] + "```"

    async def cmd_avatar(self, args, src, **_):
        """Given a User ID, post their Avatar."""
        if not args:
            user = src.author
        else:
            uid = args[0]
            if not uid.isdigit():
                return "User IDs are Integers."
            uid = int(uid)
            user = self.client.get_user(uid)
        if not user:
            return "Cannot find user."

        em = discord.Embed(
            colour=0x0ACDFF,
            description="`{}#{}` / `{}` / {}".format(
                user.name, user.discriminator, user.id, user.mention
            ),
            title="Avatar for {}".format(user.name),
        ).set_image(url=user.avatar_url)

        await src.channel.send(embed=em)

    async def cmd_ping(self, src, **_):
        """Show the round trip time from this bot to Discord (not you) and back."""
        msg = await self.client.send_message(src.author, src.channel, "*hugs*")
        delta = int((dt.now() - msg.timestamp).microseconds / 1000)
        self.config.stats["pingScore"] += delta
        self.config.stats["pingCount"] += 1

        self.config.save(vb=0)
        truedelta = int(self.config.stats["pingScore"] / self.config.stats["pingCount"])

        return "Current Ping: {}ms\nPing till now: {}ms of {} pings".format(
            str(delta), str(truedelta), str(self.config.stats["pingCount"])
        )

    async def cmd_time(self, args, **_):
        """Show the current time and date in a specific time zone or location.

        This command will accept either a region/location pair, such as `US/Pacific`, or a time zone code, like `UTC` or `CET` or even ones such as `GMT-5`. Great efforts are taken to hopefully ensure that capitalization is not a concern. With no given input, default output is in UTC.
        The time zones are defined by way of the PyTZ library, and can be found here: http://pytz.sourceforge.net/

        Syntax:
        `{p}time` - Show date/time in UTC.
        `{p}time <tz code>` - Show d/t in the specified time zone.
        `{p}time <region>/<location>` - Show d/t somewhere specific, such as `Europe/Rome`.
        `{p}time <location>` - Show d/t somewhere specific that lacks a "region", such as `GB`.
        """
        tz = args[0] if args else "UTC"
        # Try a bunch of different possibilities for what the user might have
        #     meant. Use the first one found, if any. First, check it plain.
        #     Then, check it in all caps and CamelCase. Then, look for the same,
        #     but in 'Etc/*'. Finally, split it and capitalize each part before
        #     finally giving up.
        tzone = (
            zone(tz)
            or zone(tz.upper())
            or zone(tz.capitalize())
            or zone("Etc/" + tz)
            or zone("Etc/" + tz.upper())
            or zone("Etc/" + tz.capitalize())
            or zone(
                "/".join(
                    [
                        "US" if word.lower() == "us" else word
                        for word in [term.capitalize() for term in tz.split("/")]
                    ]
                )
            )
            or zone(
                "/".join(
                    [
                        "US" if word.lower() == "us" else word
                        for word in [
                            "_".join([sub.capitalize() for sub in term.split(" ")])
                            for term in tz.split("/")
                        ]
                    ]
                )
            )
            or zone(
                "/".join(
                    [
                        "US" if word.lower() == "us" else word
                        for word in [
                            "_".join([sub.capitalize() for sub in term.split("_")])
                            for term in tz.split("/")
                        ]
                    ]
                )
            )
        )
        if tzone:
            return dt.now(tzone).strftime(tstring)
        else:
            return "Could not find the `{}` timezone.".format(tz)

    async def cmd_utc(self, **_):
        """Print the current time and date in UTC. This is equivalent to `{p}time "UTC"`."""
        return await self.cmd_time(["UTC"])

    async def cmd_stats(self, src, **_):
        """Display detailed technical statistics."""
        truedelta = int(self.config.stats["pingScore"] / self.config.stats["pingCount"])

        em = discord.Embed(title="Stats", colour=0x0ACDFF)
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
        c = 0
        if role is not None:
            for m in self.client.get_all_members():

                if role in m.roles:
                    c += 1
            em.add_field(name="Total Validated Members", value=str(c), inline=False)

        await self.client.embed(src.channel, em)

    async def cmd_animalcrossing(self, src, **_):
        """Toggle AnimalCrossing mode for your user.

        This is more or less an easter egg.
        All responses will end in an animal crossing styled ending.

        Syntax: `{p}animalcrossing`
        """
        if not self.db.useDB:
            return "Sorry, database is not enabled..."

        if self.db.get_attribute(src.author, "ac") is None:
            self.db.update_member(src.author, {"ac": True}, 2)
            return "Enabled Animal Crossing Endings..."
        elif self.db.get_attribute(src.author, "ac"):
            self.db.update_member(src.author, {"ac": False}, 2)
            return "Disabled Animal Crossing Endings..."
        else:
            self.db.update_member(src.author, {"ac": True}, 2)
            return "Re-Enabled Animal Crossing Endings..."

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
        **opts
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
        # out = ["ARGS:", *args, "OPTS:"]
        for x in ["ARGS:", *args, "OPTS:"]:
            yield x
        for opt, val in [
            ("`--boolean`, `-b`", _boolean or _b),
            ("`--string`, `-s`", _string or _s),
            ("`--dashed-long-opt`", _dashed_long_opt),
            ("`--digit`, `-d`", _digit or _d),
            ("`--number`, `-n`", _number or _n),
            # ("--boolean", _boolean),
            # ("--string", _string),
            # ("--digit", _digit),
            # ("--number", _number),
            # ("-b", _b),
            # ("-s", _s),
            # ("-d", _d),
            # ("-n", _n),
        ]:
            if val is not None:
                # out.append("{} = `{}` ({})".format(opt, repr(val), type(val).__name__))
                yield "{} = `{}` ({})".format(opt, repr(val), type(val).__name__)
        yield "MSG: " + msg
        # out.append("MSG: " + msg)
        # return "\n".join(out)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsUtil
