"""Commands module for BOT-RELATED UTILITIES.
Access: Public"""

from datetime import datetime as dt

import discord

from petal.commands import core


helptext = [
    """An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.""",
    """While spaces separate Arguments, sometimes an Argument is desired to be multiple words. In these cases, one can simply enclose the argument in quotes; For example:```{p}command "asdf qwert" zxcv```This would pass only *two* arguments to the command: `"asdf qwert"` and `"zxcv"`.""",
    """An __Option__ is an additional Argument passed to a command, prefixed by either `-` or `--`, which is optional. An Option prefixed by `-` is a "Short" Option, while an Option prefixed by `--` is a "Long" Option. For example:```{p}command --opt=asdf```If you were to run this, you would pass the Long Option, `opt`, into the command with the value of `"asdf"`. It is up to the `cmd_command()` method to accept and use this value somehow.""",
    """A __Flag__ is an Option passed without an explicit value, such as in:```{p}command --verbose```In this example, `verbose` is passed into the command with a **boolean** value of `True`, rather than any string value. This is often used by commands that may optionally return more information if requested.""",
    """Short Options may be grouped together as a single prefixed word, or cluster. This can save time when typing a command with a series of Flags, but it is less useful when values need to be passed, because only the final Short Option in a cluster will be assigned the value specified. For example:```{p}command -abc=23 --long1=xyz --long2```In this command, while `c` is passed with a value of `"23"`, `a` and `b` are simply passed with values of `True`. This is the same difference by which the Long Option `long1` is passed with the value `"xyz"` while `long2` is passed with the value `True`.""",
]


class CommandsUtil(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def authenticate(self, *_):
        return True

    async def cmd_help(self, args, src, **_):
        """Print information regarding command usage.

        Help text is drawn from the docstring of a command method, which should be formatted into four sections -- Summary, Details, Syntax, and Options -- which are separated by double-newlines.
        The __Summary__ section provides cursory information about a command, and is typically all one needs to understand it.
        The __Details__ section contains more involved information about how the command works, possibly including technical information.
        The __Syntax__ section describes exactly how the command should be invoked. Angle brackets indicate a parameter to be filled, square brackets indicate an optional segment, and parentheses indicate choices, separated by pipes.
        The __Options__ section details Options and Flags that may be passed to the command. These may significantly alter the operation of a command.

        For exhaustive help with Arguments and Options, invoke `{p}help extreme`.

        Syntax: `{p}help [(<command>|extreme)]`
        """
        if not args:
            # TODO: Iso, put your default helptext here; Didnt copy it over in case you wanted it changed
            return "`<Default helptext goes here>`\n`#BlameIso`"

        if args[0].lower() == "extreme":
            for line in helptext:
                await self.client.send_message(
                    src.author, src.channel, line.format(p=self.config.prefix)
                )
            return

        mod, cmd, denied = self.router.find_command(args[0], src)
        if denied:
            return denied
        elif cmd.__doc__:
            # Grab the docstring and insert the correct prefix wherever needed
            doc0 = cmd.__doc__.format(p=self.config.prefix)
            # Split the docstring up by double-newlines
            doc = [doc1.strip() for doc1 in doc0.split("\n\n")]

            summary = doc.pop(0)
            em = discord.Embed(
                title=self.config.prefix + cmd.__name__[4:],
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
            if details:
                em.add_field(name="Details", value=details.strip())
            if syntax:
                em.add_field(name="Syntax", value=syntax)
            if opts:
                em.add_field(name="Options", value=opts)

            em.set_author(name="Petal Help", icon_url=self.client.user.avatar_url)
            em.set_thumbnail(url=self.client.user.avatar_url)
            await self.client.embed(src.channel, em)
        else:
            if cmd:
                return "No help for `{}` available.".format(
                    self.config.prefix + cmd.__name__[4:]
                )
            else:
                return "Command not found."

    async def cmd_commands(self, src, all=False, a=False, custom=False, c=False, **_):
        """List all commands.

        Syntax: `{p}commands [OPTIONS]`

        Options: `--all`, `-a` :: List **__all__** built-in commands, even ones you cannot use.
        `--custom`, `-c` :: Include custom commands in the list, created via `{p}new`.
        """
        formattedList = ""
        cmd_list = list(set([method.__name__[4:] for method in self.router.get_all()]))
        if True in (custom, c):
            line_2 = ", including custom commands"
            cust_list = self.config.get("commands") or {}
            cmd_list += [f"{k} -> '{cust_list[k]['com']}'" for k in cust_list]
        else:
            line_2 = ""
        cmd_list.sort()

        if True not in (all, a):
            # Unless --all or -a, remove any restricted commands.
            for cmd in cmd_list.copy():
                mod, func, denied = self.router.find_command(
                    kword=cmd.split()[0], src=src
                )
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

    async def cmd_statsfornerds(self, src, **_):
        """Display more detailed statistics (for nerds)."""
        truedelta = int(self.config.stats["pingScore"] / self.config.stats["pingCount"])

        em = discord.Embed(title="Stats", description="*for nerds*", colour=0x0ACDFF)
        em.add_field(name="Version", value=self.router.version)
        em.add_field(name="Uptime", value=self.router.uptime)
        # em.add_field(name="Void Count", value=str(self.db.void.count()))
        em.add_field(name="Servers", value=str(len(self.client.servers)))
        em.add_field(
            name="Total Number of Commands run",
            value=str(self.config.get("stats")["comCount"]),
        )
        em.add_field(name="Average Ping", value=str(truedelta))
        mc = sum(1 for _ in self.client.get_all_members())
        em.add_field(name="Total Members", value=str(mc))
        role = discord.utils.get(
            self.client.get_server(self.config.get("mainServer")).roles,
            name=self.config.get("mainRole"),
        )
        c = 0
        if role is not None:
            for m in self.client.get_all_members():

                if role in m.roles:
                    c += 1
            em.add_field(name="Total Validated Members", value=str(c))

        await self.client.embed(src.channel, em)

    async def cmd_argtest(self, args, src, **opts):
        """Display details on how the command was parsed.

        Used for testing, or personal experimentation to help you to understand Arguments, Options and Flags.

        When a command is run, all text typed after the command is sent to the command as a series of words.

        An __Argument__ is simply any word given to a command. Arguments are separated from each other by spaces.```{p}command asdf qwert zxcv```Running this command would pass three Arguments to the command: `"asdf"`, `"qwert"`, and `"zxcv"`. It is up to the command function to decide what Arguments it wants, and how they are used.

        Syntax: `{p}argtest [-<abcd...>=<value>] [--<flag>=<value>]`
        """
        print(args, opts, src)
        out = ["ARGS:", *args, "OPTS:"]
        for opt, val in opts.items():
            out.append(str(opt) + "==" + str(val))
        return "\n".join(out)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsUtil
