"""Commands module for BOT-RELATED UTILITIES.
Access: Public"""

from datetime import datetime as dt
from typing import get_type_hints

import discord
import pytz

from petal.commands import core

# Reference: strftime.org
tstring = "Current time is **`%H:%M`** %Z on %A, %B %d, %Y."
helptext = [
    """An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.""",
    """While spaces separate Arguments, sometimes an Argument is desired to be multiple words. In these cases, one can simply enclose the argument in quotes; For example:```{p}command "asdf qwert" zxcv```This would pass only *two* arguments to the command: `"asdf qwert"` and `"zxcv"`.""",
    """An __Option__ is an additional Argument passed to a command, prefixed by either `-` or `--`, which is optional. An Option prefixed by `-` is a "Short" Option, while an Option prefixed by `--` is a "Long" Option. A Long Option may also have its value specified with a `=` instead of a space and a string, and additionally, only needs enough of the word to be uniquely identified. For example:```{p}command --option asdf\n{p}command --option=asdf\n{p}command --opt asdf```If you were to run one of these, you would pass the Long Option, `option`, into the command with the value of `"asdf"`. It is up to the `cmd_command()` method to accept and use this value somehow.""",
    """A __Flag__ is an Option passed without an explicit value, such as in:```{p}command --verbose```In this example, `verbose` is passed into the command with a **boolean** value of `True`, rather than any string value. This is often used by commands that may optionally return more or less information if requested.""",
    """Short Options may be grouped together as a single prefixed word, or cluster. This can save time when typing a command with a series of Flags, but it is less useful when values need to be passed, because only the final Short Option in a cluster will be assigned the value specified. For example:```{p}command -abc 23 --long1 xyz --long2```In this command, while `c` is passed with a value of `"23"`, `a` and `b` are simply passed with values of `True`. This is the same difference by which the Long Option `long1` is passed with the value `"xyz"` while `long2` is passed with the value `True`.""",
]


