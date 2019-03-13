"""Commands module for BOT-RELATED UTILITIES.
Access: Public"""

from datetime import datetime as dt

import discord

from . import core


class CommandsUtil(core.Commands):
    auth_fail = "This command is public. If you are reading this, something went wrong."

    def authenticate(self, *_):
        return True

    async def cmd_help(self, args, src, **_):
        """
        Print information regarding command usage.

        Help text is drawn from the docstring of a command method, which should be formatted into three sections -- Summary, Details, and Syntax -- which are separated by double-newlines.
        The Summary section provides cursory information about a command, and is typically all one needs to understand it.
        The Details section contains more involved information about how the command works, possibly including technical information.
        The Syntax section describes exactly how the command should be invoked. Angle brackets indicate a parameter to be filled, square brackets indicate an optional segment, and parentheses indicate choices, separated by pipes.

        Syntax: `{p}help [<command>]`
        """
        if not args:
            # TODO: Iso, put your default helptext here; Didnt copy it over in case you wanted it changed
            return "`<Default helptext goes here>`\n`#BlameIso`"

        mod, cmd, denied = self.router.find_command(args[0], src)
        if denied:
            return denied
        elif cmd.__doc__:
            # Grab the docstring and insert the correct prefix wherever needed
            doc0 = cmd.__doc__.format(p=self.config.prefix)
            # Split the docstring up by double-newlines
            doc = [doc1.strip() for doc1 in doc0.split("\n\n")]

            summary = doc.pop(0)
            em = discord.Embed(title=self.config.prefix + cmd.__name__[4:], description=summary, colour=0x0ACDFF)

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
            return "No help for `{}` available".format(self.config.prefix + cmd.__name__[4:])

    async def cmd_commands(self, **_):
        """
        List all commands.
        """
        formattedList = ""
        cmd = list(set([method.__name__[4:] for method in self.router.get_all()]))
        cmd.sort()
        for f in cmd:
            formattedList += self.config.prefix + f + "\n"

        return "Commands list: ```\n" + formattedList + "```"

    async def ping(self, src, **_):
        """
        Shows the round trip time from this bot to you and back
        Syntax: `>ping`
        """
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
        """
        Displays stats for nerds
        !statsfornerds
        """
        truedelta = int(self.config.stats["pingScore"] / self.config.stats["pingCount"])

        em = discord.Embed(title="Stats", description="*for nerds*", colour=0x0ACDFF)
        em.add_field(name="Version", value=self.router.version)
        em.add_field(name="Uptime", value=self.router.get_uptime())
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

        Used for testing, or personal experimentation to help you to understand options and flags.

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