def zone(tz: str):
    try:
        return pytz.timezone(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return None


class CommandsUtil(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    async def cmd_help(
        self,
        args,
        src,
        _short: bool = False,
        _s: bool = False,
        _extreme: bool = False,
        **_
    ):
        """Print information regarding command usage.

        Help text is drawn from the docstring of a command method, which should be formatted into four sections -- Summary, Details, Syntax, and Options -- which are separated by double-newlines.
        The __Summary__ section provides cursory information about a command, and is typically all one needs to understand it.
        The __Details__ section contains more involved information about how the command works, possibly including technical information.
        The __Syntax__ section describes exactly how the command should be invoked. Angle brackets indicate a parameter to be filled, square brackets indicate an optional segment, and parentheses indicate choices, separated by pipes.
        The __Options__ section details Options and Flags that may be passed to the command. These may significantly alter the operation of a command.

        For exhaustive help with Arguments and Options, invoke `{p}help extreme`. See also `{p}commands` and `{p}info`.

        Syntax: `{p}help [OPTIONS] [<str>]`

        Options:
        `--short`, `-s` :: Exclude the "details" section of printed help.
        `--extreme` :: Return **extremely verbose** general help on Arguments, Options, and Flags.
        """
        if _extreme:
            for line in helptext:
                await self.client.send_message(
                    src.author, src.channel, line.format(p=self.config.prefix)
                )
            return

        if not args:
            # TODO: Iso, put your default helptext here; Didnt copy it over in case you wanted it changed
            return "`<Default helptext goes here>`\n`#BlameIso`"

        mod, cmd, denied = self.router.find_command(args[0], src)
        if denied:
            return "Cannot show help: " + denied
        elif cmd.__doc__:
            # Grab the docstring and insert the correct prefix wherever needed
            doc0 = cmd.__doc__.format(p=self.config.prefix)
            # Split the docstring up by double-newlines
            doc = [doc1.strip() for doc1 in doc0.split("\n\n")]

            summary = doc.pop(0)
            em = discord.Embed(
                title="`" + self.config.prefix + cmd.__name__[4:] + "`",
                description=summary,
                colour=0x0ACDFF,
            )

            details = ""
            syntax = ""
            opts = ""
            while doc:
                line = doc.pop(0)
                if line.lower().startswith("syntax"):
                    syntax = line.split(" ", 1)[1]
                elif line.lower().startswith("options"):
                    opts = line.split(" ", 1)[1]
                else:
                    details += line + "\n"
            if details and True not in (_short, _s):
                em.add_field(name="Details:", value=details.strip())
            if syntax:
                em.add_field(name="Syntax:", value=syntax)
            if opts:
                em.add_field(name="Options:", value=opts)

            em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
            # em.set_thumbnail(url=self.client.user.avatar_url)
            await self.client.embed(src.channel, em)
        else:
            if cmd:
                return "No help for `{}` available.".format(
                    self.config.prefix + cmd.__name__[4:]
                )
            else:
                return "Command not found."

    async def cmd_info(self, args, src, **_):
        """Print technical information regarding command implementation.

        Return information about a command, including its restriction settings, its parent module, and, if applicable, its typed parameters. Can only be used on commands to which you have access. See also `{p}help` and `{p}commands`.

        Syntax: `{p}info [<command>]`
        """
        if not args:
            return "`<Default infotext goes here>`\n`#BlameDav`"

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
                    self.config.get(mod.role), mod.op, mod.whitelist
                ),
            )
            em.add_field(name="Auth Module:", value="`{}`".format(mod.__module__))

            hints = get_type_hints(cmd)
            if hints:
                em.add_field(
                    name="Typed Parameters:",
                    value="\n".join(
                        ["`{}`: `{}`".format(k, v.__name__) for k, v in hints.items()]
                    ),
                )

            em.set_author(name="Petal Info", icon_url=self.client.user.avatar_url)
            await self.client.embed(src.channel, em)
        else:
            return "Command not found."

    async def cmd_commands(
        self,
        src,
        _all: bool = False,
        _a: bool = False,
        _custom: bool = False,
        _c: bool = False,
        **_
    ):
        """List all commands.

        Syntax: `{p}commands [OPTIONS]`

        Options:
        `--all`, `-a` :: List **__all__** built-in commands, even ones you cannot use.
        `--custom`, `-c` :: Include custom commands in the list, created via `{p}new`.
        """
        formattedList = ""
        cmd_list = list(set([method.__name__[4:] for method in self.router.get_all()]))
        if True in (_custom, _c):
            line_2 = ", including custom commands"
            cmd_list += list(self.config.get("commands")) or []
        else:
            line_2 = ""
        cmd_list.sort()

        if True not in (_all, _a):
            # Unless --all or -a, remove any restricted commands.
            for cmd in cmd_list.copy():
                mod, func, denied = self.router.find_command(kword=cmd, src=src)
                if denied is not False:
                    cmd_list.remove(cmd)
            line_1 = "List of commands you can access"
        else:
            line_1 = "List of all commands"

        for cmd in cmd_list:
            formattedList += "\n" + self.config.prefix + cmd

        return line_1 + line_2 + ": ```" + formattedList + "```"

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
            or zone("/".join([term.capitalize() for term in tz.split("/")]))
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

        em = discord.Embed(title="Stats", description="*for nerds*", colour=0x0ACDFF)
        em.add_field(name="Version", value=self.router.version, inline=False)
        em.add_field(name="Uptime", value=self.router.uptime, inline=False)
        # em.add_field(name="Void Count", value=str(self.db.void.count()), inline=False)
        em.add_field(name="Servers", value=str(len(self.client.servers)), inline=False)
        em.add_field(
            name="Total Number of Commands run",
            value=str(self.config.get("stats")["comCount"]),
            inline=False,
        )
        em.add_field(name="Average Ping", value=str(truedelta), inline=False)
        mc = sum(1 for _ in self.client.get_all_members())
        em.add_field(name="Total Members", value=str(mc), inline=False)
        role = discord.utils.get(
            self.client.get_server(self.config.get("mainServer")).roles,
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
            return "Sorry, datbase is not enabled..."

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
        _b: bool = False,
        _s: str = None,
        _d: int = None,
        _n: float = None,
        _boolean: bool = False,
        _string: str = None,
        _digit: int = None,
        _number: float = None,
        _dashed_long_opt: str = None,
        **opts
    ):
        """Display details on how the command was parsed.

        Used for testing, or personal experimentation to help you to understand Arguments, Options and Flags.

        When a command is run, all text typed after the command is sent to the command as a series of words.

        An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.

        Syntax: `{p}argtest [OPTIONS] [<arguments>...]`

        Options:
        `--boolean`, `-b` :: Set the Boolean Flag to display `True`.
        `--string=<str>`, `-s <str>` :: Define this Option to be displayed.
        `--dashed-long-opt=<str>`
        `--digit=<int>`, `-d <int>` :: Define this Option to be displayed.
        `--number=<float>`, `-n <float>` :: Define this Option to be displayed.
        """
        print(args, opts, src)
        out = ["ARGS:", *args, "OPTS:"]
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
                out.append("{} = `{}` ({})".format(opt, repr(val), type(val).__name__))
        out.append("MSG: " + msg)
        return "\n".join(out)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsUtil
